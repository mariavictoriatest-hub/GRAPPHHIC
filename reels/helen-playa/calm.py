import cv2, numpy as np, subprocess, math, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC = sys.argv[1] if len(sys.argv)>1 else 'reel_helen_playa_base_v2.mp4'
OUT = sys.argv[2] if len(sys.argv)>2 else 'reel_helen_playa_calma.mp4'
FD  = os.path.join(os.path.dirname(os.path.abspath(__file__)),'fonts')
W,H,FPS=1080,1920,30
pr=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height:format=duration','-of','csv=p=0',SRC],capture_output=True,text=True).stdout.split()
SW,SH=map(int,pr[0].split(',')[:2]); DUR=float(pr[1])
NF=int(DUR*FPS)
ease=lambda p: 1-(1-max(0.0,min(1.0,p)))**2
soft=lambda p: 0.5-0.5*math.cos(math.pi*max(0.0,min(1.0,p)))
# ---------- type: Abuchaljacoach identity ----------
def pf(size,w):
    f=ImageFont.truetype(os.path.join(FD,'PlayfairItalic.ttf'),size)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
SANS='/usr/share/fonts/opentype/inter/Inter-Light.otf'
FONTS={'s':ImageFont.truetype(SANS,68),'m':pf(104,500),'b':pf(160,560),'h':pf(46,400)}
COL={'s':(255,255,255),'m':(236,220,255),'b':(236,218,255),'h':(255,255,255)}
def render_word(txt,st):
    f=FONTS[st]; x0,y0,x1,y1=f.getbbox(txt); pad=40
    w,h=x1-x0+2*pad,y1-y0+2*pad
    im=Image.new('L',(w,h),0); ImageDraw.Draw(im).text((pad-x0,pad-y0),txt,font=f,fill=255)
    a=np.asarray(im,np.float32)/255
    sh=np.clip(np.asarray(im.filter(ImageFilter.GaussianBlur(12)),np.float32)/255*1.0+np.asarray(im.filter(ImageFilter.GaussianBlur(3)),np.float32)/255*0.35,0,0.8)
    rgb=np.ones((h,w,3),np.float32)*np.array(COL[st],np.float32); shc=np.array([38,20,56],np.float32)
    A=a+sh*(1-a); C=(rgb*a[...,None]+shc*(sh*(1-a))[...,None])/np.maximum(A,1e-4)[...,None]
    return dict(rgb=C,a=A,w=w,h=h,pad=pad,x0=x0,y0=y0,adv=f.getlength(txt))
# phrases (start times from the voiceover transcript)
G=[
 [[('¿Podés',0.15,'s'),('imaginarte',0.40,'s')],[('cómo',1.08,'s'),('va',1.36,'s'),('a',1.54,'s'),('estar',1.66,'s'),('el',1.74,'s'),('día',2.00,'s')]],
 [[('viendo',2.40,'s'),('este',3.44,'s')],[('amanecer?',3.66,'b')]],
 [[('Así',4.76,'s'),('son',4.94,'s'),('los',5.18,'s')],[('registros.',5.30,'b')]],
 [[('No',6.52,'s'),('podemos',6.74,'s')],[('imaginarnos',7.06,'m')],[('cómo',7.90,'s'),('van',8.30,'s'),('a',8.50,'s'),('ser.',8.64,'s')]],
 [[('Y',9.70,'s'),('menos',9.76,'s'),('con',10.00,'s'),('estos',10.22,'s'),('días',10.38,'s')],[('que',10.76,'s'),('uno',11.06,'s'),('no',11.30,'s'),('sabe',12.26,'s')]],
 [[('si',12.50,'s'),('va',12.72,'s'),('a',12.90,'s'),('haber',13.00,'s')],[('sol',13.08,'b'),('o',13.30,'s'),('lluvia,',13.48,'b')]],
 [[('los',15.16,'s'),('registros',15.28,'m')],[('se',15.68,'s'),('viven',15.88,'s')],[('el',16.26,'s'),('día',16.70,'s'),('igual.',16.88,'m')]],
 [[('Si',17.72,'s'),('estás',17.82,'s'),('pensando',18.04,'s')],[('en',18.52,'s'),('registros,',18.70,'m')]],
 [[('este',19.90,'s'),('es',20.54,'s'),('el',20.66,'s')],[('momento.',20.76,'b')]],
]
GEND=[g[0][0][1]-0.05 for g in G[1:]]+[DUR+1]
YC=1290; SPACE={'s':20,'m':30,'b':44}; LH={'s':94,'m':128,'b':176}
WORDS=[]
for gi,g in enumerate(G):
    big=lambda line: max((w[2] for w in line),key=lambda s:LH[s])
    y=YC-sum(LH[big(l)] for l in g)/2
    for line in g:
        lh=LH[big(line)]; rs=[render_word(w,st) for w,_,st in line]
        gaps=[max(SPACE[line[i][2]],SPACE[line[i+1][2]]) for i in range(len(line)-1)]+[0]
        tw=sum(r['adv'] for r in rs)+sum(gaps)
        x=W/2-tw/2; base=y+lh*0.78
        for (txt,ts,st),r,gp in zip(line,rs,gaps):
            asc=FONTS[st].getmetrics()[0]
            WORDS.append(dict(r=r,X=int(x+r['x0']-r['pad']),Y=int(base-asc+r['y0']-r['pad']),ts=ts,st=st,end=GEND[gi]))
            x+=r['adv']+gp
        y+=lh
