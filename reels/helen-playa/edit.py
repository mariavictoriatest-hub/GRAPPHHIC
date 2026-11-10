import cv2, numpy as np, subprocess, math, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC = sys.argv[1] if len(sys.argv)>1 else 'reel_helen_playa_original.mp4'
OUT = sys.argv[2] if len(sys.argv)>2 else 'reel_helen_playa_dinamico.mp4'
W,H,FPS=1080,1920,30
SW,SH=480,854
DUR=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',SRC],capture_output=True,text=True).stdout)
NF=int(DUR*FPS)
ease=lambda p: 1-(1-max(0.0,min(1.0,p)))**3
smooth=lambda p: 0.5-0.5*math.cos(math.pi*max(0.0,min(1.0,p)))
def backout(p):
    p=max(0,min(1,p)); c=1.7; return 1+(c+1)*(p-1)**3+c*(p-1)**2
# ---------------- camera ----------------
SUN=(0.356,0.377)
SEG=[ # t0,t1, s0,s1, c0,c1
 (0.0, 6.0, 1.00,1.12,(0.5,0.5),(0.42,0.45)),
 (6.0, 8.2, 1.45,1.55,SUN,SUN),
 (8.2,11.7, 1.10,1.18,(0.55,0.62),(0.50,0.58)),
 (11.7,15.45,1.22,1.12,(0.38,0.50),(0.62,0.50)),
 (15.45,17.45,1.60,1.70,SUN,SUN),
 (17.45,20.75,1.05,1.20,(0.5,0.48),(0.5,0.44)),
 (20.75,23.25,1.15,1.24,(0.62,0.60),(0.58,0.56)),
 (23.25,25.65,1.00,1.12,(0.5,0.5),(0.45,0.46)),
 (25.65,99,  1.35,1.70,SUN,SUN),
]
def camera(t):
    for i,(t0,t1,s0,s1,c0,c1) in enumerate(SEG):
        if t<t1 or i==len(SEG)-1: break
    span=(min(t1,DUR)-t0); p=smooth((t-t0)/span) if span>0 else 0
    s=s0+(s1-s0)*p; cx=c0[0]+(c1[0]-c0[0])*p; cy=c0[1]+(c1[1]-c0[1])*p
    dt=t-t0
    if i>0: s*=1+0.10*(1-ease(dt/0.4))          # punch-in on every cut
    hw,hh=0.5/s,0.5/s
    cx=min(max(cx,hw),1-hw); cy=min(max(cy,hh),1-hh)
    flash=max(0,1-dt/0.22)*(0 if i==0 else 1)
    return s,cx,cy,flash
