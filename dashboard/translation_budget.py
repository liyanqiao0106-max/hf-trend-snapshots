"""Reserve a persistent allowance before translating on ephemeral Actions runners."""
import json
import os
import subprocess
import time
from .common import ROOT,write_json

class ReleaseBudget:
    def __init__(self,previous_requests,limit):
        self.repo=os.environ.get('GITHUB_REPOSITORY')
        if not self.repo or not os.environ.get('GH_TOKEN'):
            raise RuntimeError('缺少持久翻译预算权限，不发送翻译请求')
        self.tag='translation-budget'
        self.path=ROOT/'history/translation-budget.json'
        self.owner=os.environ.get('GITHUB_RUN_ID','')+'-'+os.environ.get('GITHUB_RUN_ATTEMPT','1')
        view=subprocess.run(['gh','release','view',self.tag,'--repo',self.repo,'--json','assets'],capture_output=True,text=True)
        if view.returncode==0:
            assets=json.loads(view.stdout)['assets']
            if not any(a['name']==self.path.name for a in assets):
                raise RuntimeError('翻译预算 Release 缺少账本，暂停翻译以防超限')
            self.command(['gh','release','download',self.tag,'--repo',self.repo,'--pattern',self.path.name,'--output',str(self.path),'--clobber'])
            state=json.loads(self.path.read_text(encoding='utf-8'))
        else:
            self.command(['gh','release','create',self.tag,'--repo',self.repo,'--title','Persistent translation budget','--notes','Rolling 24-hour character allowance. No credentials.','--latest=false'])
            state={'requests':previous_requests,'reservations':[]}
        now=time.time()
        self.requests=[r for r in state['requests'] if r['time']>now-86400]
        self.reservations=[r for r in state.get('reservations',[]) if r['time']>now-86400]
        self.allowance=max(0,limit-sum(r['characters'] for r in self.requests)-sum(r['characters'] for r in self.reservations))
        # Claim the entire remaining allowance first. A cancelled/failed job leaves the claim
        # in place until 24h expires, so reruns cannot exceed the same allowance.
        self.reservations.append({'owner':self.owner,'time':now,'characters':self.allowance})
        self.persist()

    def command(self,args):
        result=subprocess.run(args,capture_output=True,text=True)
        if result.returncode:raise RuntimeError('GitHub 持久翻译预算读写失败；暂停新增翻译')

    def persist(self):
        write_json(self.path,{'schema_version':1,'limit':3000,'requests':self.requests,'reservations':self.reservations})
        self.command(['gh','release','upload',self.tag,str(self.path),'--repo',self.repo,'--clobber'])

    def finish(self,new_requests):
        self.reservations=[r for r in self.reservations if r['owner']!=self.owner]
        self.requests.extend(new_requests)
        self.persist()
