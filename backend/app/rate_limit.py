from __future__ import annotations
import threading,time
from collections import defaultdict,deque
from fastapi import HTTPException
class RateLimiter:
    def __init__(self): self.events=defaultdict(deque); self.lock=threading.Lock()
    def check(self,key,limit,window):
        now=time.monotonic()
        with self.lock:
            q=self.events[key]; cutoff=now-window
            while q and q[0]<=cutoff:q.popleft()
            if len(q)>=limit:
                retry=max(1,int(q[0]+window-now)); raise HTTPException(429,headers={'Retry-After':str(retry)},detail={'code':'RATE_LIMITED','message':'Too many analysis requests. Please try again later.','retry_after_seconds':retry})
            q.append(now)
