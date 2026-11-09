import duckdb,json,urllib.request
j=json.load(urllib.request.urlopen("https://huggingface.co/api/datasets/commoncrawl/host-index-testing-v2/tree/main?limit=100"))
print([(x['path'],x.get('size')) for x in j][:20])
