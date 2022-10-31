# 需要用的函数
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


# 累加NSSR（直接求和）-1003
# 分成前后两段，根据占据天数的比例累加
PHENO_ROOT_PATH=r'D:\文件\华癸项目\test\phenoAllYears0908\outpath_result'
FACTOR_ROOT_PATH=r'F:\cornDATA\SNAPPED\NSSR'

ORDER=('Greenup','MidGreenup','Maturity','Peak','Senescence','MidGreendown','Dormancy')

for YEAR in range(2005,2020):
    
    # YEAR=2005
    print('=============NEW YEAR=============')
    print(YEAR)
    PHENO_FILE_NAMES,PHENO_FILE_PATHS=getFiles(PHENO_ROOT_PATH,'.img',YEAR)
    FACTOR_FILE_NAMES,FACTOR_FILE_PATHS=getFiles(FACTOR_ROOT_PATH,'.tif',YEAR)
    
    print(len(FACTOR_FILE_NAMES))
    # 预读取NSSR，可以一次读入所有的，存放入stackArray
    cnt=0
    first_flag=True
    for file in FACTOR_FILE_PATHS:
        array=readRaster(file)
        vector=array.flatten()
        if first_flag:
            stackArray=vector
            first_flag=False
        else:
            stackArray=np.vstack((stackArray,vector))
        print(cnt,end=' ')
        cnt+=1

    stackArray=stackArray.astype('int64')
    # 接下半部分

    # 接上半部分
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

        # dic={start_unix_date:filename}
        unix_date_dic={dateToUnix(string[:8]):string for string in FACTOR_FILE_NAMES}

        # dic={start_unix_date:row number in FACTOR_FILE_NAMES and stackArray}
        unix_row_dic={unix:FACTOR_FILE_NAMES.index(unix_date_dic[unix]) for unix in unix_date_dic.keys()}

        flatStart=phenoStartArray.flatten()
        flatEnd=phenoEndArray.flatten()

        # 存放结果的数组，先是一个向量
        rasterResult=np.zeros_like(flatStart).astype('int64')

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
    #         print('--------------------------')
    #         print(dateStringStart,dateStringEnd)
    #         print(StartUnix,EndUnix)

            full_part=[unix for unix in unix_date_dic.keys() if StartUnix<=unix and unix+7<=EndUnix]


            # 存在中间完整部分的情况
            if full_part!=[]:   
    #             print(full_part)
                start_part=full_part[0]-8
                start_days=full_part[0]-StartUnix
    #             print((start_part,start_days))

                end_part=full_part[-1]+8
                end_days=EndUnix-end_part
    #             print((start_part,start_days,full_part,end_part,end_days))

                start_part_data=stackArray[unix_row_dic[start_part],i]
                full_part_number=[unix_row_dic[unix] for unix in full_part]

                full_part_data=stackArray[full_part_number[0]:full_part_number[-1]+1,i]

                end_part_data=stackArray[unix_row_dic[end_part],i]

    #             print(start_part_data)
    #             print(full_part_data)
    #             print(end_part_data)

                agg_full_part=full_part_data.sum()

                agg_start_part=start_part_data*(start_days/8)

                agg_end_part=end_part_data*(end_days/8)

                aggValue=agg_full_part+agg_start_part+agg_end_part

                rasterResult[i]=aggValue

                if rasterResult[i]<0:
                    print(rasterResult[i])

    #             print(cnt,end=' ')
    #             cnt+=1
    #             print(rasterResult[i])

            # 没有中间完整部分的情况
            else:
    #             print('--------------------')
    #             print((StartUnix,EndUnix))
    #             print(dateStringStart,dateStringEnd)
    #             print(full_part)
    #             print([unix for unix in unix_date_dic.keys() if StartUnix<=unix and unix<=EndUnix])

                end_part=[unix for unix in unix_date_dic.keys() if StartUnix<=unix and unix<=EndUnix]

                # 第三种情况：全部在一个周期内
                if end_part!=[]:

                    end_part=end_part[0]

                    start_part=end_part-8


                    start_days=end_part-StartUnix
                    end_days=EndUnix-end_part

                    start_part_days=stackArray[unix_row_dic[start_part],i]
                    end_part_days=stackArray[unix_row_dic[end_part],i]

                    agg_start_part=start_part_data*(start_days/8)
                    agg_end_part=end_part_data*(end_days/8)

                    aggValue=agg_start_part+agg_end_part
                    rasterResult[i]=aggValue

                    if rasterResult[i]<0:
                        print(rasterResult[i])

    #                 print(cnt,end=' ')
    #                 cnt+=1

                else:
    #                 print('--------------------')
                    start_part=[unix for unix in unix_date_dic.keys() if unix<=StartUnix and EndUnix<=unix+8][0]
    #                 print(start_part)

                    start_part_days=(EndUnix-StartUnix)

                    aggValue=stackArray[unix_row_dic[start_part],i]*(start_part_days/8)

                    rasterResult[i]=aggValue

                    if rasterResult[i]<0:
                        print(rasterResult[i])
    #                 print(cnt,end=' ')
    #                 cnt+=1



        rasterResult=rasterResult.reshape(phenoStartArray.shape[0],phenoStartArray.shape[1])
    #     print(np.max(rasterResult))
        rasterResult=rasterResult
        writeRaster(outPath=r'F:\cornDATA\aggResult',
                    fileName=str(YEAR)+'_'+ORDER[step]+'_'+ORDER[step+1]+'_NSSR.tif',
                    data=rasterResult,
                    reference=phenoStartObject,
                    dtype='float32')
        break

    phenoStartObject.close() 
    break
    