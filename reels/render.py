import cv2, numpy as np, subprocess, math
W,H,FPS,DUR=1080,1920,30,7.0
src=cv2.imread('ultimos-lugares-2026-source.webp').astype(np.float32)
bg=cv2.imread('bg.png').astype(np.float32)
lum=lambda a: a.mean(axis=2)
diff=np.clip((lum(src)-lum(bg)-12)/90,0,1)
diff=cv2.GaussianBlur(diff,(3,3),0)
# elements: (x0,y0,x1,y1, start, kind)
els=[(380,640,700,715,0.35,'up'),
     (280,765,810,900,0.75,'zoom'),
     (120,900,960,1035,1.15,'zoom'),
     (100,1060,980,1190,1.95,'up'),
     (90,1238,440,1318,2.75,'pop'),
     (440,1238,640,1318,2.95,'pop'),
     (640,1238,992,1318,3.15,'pop')]
layers=[]
for x0,y0,x1,y1,t0,k in els:
    a=diff[y0:y1,x0:x1].copy()
    layers.append((x0,y0,src[y0:y1,x0:x1].copy(),a,t0,k))
ease=lambda p: 1-(1-max(0,min(1,p)))**3
def backout(p):
    p=max(0,min(1,p)); c=1.7; return 1+(c+1)*(p-1)**3+c*(p-1)**2
rng=np.random.default_rng(7)
N=70
px=rng.uniform(0,W,N); py=rng.uniform(0,H,N); ps=rng.uniform(1,3.2,N); ph=rng.uniform(0,6.28,N); pv=rng.uniform(8,30,N)
def comp(frame,img,alpha,cx,cy,scale,op,blur=0):
    if op<=0.003: return
    h,w=alpha.shape
    M=np.float32([[scale,0,cx-w*scale/2],[0,scale,cy-h*scale/2]])
    im=cv2.warpAffine(img,M,(W,H),flags=cv2.INTER_LINEAR,borderValue=0)
    al=cv2.warpAffine(alpha,M,(W,H),flags=cv2.INTER_LINEAR,borderValue=0)
    if blur>0.3:
        k=int(blur*3)|1; im=cv2.GaussianBlur(im,(k,k),blur); al=cv2.GaussianBlur(al,(k,k),blur)
    al=(al*op)[...,None]
    frame[:]=frame*(1-al)+im*al
ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
  '-f','lavfi','-t',str(DUR),'-i','anullsrc=r=44100:cl=stereo',
  '-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-profile:v','high','-movflags','+faststart',
  '-c:a','aac','-b:a','128k','-shortest','ultimos-lugares-2026.mp4'],stdin=subprocess.PIPE)
nf=int(DUR*FPS)
for f in range(nf):
    t=f/FPS
    # background: slow push-in + slight drift
    s=1.0+0.07*(t/DUR); dx=-12*(t/DUR)
    M=np.float32([[s,0,W/2-W*s/2+dx],[0,s,H/2-H*s/2]])
    fr=cv2.warpAffine(bg,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    # sparkles
    for i in range(N):
        tw=0.5+0.5*math.sin(t*2.2+ph[i]); a=0.55*tw*min(1,t/1.0)
        y=(py[i]-pv[i]*t)%H; x=px[i]+6*math.sin(t*0.8+ph[i])
        cv2.circle(fr,(int(x),int(y)),int(ps[i]+0.5),(255,225,240),-1,cv2.LINE_AA) if (a>0.35 and not (620<y<1330 and 80<x<1000)) else None
    for x0,y0,img,al,t0,k in layers:
        h,w=al.shape; cx=x0+w/2; cy=y0+h/2
        p=(t-t0)/0.7
        if k=='up':
            e=ease(p); comp(fr,img,al,cx,cy+40*(1-e),1,e)
        elif k=='zoom':
            e=ease((t-t0)/0.9)
            glow=1.0
            # gentle breathing on titles after intro
            if t>3.8: glow=1+0.015*math.sin((t-3.8)*2.4)
            comp(fr,img,al,cx,cy,(1.25-0.25*e)*glow,e,blur=10*(1-e))
        else:
            b=backout((t-t0)/0.55); e=ease((t-t0)/0.4)
            comp(fr,img,al,cx,cy,0.6+0.4*b,e)
    # shimmer sweep across title block 4.2-5.4s
    sp=(t-4.2)/1.2
    if 0<sp<1:
        xs=np.arange(W)[None,:]; ys=np.arange(H)[:,None]
        c=-300+sp*(W+600)
        band=np.exp(-((xs+ (ys-900)*0.35 - c)/60.0)**2)
        m=np.zeros((H,W),np.float32); m[765:1035,:]=diff[765:1035,:]
        add=(band*m*110)[...,None]
        fr=fr+add
    # fade in/out
    fa=min(1,t/0.5)
    fr=fr*fa
    ff.stdin.write(np.clip(fr,0,255).astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait()
