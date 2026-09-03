#!/usr/bin/env python3
from __future__ import annotations
import csv, io, json, math, os, random, shutil, subprocess, zipfile
from datetime import date, timedelta
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageFilter

ROOT=Path('/home/ubuntu/ventoy-themes'); REF=Path('/tmp/ventoy-reference/ventoy/theme'); OUT=ROOT/'adaptive-365'; PREV=ROOT/'adaptive-previews'; PKG=ROOT/'adaptive-packages'
W,H=1366,786; SRC_W,SRC_H=4096,2354; START=date(2026,9,3)
CATS=[('01-nature','Nature'),('02-mountains','Mountains'),('03-oceans','Oceans'),('04-forests','Forests'),('05-wildlife','Wildlife'),('06-architecture','Architecture'),('07-cities','Cities'),('08-space','Space'),('09-technology','Technology'),('10-abstract','Abstract'),('11-minimal','Minimal'),('12-travel','Travel')]
QUERIES=['nature landscape','mountain landscape','ocean coast','forest woodland','wildlife animal','architecture building','city skyline','space galaxy','technology circuit','abstract texture','minimal landscape','travel road']
S=requests.Session(); S.headers['User-Agent']='ventoy-themes-adaptive-builder/1.0'

def fnt(size,bold=False):
 p='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; return ImageFont.truetype(p,size)

def download(seed):
 u=f'https://picsum.photos/seed/ventoy-{seed}/{SRC_W}/{SRC_H}'
 for a in range(5):
  try:
   r=S.get(u,timeout=90); r.raise_for_status(); return Image.open(io.BytesIO(r.content)).convert('RGB'),u
  except Exception:
   if a==4: raise
 return None,u

def crop_resize(im):
 ratio=W/H; r=im.width/im.height
 if r>ratio:
  nw=int(im.height*ratio); x=(im.width-nw)//2; im=im.crop((x,0,x+nw,im.height))
 else:
  nh=int(im.width/ratio); y=(im.height-nh)//2; im=im.crop((0,y,im.width,y+nh))
 return im.resize((W,H),Image.Resampling.LANCZOS)

def region_score(im,box):
 g=im.crop(box).convert('L').resize((80,50))
 st=ImageStat.Stat(g); pix=list(g.getdata()); mean=st.mean[0]; var=st.var[0]
 edges=0
 for y in range(1,49):
  for x in range(1,79):
   if abs(pix[y*80+x]-pix[y*80+x-1])+abs(pix[y*80+x]-pix[(y-1)*80+x])>48: edges+=1
 # Lower variation/edges is better; extreme brightness is also less readable.
 brightness_penalty=max(0,abs(mean-110)-55)*0.35
 return var*0.60+edges*2.3+brightness_penalty

def choose_layout(im):
 mw,mh=int(W*.36),int(H*.60); margin=42
 options={'left':(margin, int(H*.20), margin+mw, int(H*.20)+mh),'right':(W-margin-mw,int(H*.20),W-margin,int(H*.20)+mh),'left-bottom':(margin,int(H*.33),margin+mw,int(H*.33)+mh),'right-bottom':(W-margin-mw,int(H*.33),W-margin,int(H*.33)+mh)}
 scores={k:region_score(im,b) for k,b in options.items()}; key=min(scores,key=scores.get); b=options[key]
 left=round(b[0]/W*100); top=round(b[1]/H*100); width=round((b[2]-b[0])/W*100); height=round((b[3]-b[1])/H*100)
 # More difficult backgrounds get a more opaque panel.
 transparency=max(0.30,min(0.58,0.58-(scores[key]/9000)))
 return key,scores,left,top,width,height,round(transparency,3)

def assets(daydir,alpha):
 # Ventoy menu pixmap style is a nine-slice; create true-alpha panels per day.
 a=int((1-alpha)*255); blue=(42,126,220,235); panel=(12,20,32,a)
 for name,color in [('menu_c.png',panel),('menu_n.png',panel),('menu_s.png',panel),('menu_e.png',panel),('menu_w.png',panel),('menu_ne.png',panel),('menu_nw.png',panel),('menu_se.png',panel),('menu_sw.png',panel),('terminal_box_c.png',(10,16,25,a)),('terminal_box_e.png',(10,16,25,a)),('terminal_box_n.png',(10,16,25,a)),('terminal_box_ne.png',(10,16,25,a)),('terminal_box_nw.png',(10,16,25,a)),('terminal_box_s.png',(10,16,25,a)),('terminal_box_se.png',(10,16,25,a)),('terminal_box_sw.png',(10,16,25,a)),('terminal_box_w.png',(10,16,25,a)),('select_c.png',blue),('slider_c.png',blue),('slider_n.png',blue),('slider_s.png',blue)]:
  Image.new('RGBA',(8,8),color).save(daydir/name)
 for p in REF.glob('*.pf2'): shutil.copy2(p,daydir/p.name)

