# 根据物候累加NSSR
import rasterio
import os
import numpy as np
import datetime
import time

def readRaster(path):
    rasterObj=rasterio.open(path)
    rasterArray=rasterObj.read(1)
    rasterObj.close()
    return rasterArray

def writeRaster(outPath,fileName,data,reference,dtype):
    new_dataset = rasterio.open(
        os.path.join(outPath,fileName),
        'w',
        driver='GTiff',
        height=reference.shape[0],
        width=reference.shape[1],
        count=1,
        dtype=dtype,
        crs=reference.crs,
        transform=reference.transform,
    )
    new_dataset.write(data, 1)
    new_dataset.close()

def getFilesOrigin(path,end):
    '''
    return names,paths
    '''
    nameList=[]
    pathList=[]
    fileList=os.listdir(path)
    for file in fileList:
        if file.endswith(end): 
            nameList.append(file)
            pathList.append(os.path.join(path,file))
    return nameList,pathList


def getFiles(path,end,year):
    '''
    return names,paths
    '''
    nameList=[]
    pathList=[]
    fileList=os.listdir(path)
    for file in fileList:
        if file.endswith(end) and file.startswith(str(year)): 
            nameList.append(file)
            pathList.append(os.path.join(path,file))
    return nameList,pathList

def dateToUnix(date):
    '''
    date is in format '20050101', str
    return: unix epoch day, int
    '''
    year=int(date[:4])
    month=int(date[4:6])
    day=int(date[6:])
    date_time=datetime.datetime(year, month, day)
    sec_unix=time.mktime(date_time.timetuple())
    day_unix=int(sec_unix/(3600*24))
    
    return day_unix

def unixToDate(unix_day):
    '''
    unix epoch day, int
    return: date is in format '20050101', str
    '''
    sec_unix=unix_day*(3600*24)
    date_time=datetime.datetime.fromtimestamp(sec_unix)
    date_time+=datetime.timedelta(days=1)
    date_string=date_time.strftime('%Y%m%d')
    return date_string

#%%
path=r'F:\cornDATA\timesat\data\wa'

def getFilesOrigin(path,end):
    '''
    return names,paths
    '''
    nameList=[]
    pathList=[]
    fileList=os.listdir(path)
    for file in fileList:
        if file.endswith(end) and 'wa_nd' in file: 
            nameList.append(file)
            pathList.append(os.path.join(path,file))
    return nameList,pathList

names,paths=getFilesOrigin(path,'.img')
print(paths)

with open(os.path.join(path,'your_file.txt'), 'w') as f:
    for line in paths:
        f.write(f"{line}\n")






#%%

# 计算KDD、GDD-1004
PHENO_ROOT_PATH=r'D:\文件\华癸项目\test\phenoAllYears0908\outpath_result'
FACTOR_ROOT_PATH_MIN=r'F:\cornDATA\SNAPPED\min_temp'
FACTOR_ROOT_PATH_MAX=r'F:\cornDATA\SNAPPED\max_temp'

ORDER=('Greenup','MidGreenup','Maturity','Peak','Senescence','MidGreendown','Dormancy')

