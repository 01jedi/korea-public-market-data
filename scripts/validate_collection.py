import json,pathlib,sys,hashlib,os
root=pathlib.Path(sys.argv[1]);a=json.loads((root/'run1/summary.json').read_text());checks=[]
for d in a['datasets']:
 name=d['dataset'];p=root/'run1'/(name+'.normalized.json');q=root/'run2'/(name+'.normalized.json');same=json.loads(p.read_text())==json.loads(q.read_text());checks.append({'dataset':name,'rows':d['rows'],'missing_slots':d['missing_slots'],'availability':'available' if d['rows']>0 and not d.get('request_failure',False) else 'N/A','same_full_window_twice':same if d['rows']>0 else None,'transport_pass':not d.get('request_failure',False) and not d.get('pagination_stalled',False),'quote_volume_sum':d['quote_volume_sum'] if d['rows']>0 and not d.get('request_failure',False) else None})
identity={}
for ex in ['upbit','bithumb']:
 p=root/'run1'/(ex+'_markets_a1.body.json')
 fallback=root/(ex+'_markets.json')
 data=json.loads(p.read_text()) if p.exists() else json.loads(fallback.read_text())['body'] if fallback.exists() else []
 names={r['market']:r['english_name'] for r in data} if isinstance(data,list) else {}
 identity[ex]=names.get('KRW-CT')=='Concrete' and names.get('KRW-BIGTIME')=='Big Time'
k=[x for x in checks if x['dataset'].startswith(('upbit_','bithumb_'))];snap=all(x['ok'] for x in a['snapshots'].values());passed=all(identity.values()) and len(k)==8 and all(x['rows']>0 and x['same_full_window_twice'] and x['transport_pass'] for x in k) and snap
aggregation=[]
import math
for ex in ['upbit','bithumb']:
 for coin in ['CT','BIGTIME']:
  one=json.loads((root/'run1'/f'{ex}_{coin}_1m.normalized.json').read_text());five=json.loads((root/'run1'/f'{ex}_{coin}_5m.normalized.json').read_text());g={}
  for x in one:g[x['timestamp_ms']//300000*300000]=g.get(x['timestamp_ms']//300000*300000,0)+x['quote_volume']
  mismatch=sum(not math.isclose(g.get(x['timestamp_ms'],0),x['quote_volume'],rel_tol=1e-7,abs_tol=.02) for x in five);aggregation.append({'dataset':ex+'_'+coin,'mismatches':mismatch})
passed=passed and all(x['mismatches']==0 for x in aggregation)
result={'aggregation_checks':aggregation,'korea_public_api_acceptance':passed,'execution_host':a['execution_host'],'start_utc':a['start_utc'],'end_exclusive_utc':a['end_exclusive_utc'],'datasets':checks,'market_identity_checks':identity,'trades_orderbook_snapshots_pass':snap,'ordinary_chat_call_acceptance':False,'original_automation_call_acceptance':False,'note':'Missing candle slots retained, not zero-filled. Cloud run success does not prove ChatGPT automation access.'}
(root/'acceptance.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));sys.exit(0 if passed else 1)
