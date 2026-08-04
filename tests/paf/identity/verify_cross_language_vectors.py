"""Offline agreement check for the independent Python and Node vector readers."""
import json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; V=ROOT/'tests/paf/identity/vectors/paf_identity_v1.json'
sys.path.insert(0,str(ROOT))
from paf.identity import canonical_bytes,TypedDigest,CanonicalizationError

def main():
 data=json.loads(V.read_text(encoding='utf-8'))
 if data.get('vector_schema')!='paf-identity-v1' or set(data.get('decisions',[])) != {f'PAF-DEC-00{i}' for i in range(1,6)}: raise SystemExit('incomplete vector coverage')
 for x in data['canonical']:
  if canonical_bytes(x['value']).hex()!=x['hex']: raise SystemExit('python canonical mismatch: '+x['id'])
 for x in data['digests']:
  if str(TypedDigest.for_value(x['domain'],x['value']))!=x['wire']: raise SystemExit('python digest mismatch: '+x['id'])
 node=shutil.which('node')
 if not node: raise SystemExit('node unavailable')
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
 p=subprocess.run([node,str(ROOT/'tests/paf/identity/verify_vectors.mjs')],cwd=ROOT,text=True,capture_output=True,env=dict(env,PAF_IDENTITY_NODE_ONLY='1'))
 if p.returncode: raise SystemExit(p.stdout+p.stderr)
 print('cross-language vectors: ok')
if __name__=='__main__': main()
