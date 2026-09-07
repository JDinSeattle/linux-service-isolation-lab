"""Linux peer credentials authenticate callers; policy grants explicit worker operations."""
import hashlib
import json
import os
import pathlib
import signal
import socket
import stat
import struct
import subprocess
import tempfile
import time

class Denied(ValueError): pass

def authorize(policy,uid,request):
    if type(policy.get('version',1)) is not int or policy.get('version',1)!=1:raise Denied('policy version')
    if not isinstance(request,dict) or set(request)!={'operation','m','n','k','seed'}: raise Denied('request schema')
    operation=request['operation']
    grants=policy.get('users',{}).get(str(uid),[])
    if operation not in grants or operation!='gemm': raise Denied('operation not granted to kernel-authenticated UID')
    for name in ['m','n','k']:
        if type(request[name]) is not int or not 1<=request[name]<=128: raise Denied('dimension limit')
    if type(request['seed']) is not int or not 0<=request['seed']<=100000: raise Denied('seed limit')
    return request

def execute(confine,worker,scratch,args,timeout=3):
    p=subprocess.Popen([str(confine),str(scratch),str(worker),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    try:
        stdout,stderr=p.communicate(timeout=timeout); status='completed' if p.returncode==0 else 'process_failure'
    except subprocess.TimeoutExpired:
        os.killpg(p.pid,signal.SIGKILL); stdout,stderr=p.communicate(timeout=2); status='timeout'
    return {'status':status,'returncode':p.returncode,'stdout':stdout,'stderr':stderr,'child_reaped':p.poll() is not None}

class Broker:
    def __init__(self,path,policy,confine,worker,scratch_root,request_timeout=2):
        if not 0<request_timeout<=30:raise ValueError('request timeout must be in (0,30]')
        self.request_timeout=request_timeout
        self.path=pathlib.Path(path); self.policy=policy; self.confine=confine; self.worker=pathlib.Path(worker)
        self.scratch_root=scratch_root; self.socket=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        # Never unlink an existing socket/file; installation cannot replace another service.
        try:self.socket.bind(str(self.path))
        except BaseException:self.socket.close();raise
        self.socket_identity=self.path.lstat().st_ino
        self.path.chmod(0o600); self.socket.listen(4); self.socket.settimeout(5)
    def serve_one(self):
        conn,_=self.socket.accept()
        with conn:
            deadline=time.monotonic()+self.request_timeout
            pid,uid,gid=struct.unpack('3i',conn.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
            try:
                raw=b''
                while not raw.endswith(b'\n'):
                    remaining=deadline-time.monotonic()
                    if remaining<=0:raise Denied('request deadline exceeded')
                    conn.settimeout(remaining)
                    block=conn.recv(1024)
                    if not block: raise Denied('truncated request')
                    raw+=block
                    if len(raw)>4096: raise Denied('request size')
                request=authorize(self.policy,uid,json.loads(raw))
                if hashlib.sha256(self.worker.read_bytes()).hexdigest()!=self.policy['worker_sha256']: raise Denied('worker digest mismatch')
                with tempfile.TemporaryDirectory(dir=self.scratch_root,prefix='job-') as d:
                    r=execute(self.confine,self.worker,d,['optimized',*[str(request[k]) for k in ['m','n','k']],'1',str(request['seed']),'generated'])
                response={'authorized':True,'peer':{'pid':pid,'uid':uid,'gid':gid},'result':r}
            except (Denied,ValueError,OSError) as e:
                response={'authorized':False,'peer':{'pid':pid,'uid':uid,'gid':gid},'reason':str(e)}
            conn.settimeout(.2)
            try:conn.sendall(json.dumps(response).encode()+b'\n');response['delivery']='sent'
            except OSError:response['delivery']='peer_disconnected'
            return response
    def close(self):
        self.socket.close()
        try:
            info=self.path.lstat()
            if info.st_ino==self.socket_identity and stat.S_ISSOCK(info.st_mode):self.path.unlink()
        except FileNotFoundError:pass

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--socket',required=True); ap.add_argument('--policy',required=True)
    ap.add_argument('--scratch-root',required=True); ap.add_argument('--confine',default='build/confine'); ap.add_argument('--worker',default='build/gemm')
    a=ap.parse_args(); pathlib.Path(a.scratch_root).mkdir(mode=0o700,parents=True,exist_ok=True)
    b=Broker(a.socket,json.loads(pathlib.Path(a.policy).read_text()),pathlib.Path(a.confine).resolve(),pathlib.Path(a.worker).resolve(),a.scratch_root)
    try:
        while True:
            try: print(json.dumps(b.serve_one()),flush=True)
            except socket.timeout: continue
    except KeyboardInterrupt: pass
    finally: b.close()
