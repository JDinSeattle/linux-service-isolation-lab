"""Small file-backed evidence recorder. All measurements remain raw and hash-addressed."""
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n")

def command(args, **kw):
    p=subprocess.run(args, text=True, capture_output=True, timeout=kw.pop('timeout',30), **kw)
    if p.returncode: raise RuntimeError(f"{args[0]} exit {p.returncode}: {p.stderr[-3000:]}")
    return p.stdout

def fresh(root, path):
    root=Path(root).resolve(); out=Path(path).absolute()
    if out.is_symlink(): raise ValueError('output must not be a symlink')
    out=out.resolve()
    if out.exists() and any(out.iterdir()):
        if not out.is_relative_to(root/'.runs'):
            raise FileExistsError('refusing to replace a nonempty evidence directory outside .runs')
        out.rename(out.with_name(out.name+'.previous.'+str(time.time_ns())))
    out.mkdir(parents=True,exist_ok=True)
    return out

def seal(root, out, extra=None):
    root=Path(root).resolve(); out=Path(out).resolve()
    ignored={'.git','.runs','.tools','build','__pycache__','evidence','.venv'}
    source={str(p.relative_to(root)):digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not (set(p.relative_to(root).parts)&ignored) and p.name!='gmon.out'}
    artifacts={str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*'))
               if p.is_file() and p.name!='manifest.json'}
    cpu=next((s.split(':',1)[1].strip() for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('model name')), 'unknown')
    write(out/'manifest.json', {'schema':1,'run_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'execution':'real local CPU processes; author-operated', 'environment':{'python':sys.version,'kernel':platform.release(),'machine':platform.machine(),'cpu':cpu,'logical_cpus':os.cpu_count()},
        'source_sha256':source,'artifact_sha256':artifacts, 'details':extra or {}})

def verify(out):
    out=Path(out); m=json.loads((out/'manifest.json').read_text())
    for file, sha in m['artifact_sha256'].items():
        p=(out/file).resolve()
        if not p.is_relative_to(out.resolve()) or digest(p)!=sha: raise ValueError(f'evidence mismatch: {file}')
    return len(m['artifact_sha256'])

if __name__=='__main__':
    print('verified evidence files:',verify(sys.argv[1]))
