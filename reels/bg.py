import cv2, numpy as np
im=cv2.imread('ultimos-lugares-2026-source.webp')
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
v=hsv[...,2].astype(int); s=hsv[...,1].astype(int)
# text: bright and low-ish saturation
m=((v>175)&(s<110)).astype(np.uint8)*255
band=np.zeros_like(m); band[640:1320,80:1000]=1
m=m*band
m=cv2.dilate(m,np.ones((7,7),np.uint8),iterations=2)
cv2.imwrite('mask.png',m)
bg=cv2.inpaint(im,m,15,cv2.INPAINT_TELEA)
# smooth inpainted area a bit
bl=cv2.GaussianBlur(bg,(0,0),9)
mf=cv2.GaussianBlur(m,(0,0),12).astype(float)[...,None]/255
bg=(bg*(1-mf)+bl*mf).astype(np.uint8)
cv2.imwrite('bg.png',bg)