for YEAR in range(2012,2020):
    
    # YEAR=2005
    print('=============NEW YEAR=============')
    print(YEAR)
    PHENO_FILE_NAMES,PHENO_FILE_PATHS=getFiles(PHENO_ROOT_PATH,'.img',YEAR)
    FACTOR_FILE_NAMES_MIN,FACTOR_FILE_PATHS_MIN=getFiles(FACTOR_ROOT_PATH_MIN,'.tif',YEAR)
    FACTOR_FILE_NAMES_MAX,FACTOR_FILE_PATHS_MAX=getFiles(FACTOR_ROOT_PATH_MAX,'.tif',YEAR)
    
    print(len(FACTOR_FILE_NAMES_MIN))
    print(len(FACTOR_FILE_NAMES_MAX))

    for step in range(6):
        # 开始和结束物候期的名称
        startStageName=str(YEAR)+'_'+ORDER[step]+'.img'
        endStageName=str(YEAR)+'_'+ORDER[step+1]+'.img'
        print(startStageName,endStageName)

        # 开始的物候数组
        phenoStartPath=os.path.join(PHENO_ROOT_PATH,startStageName)
        phenoStartObject=rasterio.open(phenoStartPath)
        phenoStartArray=phenoStartObject.read(1)


        # 结束的物候数组
        phenoEndPath=os.path.join(PHENO_ROOT_PATH,endStageName)    
        phenoEndArray=readRaster(phenoEndPath)
        
        
        minDate=unixToDate(phenoStartArray[phenoStartArray!=0].min())
        maxDate=unixToDate(phenoEndArray.max())
        print((minDate,maxDate))

        indexStart=FACTOR_FILE_NAMES_MIN.index(minDate+'min_temp.tif')
        indexEnd=FACTOR_FILE_NAMES_MIN.index(maxDate+'min_temp.tif')
        print((indexStart,indexEnd))

        reducedFactorNamesMin=FACTOR_FILE_NAMES_MIN[indexStart:indexEnd+1]
        reducedFactorFilePathsMin=FACTOR_FILE_PATHS_MIN[indexStart:indexEnd+1]
        
        reducedFactorNamesMax=FACTOR_FILE_NAMES_MAX[indexStart:indexEnd+1]
        reducedFactorFilePathsMax=FACTOR_FILE_PATHS_MAX[indexStart:indexEnd+1]
        
        print(len(reducedFactorNamesMin))
        print(len(reducedFactorNamesMax))
        
        # 预读取temp_min，存放入stackArrayMin
        cnt=0
        first_flag=True
        for file in reducedFactorFilePathsMin:
            array=readRaster(file)
            vector=array.flatten()
            if first_flag:
                stackArrayMin=vector
                first_flag=False
            else:
                stackArrayMin=np.vstack((stackArrayMin,vector))
            print(cnt,end=' ')
            cnt+=1

        stackArrayMin=stackArrayMin.astype('int16')
        print()

        # 预读取temp_max，存放入stackArrayMax
        cnt=0
        first_flag=True
        for file in reducedFactorFilePathsMax:
            array=readRaster(file)
            vector=array.flatten()
            if first_flag:
                stackArrayMax=vector
                first_flag=False
            else:
                stackArrayMax=np.vstack((stackArrayMax,vector))
            print(cnt,end=' ')
            cnt+=1
        

        stackArrayMax=(stackArrayMax-273)
        stackArrayMax=stackArrayMax.astype('int16')
        stackArrayMin=(stackArrayMin-273)
        stackArrayMin=stackArrayMin.astype('int16')
        print(stackArrayMax.max())
        print(stackArrayMin.max())

        
        flatStart=phenoStartArray.flatten()
        flatEnd=phenoEndArray.flatten()
        
        # 存放结果的数组，先是一个向量
        rasterResultGDD=np.zeros_like(flatStart).astype('int16')
        rasterResultKDD=np.zeros_like(flatStart).astype('int16')

        LENGTH=len(flatStart)
        print(LENGTH)
        print(len(list(flatStart[flatStart!=0])))
        cnt=0
        # 对玉米产量区域中的每个像元进行遍历
        for i in range(LENGTH):
            StartUnix=flatStart[i]
            EndUnix=flatEnd[i]

            # 跳过不满足条件的像元
            if StartUnix==0:
                continue
            if StartUnix>EndUnix:
                print()
                print(StartUnix,EndUnix)
                continue
            
            dateStringStart=unixToDate(StartUnix)
            dateStringEnd=unixToDate(EndUnix)
            
            indexStart=reducedFactorNamesMax.index(dateStringStart+'max_temp.tif')
            indexEnd=reducedFactorNamesMax.index(dateStringEnd+'max_temp.tif')
            # print((dateStringStart,dateStringEnd))
            # print((indexStart,indexEnd))
            
            # 计算参数
            aggregateVectorMin=stackArrayMin[indexStart:indexEnd+1,i].flatten()

            aggregateVectorMax=stackArrayMax[indexStart:indexEnd+1,i].flatten()

        
            
            GDD=0
            KDD=0
            
            for index in range(aggregateVectorMin.shape[0]):
                tempMin=aggregateVectorMin[index]
                tempMax=aggregateVectorMax[index]
                # print('当天温度：')
                # print((tempMin,tempMax))
                
                # GDD
            
                if tempMin>=29 and tempMax>=29:
                    GDD+=21
                if tempMin<=8 and tempMax<=8:
                    GDD+=0
                else:
                    GDD+=(min(tempMax,29)+max(tempMin,8))/2-8
                    if GDD<0:
                        print('***===***')
                        print((tempMin,tempMax))
                

                # KDD
                KDD+=max(tempMax,29)-29

   
            # 计算
            rasterResultGDD[i]=GDD
            rasterResultKDD[i]=KDD

        
        rasterResultGDD=rasterResultGDD.reshape(phenoStartArray.shape[0],phenoStartArray.shape[1])
        rasterResultKDD=rasterResultKDD.reshape(phenoStartArray.shape[0],phenoStartArray.shape[1])
        


        writeRaster(outPath=r'F:\cornDATA\aggResultsTemperature',
                    fileName=str(YEAR)+'_'+ORDER[step]+'_'+ORDER[step+1]+'_GDD.tif',
                    data=rasterResultGDD,
                    reference=phenoStartObject,
                    dtype='int16')
        writeRaster(outPath=r'F:\cornDATA\aggResultsTemperature',
                    fileName=str(YEAR)+'_'+ORDER[step]+'_'+ORDER[step+1]+'_KDD.tif',
                    data=rasterResultKDD,
                    reference=phenoStartObject,
                    dtype='int16')
        print(str(YEAR)+'_'+ORDER[step]+'_'+ORDER[step+1]+'_GDD.tif')
        print(str(YEAR)+'_'+ORDER[step]+'_'+ORDER[step+1]+'_KDD.tif')

        del aggregateVectorMin
        del aggregateVectorMax

    phenoStartObject.close() 
    

    