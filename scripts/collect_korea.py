#!/usr/bin/env python3
"""Public GET only, fixed official host allowlist, no keys or account access."""
import argparse,concurrent.futures,datetime as dt,hashlib,json,pathlib,time,urllib.request,urllib.parse,urllib.error,platform,os
UTC=dt.timezone.utc; KST=dt.timezone(dt.timedelta(hours=9))
def iso(ms): return dt.datetime.fromtimestamp(ms/1000,UTC).isoformat()
def stamp(s): return int(dt.datetime.fromisoformat(s).replace(tzinfo=UTC).timestamp()*1000)
class Collector:
 def __init__(self,out): self.out=pathlib.Path(out);self.out.mkdir(parents=True,exist_ok=True)
 def get(self,label,base,path,params):
  assert base in ['https://api.upbit.com','https://api.bithumb.com','https://fapi.binance.com','https://api.binance.com','https://api.exchange.coinbase.com','https://open.er-api.com','https://www.binance.com']
  url=base+path+'?'+urllib.parse.urlencode(params)
  for attempt in range(3):
   meta={'url':url,'method':'GET','request_headers':{'Accept':'application/json','User-Agent':'public-market-acceptance/1.0'},'requested_at_utc':dt.datetime.now(UTC).isoformat(),'attempt':attempt+1}
   raw=b''
   try:
    with urllib.request.urlopen(urllib.request.Request(url,headers=meta['request_headers']),timeout=25) as r: raw=r.read();meta.update(status=r.status,response_headers=dict(r.headers))
   except urllib.error.HTTPError as e:raw=e.read();meta.update(status=e.code,response_headers=dict(e.headers))
   except Exception as e:meta.update(status=None,error=str(e))
   meta.update(received_at_utc=dt.datetime.now(UTC).isoformat(),sha256=hashlib.sha256(raw).hexdigest())
   name=f'{label}_a{attempt+1}';(self.out/(name+'.body.json')).write_bytes(raw);(self.out/(name+'.meta.json')).write_text(json.dumps(meta,indent=2))
   if meta['status']==200:
    time.sleep(.3)
    return json.loads(raw)
   if meta['status'] not in [None,429,500,502,503,504]: break
   time.sleep(min(4,2**attempt))
  return None
 def korea(self,ex,coin,unit,start,end):
  base='https://api.'+ex+'.com'; rows={};cursor=end;first=None;pages=0;failure=False;stalled=False
  for p in range(100):
   # Upbit to=UTC; Bithumb documented to=KST (no offset).
   to=dt.datetime.fromtimestamp(cursor/1000,UTC).astimezone(KST if ex=='bithumb' else UTC).strftime('%Y-%m-%dT%H:%M:%S')
   params={'market':'KRW-'+coin,'count':200,'to':to}
   data=self.get(f'{ex}_{coin}_{unit}m_p{p:03}',base,f'/v1/candles/minutes/{unit}',params);pages+=1
   if p==0:
    repeat=self.get(f'{ex}_{coin}_{unit}m_repeat',base,f'/v1/candles/minutes/{unit}',params)
    first={'same_closed_response':data==repeat,'rows_first':len(data) if isinstance(data,list) else None}
   if not isinstance(data,list):failure=True;break
   if not data:break
   for r in data:
    t=stamp(r['candle_date_time_utc'])
    if start<=t<end:rows[t]={'time_utc':iso(t),'timestamp_ms':t,'open':r['opening_price'],'high':r['high_price'],'low':r['low_price'],'close':r['trade_price'],'base_volume':r['candle_acc_trade_volume'],'quote_volume':r['candle_acc_trade_price'],'quote':'KRW','source_last_trade_ms':r.get('timestamp'),'taker_buy_quote':None,'raw':r}
   oldest=min(stamp(r['candle_date_time_utc']) for r in data)
   if oldest>=cursor:stalled=True;break
   if oldest<=start:break
   cursor=oldest
  return self.finish(f'{ex}_{coin}_{unit}m',rows,start,end,unit,{'pages':pages,'repeat':first,'request_failure':failure,'pagination_stalled':stalled})
 def bn(self,coin,unit,start,end,spot=False):
  rows={};cursor=start;name=('bn_spot_' if spot else 'bn_perp_')+coin+f'_{unit}m';base='https://api.binance.com' if spot else 'https://fapi.binance.com';path='/api/v3/klines' if spot else '/fapi/v1/klines';failure=False
  for p in range(10):
   data=self.get(name+f'_p{p}',base,path,{'symbol':coin+'USDT','interval':str(unit)+'m','startTime':cursor,'endTime':end-1,'limit':1000})
   if p==0: repeat=self.get(name+'_repeat',base,path,{'symbol':coin+'USDT','interval':str(unit)+'m','startTime':cursor,'endTime':end-1,'limit':1000});equal=data==repeat
   if not isinstance(data,list):failure=True;break
   if not data:break
   for r in data:
    t=int(r[0])
    if start<=t<end: rows[t]={'time_utc':iso(t),'timestamp_ms':t,'open':float(r[1]),'high':float(r[2]),'low':float(r[3]),'close':float(r[4]),'base_volume':float(r[5]),'quote_volume':float(r[7]),'quote':'USDT','taker_buy_quote':float(r[10]),'taker_sell_quote':float(r[7])-float(r[10]),'raw':r}
   cursor=int(data[-1][0])+unit*60000
   if cursor>=end:break
  return self.finish(name,rows,start,end,unit,{'request_failure':failure,'repeat_same_closed_response':equal})
 def finish(self,name,rows,start,end,unit,extra):
  missing=sorted(set(range(start,end,unit*60000))-set(rows));vals=[rows[t] for t in sorted(rows)]
  (self.out/(name+'.normalized.json')).write_text(json.dumps(vals,ensure_ascii=False,indent=2))
  result={'dataset':name,'start_utc':iso(start),'end_exclusive_utc':iso(end),'rows':len(vals),'expected_slots':(end-start)//(unit*60000),'missing_slots':len(missing),'missing_utc':[iso(x) for x in missing],'quote_volume_sum':sum(x['quote_volume'] for x in vals),'first_utc':vals[0]['time_utc'] if vals else None,'last_utc':vals[-1]['time_utc'] if vals else None,**extra}
  (self.out/(name+'.coverage.json')).write_text(json.dumps(result,indent=2));print(name,len(vals),'missing',len(missing),flush=True);return result
 def snapshots(self):
  result={}
  for ex in ['upbit','bithumb']:
   base='https://api.'+ex+'.com'
   for coin in ['CT','BIGTIME']:
    for kind,path,params in [('trades','/v1/trades/ticks',{'market':'KRW-'+coin,'count':500}),('orderbook','/v1/orderbook',{'markets':'KRW-'+coin})]:
     d=self.get(f'{ex}_{coin}_{kind}',base,path,params);result[f'{ex}_{coin}_{kind}']={'ok':isinstance(d,list),'rows':len(d) if isinstance(d,list) else None,'sample':d[:1] if isinstance(d,list) else d}
  return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--out',required=True);a.add_argument('--hours',type=int,default=72);a.add_argument('--end',help='UTC exclusive ISO time; defaults previous 5m boundary');args=a.parse_args()
 end=stamp(args.end) if args.end else int(time.time()*1000)//300000*300000;start=end-args.hours*3600000;c=Collector(args.out)
 jobs=[(c.korea,(ex,coin,u,start,end)) for ex in ['upbit','bithumb'] for coin in ['CT','BIGTIME'] for u in [1,5]]+[(c.bn,(coin,u,start,end,False)) for coin in ['CT','BIGTIME'] for u in [1,5]]+[(c.bn,('BIGTIME',u,start,end,True)) for u in [1,5]]
 with concurrent.futures.ThreadPoolExecutor(3) as pool:results=list(pool.map(lambda j:j[0](*j[1]),jobs))
 c.get('upbit_markets','https://api.upbit.com','/v1/market/all',{'is_details':'true'});c.get('bithumb_markets','https://api.bithumb.com','/v1/market/all',{'isDetails':'true'});c.get('binance_futures_markets','https://fapi.binance.com','/fapi/v1/exchangeInfo',{});c.get('binance_spot_markets','https://api.binance.com','/api/v3/exchangeInfo',{});c.get('binance_alpha_tokens','https://www.binance.com','/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list',{})
 summary={'execution_host':{'system':platform.system(),'github_actions':os.getenv('GITHUB_ACTIONS')=='true','run_id':os.getenv('GITHUB_RUN_ID')},'start_utc':iso(start),'end_exclusive_utc':iso(end),'datasets':results,'snapshots':c.snapshots()};(c.out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