def preview(im,day,dt,cat,layout,left,top,width,height,alpha,out):
 bg=im.filter(ImageFilter.GaussianBlur(0.15)); d=ImageDraw.Draw(bg,'RGBA'); x1=int(left/100*W); y1=int(top/100*H); x2=int((left+width)/100*W); y2=int((top+height)/100*H); a=int((1-alpha)*255)
 d.rounded_rectangle((x1,y1,x2,y2),radius=13,fill=(12,20,32,a),outline=(255,255,255,65),width=2)
 title_x=54 if left<50 else 825; d.text((title_x,35),'VENTOY',font=fnt(30,True),fill=(255,255,255,245)); d.text((title_x,78),f'DAY {day:03d} | {dt.isoformat()}',font=fnt(21,True),fill=(255,255,255,240)); d.text((title_x,112),f'{cat}  •  menu: {layout}',font=fnt(16),fill=(220,230,240,225))
 ix=x1+20 if left<50 else x1+20; y=y1+24; items=['Boot from local disk','ISO images','Windows installers','Linux distributions','Tools and utilities']
 for i,t in enumerate(items):
  if i==0: d.rounded_rectangle((ix-8,y-5,x2-22,y+30),radius=6,fill=(42,126,220,220))
  d.text((ix+12,y),t,font=fnt(19),fill=(255,255,255,245) if i==0 else (222,228,236,230)); y+=47
 footer_x=54 if left<50 else 825; d.text((footer_x,H-48),'↑↓ Select    Enter Boot    F1 Help    F5 Tools',font=fnt(15),fill=(255,255,255,220)); d.text((W-112,H-30),'Ventoy',font=fnt(15),fill=(180,200,225,220)); bg.save(out,quality=90)

def main():
 OUT.mkdir(exist_ok=True); PREV.mkdir(exist_ok=True); PKG.mkdir(exist_ok=True); rows=[]
 for n in range(365):
  dt=START+timedelta(days=n); key,cat=CATS[n%len(CATS)]; daydir=OUT/key/f'day-{n+1:03d}-{dt.isoformat()}'; daydir.mkdir(parents=True,exist_ok=True)
  seed=f'{dt.isoformat()}-{n+1:03d}-{random.Random(n+917).randint(1,99999999)}'; src,tempurl=download(seed); im=crop_resize(src); layout,scores,left,top,width,height,alpha=choose_layout(im); im.save(daydir/'background.png',optimize=True); assets(daydir,alpha)
  theme=f'''desktop-image: "background.png"\ntitle-text: " "\ntitle-color: "#ffffff"\nmessage-color: "#ffffff"\n+ boot_menu {{\n    left = {left}%\n    top = {top}%\n    width = {width}%\n    height = {height}%\n    item_color = "#d8e0ea"\n    selected_item_color = "#ffffff"\n    item_height = 36\n    item_spacing = 5\n    item_padding = 8\n    item_icon_space = 12\n    scrollbar = false\n    menu_pixmap_style = "menu_*.png"\n    selected_item_pixmap_style = "select_*.png"\n}}\n'''; (daydir/'theme.txt').write_text(theme)
  (daydir/'ventoy.json').write_text(json.dumps({'theme':{'file':'/ventoy/theme/theme.txt','gfxmode':'1366x786','display_mode':'GUI','ventoy_left':'5%','ventoy_top':'95%','ventoy_color':'#d8e0ea'}},indent=2)+'\n')
  preview(im,n+1,dt,cat,layout,left,top,width,height,alpha,PREV/f'day-{n+1:03d}.jpg')
  rows.append({'day':n+1,'date':dt.isoformat(),'category':cat,'theme_dir':str(daydir.relative_to(ROOT)),'source_4k_url':tempurl,'output_size':'1366x786','menu_region':layout,'menu_left_pct':left,'menu_top_pct':top,'menu_width_pct':width,'menu_height_pct':height,'menu_transparency':alpha,'analysis_scores':json.dumps(scores,separators=(',',':'))})
  if (n+1)%25==0: print(f'completed {n+1}/365',flush=True)
 with (ROOT/'adaptive-manifest.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
 (ROOT/'adaptive-manifest.json').write_text(json.dumps(rows,indent=2))
 for key,cat in CATS:
  z=PKG/f'{key}.zip'
  with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as zz:
   for p in (OUT/key).rglob('*'):
    if p.is_file(): zz.write(p,p.relative_to(OUT/key))
 print('complete')
if __name__=='__main__': main()
