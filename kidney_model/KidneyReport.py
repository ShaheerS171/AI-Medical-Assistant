import segmentation_models_pytorch as smp
import numpy as np
import cv2
import pandas as pd
import torch
import torch.nn
import os
import albumentations as A
import matplotlib.pyplot as plt

transform = A.Compose([
    A.LongestMaxSize(max_size=768),
    A.PadIfNeeded(
        min_height=768,
        min_width=768,
        border_mode = cv2.BORDER_CONSTANT,
        fill = 0,
        fill_mask = 0),    
])


path = "./kidney_model"
img1name = "3_IM-0359-0014_anon.png" #Longitudal View for Length (3_IM-0359-0014_anon.png,13_IM-0293-0055_anon.png)
img2name = "1_IM-0001-0059_anon.png" #Transverse View for Width and Thickness (1_IM-0001-0059_anon.png,28_IM-0671-0056_anon.png)
img1 = cv2.imread(os.path.join(path,img1name))
original_w1,original_h1 = img1.shape[:2]
scale1 = min(768/original_w1,768/original_h1)
img2 = cv2.imread(os.path.join(path,img2name))
original_w2,original_h2 = img2.shape[:2]
scale2 = min(768/original_w2,768/original_h2)
aug1 = transform(image=img1,mask=None)
aug2 = transform(image=img2,mask=None)
img1 = aug1['image']
img2 = aug2['image']


model = smp.DeepLabV3Plus(encoder_name='efficientnet-b3',encoder_weights='imagenet',in_channels=3,classes=2)
weights = torch.load("./hackathon/weights.pth")
model.load_state_dict(weights['model_state_dict'])

def predict(model,img):
    model.eval()
    img = (img.astype(np.float32)/255.0)
    img = torch.from_numpy(img)
    img = img.permute(2,0,1).unsqueeze(0)
    prediction = model(img)
    prediction = prediction.argmax(dim=1).squeeze(0)
    return prediction

pred1 = predict(model,img1).cpu().numpy().astype(np.uint8)
pred2 = predict(model,img2).cpu().numpy().astype(np.uint8)

def findlines(pred,view="L"):
    contours,_ = cv2.findContours(pred,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    contour = max(contours,key=cv2.contourArea)
    points = contour[:,0,:]
    center = points.mean(axis=0)
    centeredpoints = points-center

    _,_,pca = np.linalg.svd(centeredpoints,full_matrices=False)
    line = []

    if view=="L":
        noofaxis = 1
    else:
        noofaxis = 2

    for i in range(0,noofaxis):
        projections = centeredpoints@pca[i]
        line.append([points[projections.argmin()],points[projections.argmax()]])
                    #[[(x,y),(x,y)]]
                    #[[(x,y),(x,y)],[(x,y),(x,y)]]
    return line

line1 = findlines(pred1,"L")[0] #[(x,y),(x,y)]
line2,line3 = findlines(pred2,"T") #[(x,y),(x,y)],[(x,y),(x,y)]

def distance(line):
    return np.sqrt((line[0][0]-line[1][0])**2 + (line[0][1]-line[1][1])**2)

def illustrate(img,line):
    imgwithline = cv2.line(img,tuple(line[0]),tuple(line[1]),(0,0,255),2)
    return imgwithline



df = pd.read_excel("./hackathon/OpenKidneyUltrasoundDataSet_TransducerInfo.xlsx")

def getscale(df,filenames):
    values = []
    for i in range(0,len(filenames)):
        filename = filenames[i].replace("_anon.png","")
        mf = df[df["Filename"]==filename]
        if mf["Physical Delta X"].iloc[0]==1:
            values.append([df["Physical Delta X"].median(),df["Physical Delta Y"].median()])
        else:
            values.append([mf["Physical Delta X"].iloc[0],mf["Physical Delta Y"].iloc[0]])
    return values
    #[[sx1,sy1],[sx2,sy2]]

im1cm,im2cm = getscale(df,[img1name,img2name])
sx1,sy1 = im1cm
sx2,sy2 = im2cm

def pixelstocm(scale,dx,dy,line):
    dist_x = line[0][0]-line[1][0]
    dist_y = line[0][1]-line[1][1]
    dist_x = dist_x*(abs(dx)/scale)
    dist_y = dist_y*(abs(dy)/scale)
    length = np.sqrt(dist_x**2+dist_y**2)   
    return length

length = pixelstocm(scale1,sx1,sy1,line1)
width = pixelstocm(scale2,sx2,sy2,line2)
thickness = pixelstocm(scale2,sx2,sy2,line3)

print(f"Length of the Kidney : {round(length,2)}cm")
print(f"Width of the Kidney : {round(width,2)}cm")
print(f"Thickness of the Kidney : {round(thickness,2)}cm")

fig,axes = plt.subplots(2,2)
axes = axes.flatten()
axes[0].imshow(img1)
axes[1].imshow(illustrate(img1,line1))
axes[2].imshow(img2)
img2withline = illustrate(img2,line2)
axes[3].imshow(illustrate(img2withline,line3))
plt.tight_layout()
plt.show()
