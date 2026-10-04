from __future__ import annotations
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from .common import envelope, request_json

MODELS_URL='https://openrouter.ai/api/v1/models'
AZURE_URL='https://prices.azure.com/api/retail/prices'

def parse_models(payload):
    rows=[]
    for item in payload.get('data',[]):
        try:
            prices=item.get('pricing') or {}
            prompt=Decimal(prices['prompt']); output=Decimal(prices['completion'])
            if prompt<0 or output<0:
                continue
            rows.append({'id':item['id'],'name':item.get('name',item['id']),
                'url':'https://openrouter.ai/'+item['id'],
                'input_usd_per_million':float(prompt*1_000_000),
                'output_usd_per_million':float(output*1_000_000),
                'free':prompt==0 and output==0,
                'context_length':item.get('context_length'),
                'modalities':(item.get('architecture') or {}).get('input_modalities',[]),
                'tiered_pricing':bool(prices.get('overrides')),
                'cache_pricing':{k:v for k,v in prices.items() if 'cache' in k}})
        except (KeyError,InvalidOperation,TypeError):
            continue
    return sorted(rows,key=lambda r:(r['free'],r['input_usd_per_million'],r['id']))

def collect_models(day):
    return envelope('token_prices','OpenRouter',MODELS_URL,parse_models(request_json(MODELS_URL)),
        '模型目录基础输入/输出报价，单位 USD/百万 Token；缓存、分档和免费模型单独标注。动态负价不参与比较。不是 Silicon Data 指数。',snapshot_date=day,unit='USD / M Tokens')

def parse_azure(items, config):
    rows={}
    for item in items:
        product=item.get('productName',''); meter=item.get('meterName','')
        if 'Windows' in product or item.get('type')!='Consumption' or item.get('unitOfMeasure')!='1 Hour':
            continue
        if not item.get('isPrimaryMeterRegion',False) or item.get('tierMinimumUnits',0)!=0:
            continue
        price=float(item.get('retailPrice',0))
        if price<=0:
            continue
        kind='Spot' if 'Spot' in meter else 'Low Priority' if 'Low Priority' in meter else 'On-demand'
        row={'id':item['meterId'],'provider':'Azure','gpu':config['gpu'],'gpu_count':config['gpu_count'],
            'region':item['armRegionName'],'sku':config['sku'],'instance_usd_hour':price,
            'usd_per_gpu_hour':round(price/config['gpu_count'],6),'billing':kind,
            'effective_start':item.get('effectiveStartDate'),'url':'https://azure.microsoft.com/pricing/details/virtual-machines/linux/'}
        rows[(row['region'],kind)]=row
    return list(rows.values())

def collect_gpu(day, configs):
    rows=[]
    for config in configs:
        query=urlencode({'$filter':f"armSkuName eq '{config['sku']}' and priceType eq 'Consumption'"})
        url=AZURE_URL+'?'+query
        for _ in range(20):
            payload=request_json(url)
            rows.extend(parse_azure(payload.get('Items',[]),config))
            url=payload.get('NextPageLink')
            if not url:
                break
        else:
            raise RuntimeError('Azure 分页超过上限')
    return envelope('gpu_prices','Azure Retail Prices',AZURE_URL,
        sorted(rows,key=lambda r:(r['billing'],r['usd_per_gpu_hour'],r['region'])),
        'H100 ND96isr_H100_v5 实例含 8 张 GPU；每 GPU 价格是整机 Linux 实例报价除以 8，包含 CPU/RAM 分摊。On-demand 与可中断 Spot 分开。不是 Silicon Data 租赁指数。',snapshot_date=day,unit='USD / GPU·hour')
