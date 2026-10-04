import datetime as dt
import hashlib
import io
import json
import tarfile
import tempfile
import unittest
import time
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

from dashboard.prices import parse_models,parse_azure
from dashboard.news import parse_feed,clean,collect_news,memory_related
from dashboard.storage import select_spaced,unpack_bundle
from dashboard.translation import restore_terms,MyMemoryTranslator
from dashboard.translation_budget import ReleaseBudget

class DailySourcesTests(unittest.TestCase):
    def test_per_token_prices_and_dynamic_exclusion(self):
        rows=parse_models({'data':[
            {'id':'paid','pricing':{'prompt':'0.000003','completion':'0.000015'}},
            {'id':'free','pricing':{'prompt':'0','completion':'0'}},
            {'id':'dynamic','pricing':{'prompt':'-1','completion':'0'}}]})
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['input_usd_per_million'],3)
        self.assertEqual(rows[0]['output_usd_per_million'],15)
        self.assertTrue(rows[1]['free'])

    def test_gpu_price_is_instance_divided_by_eight_not_windows(self):
        base={'productName':'Virtual Machines ND','type':'Consumption','unitOfMeasure':'1 Hour',
            'isPrimaryMeterRegion':True,'tierMinimumUnits':0,'retailPrice':96,'meterId':'x',
            'armRegionName':'eastus','meterName':'ND96 H100'}
        rows=parse_azure([base,dict(base,productName='Windows ND'),dict(base,meterName='ND96 Spot',retailPrice=24)],
            {'gpu':'H100','gpu_count':8,'sku':'Standard_ND96isr_H100_v5'})
        self.assertEqual([(r['billing'],r['usd_per_gpu_hour']) for r in rows],[('On-demand',12),('Spot',3)])

    def test_news_filters_future_links_and_html(self):
        feed={'name':'test','language':'en','region':'国际'}
        xml=b'<rss><channel><item><title>AI update</title><link>https://example.com/1</link><pubDate>Sat, 03 Oct 2026 04:00:00 GMT</pubDate><description>AI system</description></item><item><title>AI future</title><link>https://example.com/2</link><pubDate>Sun, 04 Oct 2026 04:00:00 GMT</pubDate></item></channel></rss>'
        rows=parse_feed(xml,feed,now=dt.datetime(2026,10,3,5,tzinfo=dt.timezone.utc))
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['translation_status'],'pending')
        self.assertEqual(clean('<script>secret</script><b>AI</b> &amp; GPU'),'AI & GPU')
        with self.assertRaises(ValueError):
            parse_feed(b'<html><body>not RSS</body></html>',feed)

    def test_memory_column_excludes_consumer_pc_ram_configurations(self):
        self.assertFalse(memory_related('迷你工作站上市，32GB DDR4内存和1TB SSD，到手6399元'))
        self.assertTrue(memory_related('HBM memory demand rises as GPU makers expand data center capacity'))
        self.assertTrue(memory_related('美光扩大DRAM晶圆产能，应对AI内存需求'))

    def test_daily_snapshots_use_seven_day_anchors(self):
        days=[dt.date(2026,10,3)-dt.timedelta(days=n) for n in range(20)]
        self.assertEqual(select_spaced(days),[dt.date(2026,10,3),dt.date(2026,9,26),dt.date(2026,9,19)])

    def test_all_feed_failures_do_not_relabel_old_news_as_fresh(self):
        with patch('dashboard.news.request_bytes',side_effect=RuntimeError('HTTP 503')):
            with self.assertRaises(ValueError):
                collect_news('2026-10-03',{'feeds':[{'name':'test','url':'https://example.com','language':'en','region':'国际'}],
                    'news_days':7,'news_limit_per_region':12},previous={'rows':[{'id':'old','published_at_utc':'2026-10-02T00:00:00+00:00'}]})

    def make_bundle(self,name,content,checksum=None):
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w:gz') as tar:
            info=tarfile.TarInfo(name);info.size=len(content);tar.addfile(info,io.BytesIO(content))
            manifest=json.dumps({'files':{name:{'bytes':len(content),'sha256':checksum or hashlib.sha256(content).hexdigest()}}}).encode()
            info=tarfile.TarInfo('bundle_manifest.json');info.size=len(manifest);tar.addfile(info,io.BytesIO(manifest))
        return buf.getvalue()

    def test_archive_rejects_tampering_and_path_escape(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):unpack_bundle(self.make_bundle('../outside.txt',b'bad'),root)
            with self.assertRaises(ValueError):unpack_bundle(self.make_bundle('history/a.txt',b'bad','wrong'),root)
            unpack_bundle(self.make_bundle('history/a.txt',b'ok'),root)
            self.assertEqual((Path(root)/'history/a.txt').read_bytes(),b'ok')

    def test_old_anchors_cannot_overwrite_new_translation_cache(self):
        with tempfile.TemporaryDirectory() as root:
            blob=self.make_bundle('history/translation-cache.json',b'{}')
            unpack_bundle(blob,root,restore_site=False)
            self.assertFalse((Path(root)/'history/translation-cache.json').exists())
            unpack_bundle(blob,root,restore_site=True)
            self.assertTrue((Path(root)/'history/translation-cache.json').exists())

    def test_translation_restores_names_or_rejects_missing_names(self):
        self.assertEqual(restore_terms('Anthropic updates Claude Code','人类学更新了克劳德代码'),'Anthropic更新了Claude Code')
        with self.assertRaises(ValueError):restore_terms('Anthropic announces a model','一家企业宣布新模型')

    def test_translation_budget_is_persistent_and_cache_does_not_spend_again(self):
        with tempfile.TemporaryDirectory() as root,patch.dict('os.environ',{'GITHUB_ACTIONS':'false'}):
            path=Path(root)/'cache.json'
            path.write_text(json.dumps({'requests':[{'time':time.time(),'characters':2994}]}),encoding='utf-8')
            translator=MyMemoryTranslator({'max_characters_per_24h':3000},path)
            response=json.dumps({'responseStatus':200,'responseData':{'translatedText':'你好'}}).encode()
            with patch('dashboard.translation.request_bytes',return_value=response) as request:
                self.assertEqual(translator('Hello'),'你好')
                self.assertEqual(translator('Hello'),'你好')
                with self.assertRaises(RuntimeError):translator('other')
                self.assertEqual(request.call_count,1)
            restored=MyMemoryTranslator({},path)
            self.assertEqual(sum(r['characters'] for r in restored.requests),2999)
            self.assertEqual(restored('Hello'),'你好')

    def test_failed_translation_request_is_counted_and_not_retried(self):
        with tempfile.TemporaryDirectory() as root,patch.dict('os.environ',{'GITHUB_ACTIONS':'false'}):
            translator=MyMemoryTranslator({},Path(root)/'cache.json')
            with patch('dashboard.translation.request_bytes',side_effect=RuntimeError('HTTP 429')) as request:
                with self.assertRaises(RuntimeError):translator('Hello')
                with self.assertRaises(RuntimeError):translator('another')
                self.assertEqual(request.call_count,1)
                self.assertEqual(request.call_args.kwargs['retries'],1)
            self.assertEqual(sum(r['characters'] for r in translator.requests),5)

    def test_failed_actions_run_keeps_budget_reserved_for_rerun(self):
        with tempfile.TemporaryDirectory() as root,patch.dict('os.environ',{'GITHUB_REPOSITORY':'example/dashboard','GH_TOKEN':'unit-test-placeholder','GITHUB_RUN_ID':'1'}),patch('dashboard.translation_budget.ROOT',Path(root)):
            path=Path(root)/'history/translation-budget.json';path.parent.mkdir()
            path.write_text(json.dumps({'requests':[{'time':time.time(),'characters':2000}],'reservations':[]}),encoding='utf-8')
            view=SimpleNamespace(returncode=0,stdout=json.dumps({'assets':[{'name':path.name}]}))
            with patch('dashboard.translation_budget.subprocess.run',return_value=view),patch.object(ReleaseBudget,'command'):
                first=ReleaseBudget([],3000)
                self.assertEqual(first.allowance,1000)
                with patch.dict('os.environ',{'GITHUB_RUN_ID':'2'}):
                    rerun=ReleaseBudget([],3000)
                    self.assertEqual(rerun.allowance,0)

    def test_successful_run_replaces_reservation_with_actual_usage(self):
        with tempfile.TemporaryDirectory() as root,patch.dict('os.environ',{'GITHUB_REPOSITORY':'example/dashboard','GH_TOKEN':'unit-test-placeholder','GITHUB_RUN_ID':'1'}),patch('dashboard.translation_budget.ROOT',Path(root)):
            path=Path(root)/'history/translation-budget.json';path.parent.mkdir()
            path.write_text(json.dumps({'requests':[],'reservations':[]}),encoding='utf-8')
            view=SimpleNamespace(returncode=0,stdout=json.dumps({'assets':[{'name':path.name}]}))
            with patch('dashboard.translation_budget.subprocess.run',return_value=view),patch.object(ReleaseBudget,'command'):
                ledger=ReleaseBudget([],3000)
                ledger.finish([{'time':time.time(),'characters':800}])
                state=json.loads(path.read_text(encoding='utf-8'))
                self.assertFalse(state['reservations'])
                self.assertEqual(sum(r['characters'] for r in state['requests']),800)

if __name__=='__main__':unittest.main()