def warp(fr,s,cx,cy):
    k=W/SW*s   # source->output scale (source fills 1080x1920 at s=1)
    M=np.float32([[k,0,W/2-cx*SW*k],[0,k*(H/SH)/(W/SW),H/2-cy*SH*k*(H/SH)/(W/SW)]])
    return cv2.warpAffine(fr,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
# ---------------- grade ----------------
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
VIG=np.clip(1-((((xx-W/2)/(W*0.75))**2+((yy-H/2)/(H*0.7))**2))*0.9,0,1)[...,None]
PURPLE=np.array([62,40,92],np.float32)
def grade(f,t):
    f=f.astype(np.float32)/255
    l=f.mean(2,keepdims=True)
    f=np.clip((f-0.5)*1.08+0.5,0,1)
    f=f+(1-l)**2*np.array([0.05,-0.02,0.09])+l**2*np.array([0.06,0.025,-0.03])
    # "sol" warm / "lluvia" cool & muted
    if 15.40<t<17.45:
        w=ease((t-15.40)/0.2)*(1-ease((t-15.75)/0.15)); c=ease((t-15.82)/0.25)*(1-ease((t-17.2)/0.25))
        f=f+w*np.array([0.08,0.04,-0.04]); g=f.mean(2,keepdims=True)
        f=f*(1-0.55*c)+g*0.55*c+c*np.array([-0.04,0.0,0.06])-0.06*c
    f=f*255
    f=f*(0.55+0.45*VIG)+PURPLE*(1-VIG)*0.45
    return f
# ---------------- text ----------------
F_SANS='/usr/share/fonts/opentype/inter/Inter-Regular.otf'
def pf(size,w=500,italic=True):
    f=ImageFont.truetype('fonts/PlayfairItalic.ttf' if italic else 'fonts/Playfair.ttf',size)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
FONTS={'s':ImageFont.truetype(F_SANS,70),'m':pf(110,500),'b':pf(175,600),'h':pf(50,400)}
COL={'s':(255,255,255),'m':(236,220,255),'b':(236,218,255),'h':(255,255,255)}
def render_word(txt,st):
    f=FONTS[st]; x0,y0,x1,y1=f.getbbox(txt); pad=40
    w,h=x1-x0+2*pad,y1-y0+2*pad
    im=Image.new('L',(w,h),0); ImageDraw.Draw(im).text((pad-x0,pad-y0),txt,font=f,fill=255)
    a=np.asarray(im,np.float32)/255
    sh=np.clip(np.asarray(im.filter(ImageFilter.GaussianBlur(12)),np.float32)/255*1.1+np.asarray(im.filter(ImageFilter.GaussianBlur(4)),np.float32)/255*0.35,0,0.85)
    rgb=np.ones((h,w,3),np.float32)*np.array(COL[st],np.float32)
    shc=np.array([35,18,52],np.float32)
    # merge text over shadow into one RGBA
    A=a+sh*(1-a)
    C=(rgb*a[...,None]+shc*(sh*(1-a))[...,None])/np.maximum(A,1e-4)[...,None]
    adv=f.getlength(txt)
    return dict(rgb=C,a=A,w=w,h=h,pad=pad,x0=x0,y0=y0,adv=adv,asc=-y0)
import json
WT=[(w['w'].strip(),w['s']) for s in json.load(open('tr.json')) for w in s['words']]
def T(word,idx=0):
    c=[s for w,s in WT if w.lower().strip('¿?,.')==word.lower()]
    return c[idx]
# groups: list of lines; line = list of (text, start, style)
G=[
 [[('¿Puedes',0.78,'s'),('imaginarte',1.34,'s')],[('cómo',1.90,'s'),('va',2.20,'s'),('a',2.38,'s'),('estar',2.52,'s'),('el',2.56,'s'),('día',2.84,'s')]],
 [[('viendo',3.04,'s'),('este',4.28,'s')],[('amanecer?',4.50,'b')]],
 [[('Así',6.08,'s'),('son',6.34,'s'),('los',6.58,'s')],[('registros.',6.70,'b')]],
 [[('No',8.24,'s'),('podemos',8.60,'s')],[('imaginarnos',8.96,'m')],[('cómo',9.78,'s'),('van',10.18,'s'),('a',10.36,'s'),('ser,',10.54,'s')]],
 [[('y',11.74,'s'),('menos',12.16,'s'),('con',12.40,'s'),('estos',12.62,'s'),('días',12.80,'s')],[('que',13.16,'s'),('uno',13.46,'s'),('no',13.70,'s'),('sabe',14.68,'s')],[('si',14.90,'s'),('va',15.14,'s'),('a',15.30,'s'),('haber...',15.34,'s')]],
 [[('sol',15.46,'b')],[('o',15.66,'s')],[('lluvia,',15.88,'b')]],
 [[('los',17.48,'s'),('registros',17.70,'m')],[('se',18.06,'s'),('viven',18.28,'s')],[('el',18.66,'s'),('día',19.12,'s'),('igual.',19.28,'m')]],
 [[('Si',20.78,'s'),('ya',21.16,'s'),('te',21.36,'s')],[('levantaste,',21.48,'m')]],
 [[('si',23.28,'s'),('estás',23.72,'s'),('pensando',23.96,'s')],[('en',24.40,'s'),('los',24.56,'s'),('registros,',24.62,'m')]],
 [[('este',25.70,'s'),('es',26.46,'s')],[('el',26.56,'s'),('momento.',26.68,'b')]],
]
GEND=[g[0][0][1] for g in G[1:]]+[27.55]
YC=1210  # caption block centre
WORDS=[]  # dict per word with absolute pos and timing
SPACE={'s':20,'m':26,'b':30}
LH={'s':92,'m':128,'b':190}
for gi,g in enumerate(G):
    total=sum(LH[max((w[2] for w in line),key=lambda s:LH[s])] for line in g)
    y=YC-total/2
    for line in g:
        lh=LH[max((w[2] for w in line),key=lambda s:LH[s])]
        rs=[render_word(w,st) for w,st_t,st in [(a,b,c) for a,b,c in line]]
        widths=[r['adv'] for r in rs]; tw=sum(widths)+sum(SPACE[line[i][2]] for i in range(len(line)-1))
        x=W/2-tw/2
        base=y+lh*0.78
        for (txt,ts,st),r in zip(line,rs):
            asc=FONTS[st].getmetrics()[0]
            X=int(x+r['x0']-r['pad']); Y=int(base-asc+r['y0']-r['pad'])
            WORDS.append(dict(r=r,X=X,Y=Y,ts=ts,st=st,g=gi,end=GEND[gi]))
            x+=r['adv']+SPACE[st]
        y+=lh
def blit(fr,rgb,a,X,Y,op):
    if op<=0.003: return
    h,w=a.shape; x0,y0=max(0,X),max(0,Y); x1,y1=min(W,X+w),min(H,Y+h)
    if x1<=x0 or y1<=y0: return
    aa=(a[y0-Y:y1-Y,x0-X:x1-X]*op)[...,None]
    fr[y0:y1,x0:x1]=fr[y0:y1,x0:x1]*(1-aa)+rgb[y0-Y:y1-Y,x0-X:x1-X]*aa
def draw_word(fr,wd,t):
    r=wd['r']; p=(t-wd['ts']+0.04)/(0.45 if wd['st']=='b' else 0.32)
    if p<=0: return
    out=1.0; dy_o=0
    if t>wd['end']-0.05:
        q=ease((t-wd['end']+0.05)/0.22); out=1-q; dy_o=-24*q
        if out<=0: return
    e=ease(p)
    if wd['st']=='s':
        blit(fr,r['rgb'],r['a'],wd['X'],int(wd['Y']+26*(1-e)+dy_o),e*out)
    else:
        sc=1.28-0.28*e if wd['st']=='b' else 1.15-0.15*e
        bl=8*(1-e)
        rgb,a=r['rgb'],r['a']
        if abs(sc-1)>0.003 or bl>0.3:
            nw,nh=int(r['w']*sc),int(r['h']*sc)
            rgb=cv2.resize(rgb,(nw,nh)); a=cv2.resize(a,(nw,nh))
            if bl>0.3:
                k=int(bl*3)|1; rgb=cv2.GaussianBlur(rgb,(k,k),bl); a=cv2.GaussianBlur(a,(k,k),bl)
        X=int(wd['X']+r['w']/2-a.shape[1]/2); Y=int(wd['Y']+r['h']/2-a.shape[0]/2+dy_o)
        blit(fr,rgb,a,X,Y,e*out)
SCRIM=(np.exp(-((np.arange(H)-YC)/260.0)**4)*0.42)[:,None,None].astype(np.float32)
HANDLE=render_word('@abuchaljacoach','h')
# glints
gy,gx=np.mgrid[-60:61,-60:61].astype(np.float32)
GLK=np.exp(-(gx**2+gy**2)/(2*6**2))+0.9*np.exp(-(np.abs(gx)/2.2+np.abs(gy)/26))+0.9*np.exp(-(np.abs(gy)/2.2+np.abs(gx)/26))
def glint(fr,x,y,sz,v):
    if v<0.02: return
    r=int(60*sz); k=cv2.resize(GLK,(2*r+1,2*r+1))*v*150
    x0,y0=x-r,y-r
    if x0<0 or y0<0 or x0+2*r+1>W or y0+2*r+1>H: return
    fr[y0:y0+2*r+1,x0:x0+2*r+1]+=k[...,None]*np.array([1.0,0.93,1.0],np.float32)
BIG=[w for w in WORDS if w['st']=='b']
# dust particles
rng=np.random.default_rng(3); N=45
px=rng.uniform(0,W,N); py=rng.uniform(0,H,N); ps=rng.uniform(1,3,N); ph=rng.uniform(0,6.28,N); pv=rng.uniform(10,35,N)
# ---------------- outro (brand card from earlier design) ----------------
OT=27.55
bgT=cv2.cvtColor(cv2.imread('../bg.png'),cv2.COLOR_BGR2RGB).astype(np.float32)
s1=cv2.cvtColor(cv2.imread('../ultimos-lugares-2026-source.webp'),cv2.COLOR_BGR2RGB).astype(np.float32)
s2=cv2.cvtColor(cv2.imread('../registros-akashicos-source.webp'),cv2.COLOR_BGR2RGB).astype(np.float32)
lum=lambda a: a.mean(axis=2)
d2=cv2.GaussianBlur(np.clip((lum(s2)-lum(bgT)-12)/90,0,1),(3,3),0)
d=np.abs(s2-s1).max(2); bm=((d>28)&(np.arange(H)[:,None]>1500)).astype(np.uint8)*255
bm=cv2.morphologyEx(bm,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
cn,_=cv2.findContours(bm,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
bm=np.zeros_like(bm); cv2.drawContours(bm,[c for c in cn if cv2.contourArea(c)>2000],-1,255,-1)
bm=cv2.GaussianBlur(bm.astype(np.float32)/255,(5,5),0)
def lay(box,al=d2): x0,y0,x1,y1=box; return dict(x0=x0,y0=y0,img=s2[y0:y1,x0:x1].copy(),a=al[y0:y1,x0:x1].copy())
O_TITLE=lay((160,805,925,885)); O_PRICE=lay((130,885,960,1160))
O_PILLS=[lay((a,1238,b,1318)) for a,b in [(90,440),(440,640),(640,992)]]
BOOK=lay((0,1500,1080,1920),bm)
BY0=1500; PVX,PVY=540.0,1918.0-BY0
bh,bw=BOOK['a'].shape; yb,xb=np.mgrid[0:bh,0:bw].astype(np.float32)
ANG=np.degrees(np.arctan2(PVY-yb,xb-PVX)); ANG=np.where(ANG<-90,180,np.clip(ANG,0,180))
SECT=[]
for (a0,a1) in ((90,180),(0,90)):
    ed=np.linspace(a0,a1,13)
    for i in range(12):
        lo,hi=ed[i],ed[i+1]; wgt=np.clip((ANG-lo+0.4)/0.8,0,1)*np.clip((hi-ANG+0.4)/0.8,0,1)
        aw=BOOK['a']*wgt
        if aw.max()>0.05: SECT.append(((lo+hi)/2,aw))
CTA=render_word('Reserva tu lugar ✦ escríbeme','s') if False else None
FONTS['c']=ImageFont.truetype(F_SANS,50); COL['c']=(255,255,255)
CTA=render_word('Reserva tu lugar · escríbeme por DM','c')
def comp(fr,img,alpha,cx,cy,scale,op,blur=0,rot=0):
    if op<=0.003: return
    h,w=alpha.shape
    M=cv2.getRotationMatrix2D((w/2,h/2),rot,scale); M[0,2]+=cx-w/2; M[1,2]+=cy-h/2
    im=cv2.warpAffine(img,M,(W,H)); al=cv2.warpAffine(alpha,M,(W,H))
    if blur>0.3:
        k=int(blur*3)|1; im=cv2.GaussianBlur(im,(k,k),blur); al=cv2.GaussianBlur(al,(k,k),blur)
    al=(al*op)[...,None]; fr[:]=fr*(1-al)+im*al
def outro(fr,t):
    tb=t-OT
    if tb<0: return fr
    k=ease(tb/0.7)
    sm=cv2.GaussianBlur(fr,(0,0),1+14*k)
    fr=sm*(1-0.72*k)+np.array([86,60,118],np.float32)*0.72*k
    L=O_TITLE; e=ease((tb-0.45)/0.6)
    blit(fr,L['img'],L['a'],L['x0'],int(L['y0']+40*(1-e)),e)
    L=O_PRICE; e=ease((tb-0.8)/0.9); h,w=L['a'].shape
    comp(fr,L['img'],L['a'],L['x0']+w/2,L['y0']+h/2,1.25-0.25*e,e,blur=10*(1-e))
    for i,L in enumerate(O_PILLS):
        p=(tb-1.45-0.18*i)/0.55; h,w=L['a'].shape
        comp(fr,L['img'],L['a'],L['x0']+w/2,L['y0']+h/2,0.6+0.4*backout(p),ease(p*1.4))
    e=ease((tb-2.2)/0.5); blit(fr,CTA['rgb'],CTA['a'],int(W/2-CTA['w']/2),int(1395+20*(1-e)),e*0.95)
    # book opens (closed -> open, left to right)
    bt=tb-1.0
    if bt>0:
        items=[]; CL=150.0
        right=sorted([z for z in SECT if z[0]<90],key=lambda z:z[0])
        for ca,aw in SECT:
            if ca>90:
                e=smooth((bt-0.15-0.5*(ca-90)/90)/0.9); items.append((1,(CL-ca)*(1-e),aw))
        for j,(ca,aw) in enumerate(right):
            q=(bt-0.2-j*0.13)/0.75; e=smooth(q)
            items.append(((j*1e-3) if q>=1 else (2-j*1e-3 if q<=0 else 3+j*1e-3),(CL-ca)*(1-e),aw))
        items.sort(key=lambda z:z[0])
        for _,rot,aw in items:
            M=cv2.getRotationMatrix2D((PVX,PVY),rot,1.0); M[1,2]+=BY0
            im=cv2.warpAffine(BOOK['img'],M,(W,H)); al=(cv2.warpAffine(aw,M,(W,H))*min(1,bt*5))[...,None]
            fr=fr*(1-al)+im*al
        gv=max(0,math.sin(math.pi*min(1,bt/2.2)))
        if gv>0.01:
            g=np.exp(-(((xx[1520:1920]-PVX)/170)**2+((yy[1520:1920]-1918)/150)**2))*gv*110
            fr[1520:1920]+=g[...,None]*np.array([1.0,0.92,0.75],np.float32)
    if tb>1.6:
        for gx_,gy_,sz,phs in [(876,930,1.0,0.0),(907,906,0.5,1.3),(925,956,0.6,2.1),(163,1091,0.8,0.7),(196,1106,0.45,2.6)]:
            glint(fr,gx_,gy_,sz,max(0,math.sin((tb-1.6)*3.0+phs))**3*min(1,(tb-1.6)/0.5))
    return fr
# ---------------- main loop ----------------
dec=subprocess.Popen(['ffmpeg','-loglevel','error','-i',SRC,'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
  '-i',SRC,'-map','0:v','-map','1:a','-af','highpass=f=80,afftdn=nf=-25,loudnorm=I=-14:TP=-1.5:LRA=11',
  '-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-profile:v','high','-movflags','+faststart',
  '-c:a','aac','-b:a','160k','-ar','48000','-t',f'{DUR:.3f}',OUT],stdin=subprocess.PIPE)
last=None
for f in range(NF):
    t=f/FPS
    buf=dec.stdout.read(SW*SH*3)
    if len(buf)==SW*SH*3: last=np.frombuffer(buf,np.uint8).reshape(SH,SW,3)
    s,cx,cy,flash=camera(t)
    fr=grade(warp(last,s,cx,cy),t)
    if flash>0: fr=fr+flash*70
    if t>26.62 and t<27.4: fr=fr+60*max(0,1-(t-26.66)/0.5)*(t>26.66)   # glow on "momento"
    for i in range(N):
        a=(0.5+0.5*math.sin(t*2.0+ph[i]))
        y=(py[i]-pv[i]*t)%H; x=px[i]+8*math.sin(t*0.7+ph[i])
        if a>0.6 and not (900<y<1500 and 80<x<1000): cv2.circle(fr,(int(x),int(y)),int(ps[i]+0.5),(255,240,225),-1,cv2.LINE_AA)
    sv=ease((t-0.5)/0.4)*(1-ease((t-OT)/0.5))
    if sv>0: fr=fr*(1-SCRIM*sv)+np.array([40,22,62],np.float32)*SCRIM*sv
    if t<OT+0.6:
        for wd in WORDS: draw_word(fr,wd,t)
        for wd in BIG:
            dt=t-wd['ts']-0.35
            if 0<dt<wd['end']-wd['ts']-0.4:
                v=max(0,math.sin(dt*3.2))**3*min(1,dt/0.3)
                glint(fr,int(wd['X']+wd['r']['w']-wd['r']['pad']+8),int(wd['Y']+wd['r']['pad']+10),0.7,v)
    fr=outro(fr,t)
    hp=ease((t-0.3)/0.6)
    blit(fr,HANDLE['rgb'],HANDLE['a'],int(W/2-HANDLE['w']/2),230,hp*0.9 if t<OT else hp*0.9*(1-ease((t-OT)/0.5)))
    fr=fr*min(1,t/0.4)
    enc.stdin.write(np.clip(fr,0,255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); dec.kill()
