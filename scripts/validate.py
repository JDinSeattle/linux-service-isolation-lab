#!/usr/bin/env python3
import argparse, errno, json, os, pathlib, signal, socket, subprocess, sys, tempfile, threading, time
ROOT=pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from broker import Broker, execute
from evidence import command, digest, fresh, seal, write

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='.runs/latest'); args=ap.parse_args()
    out=fresh(ROOT,args.out)
    build=ROOT/'build'; build.mkdir(exist_ok=True)
    for name in ['confine','probe']:
        command(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/f'src/{name}.c'),'-o',str(build/name)])
    assert digest(ROOT/'vendor/gemm.cpp')==json.loads((ROOT/'vendor/lock.json').read_text())['sha256']
    command(['g++','-std=c++17','-O3',str(ROOT/'vendor/gemm.cpp'),'-o',str(build/'gemm')])
    abi=json.loads(command([str(build/'confine'),'--probe']))
    results=[]
    with tempfile.TemporaryDirectory(prefix='isolation-lab-') as td:
        area=pathlib.Path(td); scratch=area/'scratch'; scratch.mkdir(); forbidden=area/'private.txt'; forbidden.write_text('test-owned sentinel')
        (scratch/'input').write_text('allowed'); (scratch/'escape').symlink_to(forbidden)
        controls=[]
        for probe in [['read',str(forbidden)],['socket'],['memory']]:
            result=json.loads(command([str(build/'probe'),*probe]))
            assert result['rc']>=0,result
            controls.append({'probe':probe[0],'unconfined':result})
        write(out/'unconfined-controls.json',controls)
        for label,worker,argv,expected in [
            ('business_gemm','gemm',['optimized','1','1','1','1','0','generated'],'success'),
            ('read_allowed','probe',['read',str(scratch/'input')],'success'),
            ('write_allowed','probe',['write',str(scratch/'output')],'success'),
            ('read_outside','probe',['read',str(forbidden)],errno.EACCES),
            ('write_outside','probe',['write',str(forbidden)],errno.EACCES),
            ('symlink_escape','probe',['read',str(scratch/'escape')],errno.EACCES),
            ('network','probe',['socket'],errno.EPERM),('process_creation','probe',['fork'],errno.EPERM),
            ('ptrace','probe',['ptrace'],errno.EPERM),('memory','probe',['memory'],errno.ENOMEM),
            ('descriptors','probe',['files',str(scratch/'input')],errno.EMFILE),
            ('file_capacity','probe',['disk'],-signal.SIGXFSZ),('cpu_budget','probe',['cpu'],-signal.SIGXCPU),
            ('wall_deadline','probe',['wall'],'timeout')]:
            start=time.monotonic(); r=execute(build/'confine',build/worker,scratch,argv,timeout=.2 if label=='wall_deadline' else 4)
            r.update(case=label,elapsed_ms=(time.monotonic()-start)*1000)
            if expected=='success':
                assert r['status']=='completed',r
                data=json.loads(r['stdout']); assert data.get('rc',0)==0,r
                if worker=='gemm': assert data['values']==[99/64],r
            elif expected=='timeout': assert r['status']=='timeout' and r['child_reaped'],r
            elif expected<0: assert r['returncode']==expected,r
            else:
                assert r['status']=='completed',r
                data=json.loads(r['stdout']); assert data['rc']==-1 and data['errno']==expected,r
            r['expected_enforced']=True; results.append(r)
        assert forbidden.read_text()=='test-owned sentinel'
        assert (scratch/'limited.bin').stat().st_size==32768
        policy={'version':1,'users':{str(os.getuid()):['gemm']},'worker_sha256':digest(build/'gemm')}
        broker=Broker(area/'broker.sock',policy,build/'confine',build/'gemm',area)
        try:
          for label,request in [('allowed',{'operation':'gemm','m':1,'n':1,'k':1,'seed':0}),
                                ('wrong_operation',{'operation':'shell','m':1,'n':1,'k':1,'seed':0}),
                                ('uid_spoof',{'operation':'gemm','m':1,'n':1,'k':1,'seed':0,'uid':0})]:
            captured=[]; t=threading.Thread(target=lambda:captured.append(broker.serve_one())); t.start()
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
                client.connect(str(broker.path)); client.sendall(json.dumps(request).encode()+b'\n'); raw=b''
                while not raw.endswith(b'\n'): raw+=client.recv(65536)
            t.join(timeout=5); response=json.loads(raw)
            assert response['authorized']==(label=='allowed'),response
            assert response['peer']['uid']==os.getuid(),response
            if label=='allowed': assert json.loads(response['result']['stdout'])['values']==[99/64]
            results.append({'case':'peer_auth_'+label,'expected_enforced':True,'response':response})
        finally: broker.close()
        write(out/'policy-example.json',policy)
    write(out/'matrix.json',results)
    (out/'probe.disassembly.txt').write_text(command(['objdump','-d',str(build/'probe')]))
    seal(ROOT,out,{'kernel_capabilities':abi,'cases':len(results),'confine_sha256':digest(build/'confine'),
        'worker_sha256':digest(build/'gemm'),'limits':{'address_space_mib':64,'file_bytes':32768,'open_fds':32,'cpu_soft_seconds':1},
        'boundary':'local same-host UID auth, Landlock ABI3 filesystem rights, syscall allowlist; no container/cgroup/network namespace claim',
        'assumptions':'trusted broker, binaries and policy directory; same-UID hostile host processes/root outside threat model'})
    print(json.dumps({'kernel':abi,'real_kernel_and_auth_cases':len(results),'all_expected_enforced':True},indent=2))

if __name__=='__main__': main()
