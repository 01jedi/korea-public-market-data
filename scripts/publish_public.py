"""Publish only this run's public market evidence using Actions built-in token."""
import os,json,urllib.request,urllib.error,pathlib,base64,zipfile
root=pathlib.Path('evidence/cloud');repo=os.environ['GITHUB_REPOSITORY'];token=os.environ['GITHUB_TOKEN'];base='https://api.github.com/repos/'+repo+'/contents/'
def put(path,raw):
 url=base+path;headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'};payload={'message':'Publish manual public market acceptance '+os.environ['GITHUB_RUN_ID'],'content':base64.b64encode(raw).decode()}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers=headers)) as r:payload['sha']=json.load(r)['sha']
 except urllib.error.HTTPError as e:
  if e.code!=404:raise
 req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers=headers,method='PUT')
 with urllib.request.urlopen(req) as r:assert r.status in [200,201]
for name in ['acceptance.json','run1/summary.json']:
 p=root/name
 if p.exists():put('data/'+name,p.read_bytes())
for p in sorted((root/'run1').glob('*.normalized.json')):put('data/'+p.name,p.read_bytes())
with zipfile.ZipFile('public-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in root.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(root))
put('data/public-evidence.zip',pathlib.Path('public-evidence.zip').read_bytes())
print('Published public evidence for run '+os.environ['GITHUB_RUN_ID'])
