import cv2, numpy as np, subprocess, math, sys
W,H,FPS=1080,1920,30
SRC1,SRC2,OUT=sys.argv[1:4] if len(sys.argv)>3 else ('ultimos-lugares-2026-source.webp','registros-akashicos-source.webp','ultimos-lugares-y-registros-akashicos.mp4')
DUR=14.0
src=cv2.imread(SRC1).astype(np.float32)
src2=cv2.imread(SRC2).astype(np.float32)
bg=cv2.imread('bg.png').astype(np.float32)
lum=lambda a: a.mean(axis=2)
def tmask(s): return cv2.GaussianBlur(np.clip((lum(s)-lum(bg)-12)/90,0,1),(3,3),0)
diff=tmask(src); diff2=tmask(src2)
# book mask: where img2 differs from img1 in bottom area
d=np.abs(src2-src).max(2); bm=((d>28)&(np.arange(H)[:,None]>1500)).astype(np.uint8)*255
bm=cv2.morphologyEx(bm,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
cnts,_=cv2.findContours(bm,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
bm=np.zeros_like(bm); cv2.drawContours(bm,[c for c in cnts if cv2.contourArea(c)>2000],-1,255,-1)
bm=cv2.GaussianBlur(bm.astype(np.float32)/255,(5,5),0)
L=[]
def add(img,al,box,t_in,kind,t_out=None,dur=0.7,excl=()):
    x0,y0,x1,y1=box; a=al[y0:y1,x0:x1].copy()
    for ex0,ey0,ex1,ey1 in excl: a[max(0,ey0-y0):ey1-y0,max(0,ex0-x0):ex1-x0]=0
    L.append(dict(x0=x0,y0=y0,img=img[y0:y1,x0:x1].copy(),a=a,t_in=t_in,k=kind,t_out=t_out,dur=dur))
# part 1
add(src,diff,(380,640,700,715),0.35,'up')
add(src,diff,(280,765,810,900),0.75,'zoom',7.0)
add(src,diff,(120,900,960,1035),1.15,'zoom',7.1)
add(src,diff,(100,1060,980,1190),1.95,'up',7.2)
for i,(a,b) in enumerate([(90,440),(440,640),(640,992)]): add(src,diff,(a,1238,b,1318),2.75+0.2*i,'pop')
# part 2
S1=(835,885,950,985); S2=(135,1055,225,1125)
add(src2,diff2,(160,805,925,885),7.55,'up')
add(src2,diff2,(130,885,960,1160),7.95,'zoom',dur=0.9)
GL=[(876,930,1.0,0.0),(907,906,0.5,1.3),(925,956,0.6,2.1),(163,1091,0.8,0.7),(196,1106,0.45,2.6)]
yy,xx=np.mgrid[-60:61,-60:61].astype(np.float32)
GLK=np.exp(-(xx**2+yy**2)/(2*6**2))+0.9*np.exp(-(np.abs(xx)/2.2+np.abs(yy)/26))+0.9*np.exp(-(np.abs(yy)/2.2+np.abs(xx)/26))
add(src2,bm,(0,1500,1080,1920),8.3,'book',dur=1.1)
# book opening: split into angular page sectors around spine pivot
BY0=1500; PVX,PVY=540.0,1918.0-BY0
_b=[l for l in L if l['k']=='book'][0]
bh,bw=_b['a'].shape
yy_,xx_=np.mgrid[0:bh,0:bw].astype(np.float32)
ANG=np.degrees(np.arctan2(PVY-yy_,xx_-PVX)); ANG=np.where(ANG<-90,180,np.clip(ANG,0,180))
SECT=[]; NS=12; RW=0.8
for side,(a0,a1) in (('L',(90,180)),('R',(0,90))):
    edges=np.linspace(a0,a1,NS+1)
    for i in range(NS):
        lo,hi=edges[i],edges[i+1]
        w=np.clip((ANG-lo+RW/2)/RW,0,1)*np.clip((hi-ANG+RW/2)/RW,0,1)
        if side=='L' and i==0: w=np.clip((ANG-lo+RW/2)/RW,0,1)*(ANG<=hi+RW/2)*np.clip((hi-ANG+RW/2)/RW,0,1)
        aw=_b['a']*w
        if aw.max()<0.05: continue
        SECT.append(((lo+hi)/2,aw))
SECT.sort(key=lambda z:-abs(z[0]-90))  # outer first, inner pages on top
ease=lambda p: 1-(1-max(0,min(1,p)))**3
def backout(p):
    p=max(0,min(1,p)); c=1.7; return 1+(c+1)*(p-1)**3+c*(p-1)**2
YG,XG=np.mgrid[0:400,0:W].astype(np.float32)
rng=np.random.default_rng(7); N=70
px=rng.uniform(0,W,N); py=rng.uniform(0,H,N); ps=rng.uniform(1,3.2,N); ph=rng.uniform(0,6.28,N); pv=rng.uniform(8,30,N)
def comp(fr,img,alpha,cx,cy,scale,op,blur=0,rot=0):
    if op<=0.003: return
    h,w=alpha.shape
    M=cv2.getRotationMatrix2D((w/2,h/2),rot,scale); M[0,2]+=cx-w/2; M[1,2]+=cy-h/2
    im=cv2.warpAffine(img,M,(W,H),flags=cv2.INTER_LINEAR,borderValue=0)
    al=cv2.warpAffine(alpha,M,(W,H),flags=cv2.INTER_LINEAR,borderValue=0)
    if blur>0.3:
        k=int(blur*3)|1; im=cv2.GaussianBlur(im,(k,k),blur); al=cv2.GaussianBlur(al,(k,k),blur)
    al=(al*op)[...,None]; fr[:]=fr*(1-al)+im*al
def shimmer(fr,t,t0,mask,y0,y1,yc):
    sp=(t-t0)/1.2
    if not 0<sp<1: return fr
    xs=np.arange(W)[None,:]; ys=np.arange(H)[:,None]
    band=np.exp(-((xs+(ys-yc)*0.35-(-300+sp*(W+600)))/60.0)**2)
    m=np.zeros((H,W),np.float32); m[y0:y1]=mask[y0:y1]
    return fr+(band*m*110)[...,None]
ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
  '-f','lavfi','-t',str(DUR),'-i','anullsrc=r=44100:cl=stereo','-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p',
  '-profile:v','high','-movflags','+faststart','-c:a','aac','-b:a','128k','-shortest',OUT],stdin=subprocess.PIPE)
