import json,urllib.request,sys
d,p=sys.argv[1:3]
j=json.load(urllib.request.urlopen(f"https://huggingface.co/api/datasets/{d}/tree/main/{p}?limit=1000"))
tot=sum(x.get('size',0) for x in j)
print(len(j),tot/1e9)
for x in j[:8]: print(x['path'],x.get('size'),x.get('lfs',{}).get('size'))