def blit(fr,rgb,a,X,Y,op):
    if op<=0.003: return
    h,w=a.shape; x0,y0=max(0,X),max(0,Y); x1,y1=min(W,X+w),min(H,Y+h)
    if x1<=x0 or y1<=y0: return
    aa=(a[y0-Y:y1-Y,x0-X:x1-X]*op)[...,None]
    fr[y0:y1,x0:x1]=fr[y0:y1,x0:x1]*(1-aa)+rgb[y0-Y:y1-Y,x0-X:x1-X]*aa
def draw_word(fr,wd,t):
    r=wd['r']; p=(t-wd['ts'])/(0.9 if wd['st']=='b' else 0.6)
    if p<=0: return
    out=1-soft((t-wd['end'])/0.45)
    if out<=0: return
    e=soft(p)
    if wd['st']=='s':
        blit(fr,r['rgb'],r['a'],wd['X'],int(wd['Y']+10*(1-e)),e*out); return
    sc=1.04-0.04*e                      # very gentle settle, no blur
    nw,nh=int(r['w']*sc),int(r['h']*sc)
    rgb=cv2.resize(r['rgb'],(nw,nh)); a=cv2.resize(r['a'],(nw,nh))
    blit(fr,rgb,a,int(wd['X']+r['w']/2-nw/2),int(wd['Y']+r['h']/2-nh/2),e*out)
# soft twinkle next to the key words
gy,gx=np.mgrid[-50:51,-50:51].astype(np.float32)
GLK=np.exp(-(gx**2+gy**2)/(2*5**2))+0.8*np.exp(-(np.abs(gx)/2+np.abs(gy)/22))+0.8*np.exp(-(np.abs(gy)/2+np.abs(gx)/22))
def glint(fr,x,y,v):
    if v<0.02: return
    r=50; k=GLK*v*90
    if x-r<0 or y-r<0 or x+r+1>W or y+r+1>H: return
    fr[y-r:y+r+1,x-r:x+r+1]+=k[...,None]*np.array([1.0,0.94,1.0],np.float32)
KEY=[w for w in WORDS if w['st'] in ('b','m')]
SCRIM=(np.exp(-((np.arange(H)-YC)/300.0)**4)*0.30)[:,None,None].astype(np.float32)
SCRC=np.array([40,22,62],np.float32)
HANDLE=render_word('@abuchaljacoach','h')
dec=subprocess.Popen(['ffmpeg','-loglevel','error','-i',SRC,'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
  '-i',SRC,'-map','0:v','-map','1:a','-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-profile:v','high',
  '-movflags','+faststart','-c:a','aac','-b:a','192k','-t',f'{DUR:.3f}',OUT],stdin=subprocess.PIPE)
last=None
for f in range(NF):
    t=f/FPS
    buf=dec.stdout.read(SW*SH*3)
    if len(buf)==SW*SH*3: last=np.frombuffer(buf,np.uint8).reshape(SH,SW,3)
    fr=cv2.resize(last,(W,H),interpolation=cv2.INTER_CUBIC).astype(np.float32)
    fr=fr*(1-SCRIM)+SCRC*SCRIM
    for wd in WORDS: draw_word(fr,wd,t)
    for wd in KEY:
        dt=t-wd['ts']-0.6
        if 0<dt<wd['end']-wd['ts']-0.8:
            v=max(0,math.sin(dt*1.6))**4*min(1,dt/0.6)
            glint(fr,int(wd['X']+wd['r']['w']-wd['r']['pad']+6),int(wd['Y']+wd['r']['pad']+8),v)
    blit(fr,HANDLE['rgb'],HANDLE['a'],int(W/2-HANDLE['w']/2),250,0.85*soft((t-0.3)/1.2))
    enc.stdin.write(np.clip(fr,0,255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); dec.kill()
