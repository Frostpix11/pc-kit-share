# clean.py src out_art.png W H colors : Codex picture -> honest pixel art W×H, `colors` palette
import sys, numpy as np
from PIL import Image
src,out,W,H,N=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5])
im=Image.open(src).convert('RGB'); a=np.asarray(im,dtype=float)
h,w,_=a.shape
# crop to 16:9 centred
th=round(w*H/W)
if th<=h: y0=(h-th)//2; a=a[y0:y0+th]; h=th
else:
    tw=round(h*W/H); x0=(w-tw)//2; a=a[:,x0:x0+tw]; w=tw
cw,ch=w/W,h/H
art=np.zeros((H,W,3))
for j in range(H):
    y1,y2=int(j*ch+ch*0.2),max(int(j*ch+ch*0.8),int(j*ch+ch*0.2)+1)
    for i in range(W):
        x1,x2=int(i*cw+cw*0.2),max(int(i*cw+cw*0.8),int(i*cw+cw*0.2)+1)
        art[j,i]=np.median(a[y1:y2,x1:x2].reshape(-1,3),axis=0)
def oklab(rgb):
    c=rgb/255.0; c=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
    M1=np.array([[0.4122214708,0.5363325363,0.0514459929],[0.2119034982,0.6806995451,0.1073969566],[0.0883024619,0.2817188376,0.6299787005]])
    lms=np.cbrt(c@M1.T)
    M2=np.array([[0.2104542553,0.7936177850,-0.0040720468],[1.9779984951,-2.4285922050,0.4505937099],[0.0259040371,0.7827717662,-0.8086757660]])
    return lms@M2.T
img=Image.fromarray(art.clip(0,255).astype(np.uint8))
px=art.reshape(-1,3); L=oklab(px)
chroma=np.hypot(L[:,1],L[:,2])
# base palette (median cut) + reserved accents (the highest-chroma warm/bright pixels: window,
# lantern, flowers) so a few pixels aren't averaged into the sky
base=img.quantize(colors=N-12,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGB')
pal=np.unique(np.asarray(base).reshape(-1,3),axis=0).astype(float)
acc=px[chroma>=np.quantile(chroma,0.99)]
if len(acc)>=12:
    ai=Image.fromarray(acc.reshape(1,-1,3).astype(np.uint8)).quantize(colors=12,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGB')
    pal=np.vstack([pal,np.unique(np.asarray(ai).reshape(-1,3),axis=0)])
P=oklab(pal)
idx=np.empty(len(L),int)
for i in range(0,len(L),20000):
    d=((L[i:i+20000,None,:]-P[None])**2).sum(2); idx[i:i+20000]=d.argmin(1)
res=Image.fromarray(pal[idx].reshape(art.shape).astype(np.uint8)); res.save(out)
print(out, len(res.getcolors(1000)), 'colours')
