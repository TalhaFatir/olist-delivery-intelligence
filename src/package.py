"""Package source, reproducible outputs and attribution without raw source archives."""
import os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
target=ROOT.parent/'olist-delivery-intelligence-portfolio.zip'
with ZipFile(target,'w',ZIP_DEFLATED) as archive:
    for current,dirs,files in os.walk(ROOT,followlinks=False):
        dirs[:]=sorted(d for d in dirs if d not in {'raw','__pycache__','screenshots','outputs','node_modules'} and not d.startswith('.'))
        for name in sorted(files):
            p=Path(current)/name
            if p.suffix not in {'.pyc','.zip'} and not name.startswith('.env'):
                archive.write(p,Path(ROOT.name)/p.relative_to(ROOT))
print(target)
