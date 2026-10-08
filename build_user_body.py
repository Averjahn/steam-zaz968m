"""Convert user's downloaded ZIP, including nested source/train.zip, to site GLB.
Usage: python3 build_user_body.py /path/to/zaz-968-m-low-poly.zip
Requires Node, playwright-core and Chrome. Input archive is never modified.
"""
from pathlib import Path
import json,zipfile,io,tempfile,subprocess,hashlib,sys
ROOT=Path(__file__).resolve().parent
archive=Path(sys.argv[1]) if len(sys.argv)>1 else Path.home()/'Desktop/zaz-968-m-low-poly.zip'
with tempfile.TemporaryDirectory(prefix='zaz-user-model-') as task_dir:
 staging=Path(task_dir)
 with zipfile.ZipFile(archive) as outer:
  with zipfile.ZipFile(io.BytesIO(outer.read('source/train.zip'))) as source:
   for info in source.infolist():
    p=staging/info.filename
    if not p.resolve().is_relative_to(staging.resolve()):raise ValueError('Unsafe archive member')
    if info.is_dir():p.mkdir(parents=True,exist_ok=True)
    else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(source.read(info))
 subprocess.run(['node',str(ROOT/'build_user_body.mjs'),str(staging)],cwd=ROOT,check=True)
p=ROOT/'models/zaz-968m-yatloo.json';meta=json.loads(p.read_text());meta['supplied_archive']={'name':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()};p.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
