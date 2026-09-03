from pathlib import Path
from PIL import Image
import csv, json, zipfile
root=Path('/home/ubuntu/ventoy-themes')
themes=list((root/'adaptive-365').glob('*/*/theme.txt'))
images=list((root/'adaptive-365').glob('*/*/background.png'))
previews=list((root/'adaptive-previews').glob('day-*.jpg'))
packages=list((root/'adaptive-packages').glob('*.zip'))
assert len(themes)==365, len(themes)
assert len(images)==365, len(images)
assert len(previews)==365, len(previews)
assert len(packages)==12, len(packages)
for p in images:
    assert Image.open(p).size==(1366,786), (p,Image.open(p).size)
for p in previews:
    assert Image.open(p).size==(1366,786), (p,Image.open(p).size)
with (root/'adaptive-manifest.csv').open() as f:
    rows=list(csv.DictReader(f))
assert len(rows)==365
assert len({r['date'] for r in rows})==365
assert all(r['menu_region'] in {'left','right','left-bottom','right-bottom'} for r in rows)
assert len({r['menu_region'] for r in rows})>=2
print(json.dumps({'themes':len(themes),'images':len(images),'previews':len(previews),'packages':len(packages),'unique_dates':len({r['date'] for r in rows}),'menu_regions':sorted({r['menu_region'] for r in rows}),'image_size':'1366x786','vm_render_tools_available':False},indent=2))