for f in range(int(DUR*FPS)):
    t=f/FPS
    s=1.0+0.07*(t/7); dx=-12*(t/7)
    M=np.float32([[s,0,W/2-W*s/2+dx],[0,s,H/2-H*s/2]])
    fr=cv2.warpAffine(bg,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    for i in range(N):
        a=0.55*(0.5+0.5*math.sin(t*2.2+ph[i]))*min(1,t)
        y=(py[i]-pv[i]*t)%H; x=px[i]+6*math.sin(t*0.8+ph[i])
        if a>0.35 and not (620<y<1330 and 80<x<1000): cv2.circle(fr,(int(x),int(y)),int(ps[i]+0.5),(255,225,240),-1,cv2.LINE_AA)
    for l in L:
        h,w=l['a'].shape; cx=l['x0']+w/2; cy=l['y0']+h/2; k=l['k']; p=(t-l['t_in'])/l['dur']
        if t<l['t_in']: continue
        out=1.0; ob=0; osc=0
        if l['t_out'] is not None and t>l['t_out']:
            q=ease((t-l['t_out'])/0.55); out=1-q; ob=8*q; osc=0.08*q
            if out<=0: continue
        if k=='up':
            e=ease(p); comp(fr,l['img'],l['a'],cx,cy+40*(1-e)-30*osc,1,e*out,blur=ob)
        elif k=='zoom':
            e=ease(p); g=1+0.015*math.sin((t-l['t_in']-3)*2.4) if t-l['t_in']>3 else 1
            comp(fr,l['img'],l['a'],cx,cy,(1.25-0.25*e)*g+osc,e*out,blur=10*(1-e)+ob)
        elif k=='pop':
            comp(fr,l['img'],l['a'],cx,cy,0.6+0.4*backout(p/0.55*0.7),ease(p/0.4*0.7))
        elif k=='star':
            e=backout(p/0.6*0.7); tw=1+0.18*math.sin((t-l['t_in'])*4.5)
            comp(fr,l['img'],l['a'],cx,cy,max(0.01,e*tw),ease(p),rot=(1-ease(p))*90)
        elif k=='book':
            tb=t-l['t_in']; rise=ease(tb/0.45); bob=4*math.sin((tb-1.7)*1.8) if tb>1.7 else 0
            dy=bob
            left=[z for z in SECT if z[0]>90]; right=sorted([z for z in SECT if z[0]<90],key=lambda z:z[0])
            items=[]
            for ca,aw in left:
                e=ease(tb/0.6); items.append((0,(180-ca)*0.35*(1-e),aw))
            nr=len(right)
            for j,(ca,aw) in enumerate(right):
                st=0.05+j*0.16; q=(tb-st)/0.75
                e=1-(1-max(0,min(1,q)))**2 if q<1 else 1
                e=0.5-0.5*math.cos(math.pi*max(0,min(1,q)))  # smooth page turn
                state=2 if q>=1 else (1 if q<=0 else 3)
                items.append((state if state!=2 else 0.5+j*1e-3,(180-2*ca)*(1-e),aw))
            items.sort(key=lambda z:z[0])
            for _,rot,aw in items:
                M=cv2.getRotationMatrix2D((PVX,PVY),rot,1.0); M[1,2]+=BY0+dy
                im=cv2.warpAffine(l['img'],M,(W,H),flags=cv2.INTER_LINEAR,borderValue=0)
                al=cv2.warpAffine(aw,M,(W,H),flags=cv2.INTER_LINEAR,borderValue=0)
                al=(al*min(1,tb*4))[...,None]; fr[:]=fr*(1-al)+im*al
            gv=max(0,math.sin(math.pi*min(1,max(0,tb/2.2))))
            if gv>0.01:
                gy0=int(BY0+PVY+dy)-260
                g=np.exp(-(((XG-PVX)/170)**2+((YG-260)/150)**2))*gv*120
                y0c=max(0,gy0); y1c=min(H,gy0+400)
                if y1c>y0c: fr[y0c:y1c]+= (g[y0c-gy0:y1c-gy0,...,None]*np.array([0.75,0.92,1.0],np.float32))
    if t>8.6:
        for gx,gy,sz,phs in GL:
            v=max(0,math.sin((t-8.6)*3.0+phs))**3*min(1,(t-8.6)/0.5)
            if v<0.02: continue
            r=int(60*sz); k=cv2.resize(GLK,(2*r+1,2*r+1))*v*150
            fr[gy-r:gy+r+1,gx-r:gx+r+1]+=k[...,None]*np.array([1.0,0.92,1.0],np.float32)
    fr=shimmer(fr,t,4.2,diff,765,1035,900)
    fr=shimmer(fr,t,10.6,diff2,890,1160,1020)
    fr=fr*min(1,t/0.5)
    ff.stdin.write(np.clip(fr,0,255).astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait()
