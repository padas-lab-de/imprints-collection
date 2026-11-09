import io,urllib.request
class HFFile(io.RawIOBase):
    """Seekable read-only file over HTTP range requests; counts bytes read."""
    def __init__(self,url):
        self.pos=0; self.bytes=0; self.nreq=0
        r=urllib.request.urlopen(urllib.request.Request(url,method='HEAD'))
        self.url=r.geturl(); self.size=int(r.headers['Content-Length'])
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self,off,whence=0):
        self.pos={0:off,1:self.pos+off,2:self.size+off}[whence]; return self.pos
    def readinto(self,b):
        n=len(b)
        if n==0 or self.pos>=self.size: return 0
        end=min(self.pos+n,self.size)-1
        for t in range(5):
            try:
                req=urllib.request.Request(self.url,headers={'Range':f'bytes={self.pos}-{end}'})
                d=urllib.request.urlopen(req,timeout=120).read(); break
            except Exception as e:
                if t==4: raise
        b[:len(d)]=d; self.pos+=len(d); self.bytes+=len(d); self.nreq+=1; return len(d)
