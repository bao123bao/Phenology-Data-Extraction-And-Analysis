# -*- coding: utf-8 -*-
"""
Created on Sat Sep 17 11:16:20 2022
 
@author: ch611
"""

import rasterio,os

inPath=r'D:\文件\华癸项目\DATA\SNAPPED\max_temp'
imgFile='20050818max_temp.tif'
dataset = rasterio.open(os.path.join(inPath,imgFile))

print((dataset.transform))
print(dataset.bounds)

print(dataset.transform * (dataset.width, dataset.height))
print(dataset.crs)

#%%



