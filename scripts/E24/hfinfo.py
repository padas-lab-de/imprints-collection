import json,urllib.request,sys
for d in sys.argv[1:]:
    try:
        j=json.load(urllib.request.urlopen(f"https://huggingface.co/api/datasets/{d}"))
        print(d,'| gated',j.get('gated'),'| lic',(j.get('cardData') or {}).get('license'),'| dl',j.get('downloads'),'| files',len(j.get('siblings',[])),[s['rfilename'] for s in j.get('siblings',[])][:5])
    except Exception as e: print(d,'ERR',e)
