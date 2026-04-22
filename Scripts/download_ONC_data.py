import requests
import json
import os
import sys
import time
from contextlib import closing
import errno
import math

url = 'https://data.oceannetworks.ca/api/dataProductDelivery'
<<<<<<< HEAD
token = '0d6776bd-e174-4817-931b-a7bdd5de2514'      # Alanna Token                            
=======
token = 'aaf56230-d4da-4c5a-9023-4358410f97bb'                                  
>>>>>>> 205f635b9fc7bbc1c956c853cd4da77cb3cbf735
requestParameters = {'method':'request',
            'token':token,                              # replace YOUR_TOKEN_HERE with your personal token obtained from the 'Web Services API' tab at https://data.oceannetworks.ca/Profile when logged in.
            }
downloadFolder = os.path.join("Startle Dataset","Acoustic Data")                                      # The folder that file(s) will be saved to

def downloadFile(type,dateFrom,dateTo):
    setRequestParameters(type,dateFrom,dateTo)
    requestId = requestDataProduct(requestParameters)
<<<<<<< HEAD
    
    # AC add
    if requestId == None:
        print('User aborted download')
        return
=======
>>>>>>> 205f635b9fc7bbc1c956c853cd4da77cb3cbf735

    for runId in runDataProduct(requestId):
        indx = 1    #Index Number of file to download.
                        #Because the number of files are not known until the process is complete,
                        #we try the next index until we get back a 404 status indicating that we are beyond the end of the array
        while True:
            dict = downloadDataProductIndex(runId,indx,downloadFolder)
            if dict:
                indx+=1
            else:
                break

def setRequestParameters(type,dateFrom,dateTo):
    if type == 'SONAR':
        requestParameters.update({'locationCode':'BACND',    # Barkley Canyon / Axis (POD 1)
            'deviceCategoryCode':'MBPROFILESONAR',      # MBPROFILESONAR or VIDEOCAM
            'dataProductCode':'SMSONAR',                # Time Series Scalar Data
            'extension':'mat',                          # Mat file
            'dateFrom': dateFrom,                       # The datetime of the first data point (From Date)
            'dateTo': dateTo,                           # The datetime of the last data point (To Date)
            })
    elif type == 'VIDEOCAM':
        requestParameters.update({'locationCode':'BACND',    # Barkley Canyon / Axis (POD 1)
            'deviceCategoryCode':'VIDEOCAM',            # 
            'dataProductCode':'MP4V',                   # Time Series Scalar Data
            'extension':'mp4',                          # Mp4 video file
            'dateFrom': dateFrom,                        # The datetime of the first data point (From Date)
            'dateTo': dateTo,                            # The datetime of the last data point (To Date)
            })    

  
def requestDataProduct(parameters):
 
    response = requests.get(url,params=parameters)
    requestId = None
    if (response.ok and len(str(response.content,'utf-8'))>0):
        requestInfo = json.loads(str(response.content,'utf-8')) # convert the json response to an object
        requestId = requestInfo['dpRequestId']
        print('Request Id: {}'.format(requestId))      # Print the Request Id
        if ('numFiles' in requestInfo.keys()):
            print('File Count: {}'.format(requestInfo['numFiles']))     # Print the Estimated File Size
        if ('fileSize' in requestInfo.keys()):
            print('File Size: {}'.format(requestInfo['fileSize']))      # Print the Estimated File Size
<<<<<<< HEAD
            
            # AC add
            print('Would you still like to proceed with download?')
            answer = input("Y/N: ")
            if answer == 'N':
                return None
=======
>>>>>>> 205f635b9fc7bbc1c956c853cd4da77cb3cbf735
        if 'downloadTimes' in requestInfo.keys():
            print('Estimated download time:')
            for e in sorted(requestInfo['downloadTimes'].items(),key=lambda t: t[1]):
                print('  {} - {} sec'.format(e[0],'{:0.2f}'.format(e[1])))
 
        if 'estimatedFileSize' in requestInfo.keys():
            print('Estimated File Size: {}'.format(requestInfo['estimatedFileSize']))
        if 'estimatedProcessingTime' in requestInfo.keys():
            print('Estimated Processing Time: {}'.format(requestInfo['estimatedProcessingTime']))
    else:
        if(response.status_code == 400):
            error = json.loads(str(response.content,'utf-8'))
            print(error) # json response contains a list of errors, with an errorMessage and parameter
        else:
            print ('Error {} - {}'.format(response.status_code,response.reason))
 
    return requestId
 
def runDataProduct(requestId):
    parameters = {'method':'run',
                'token':token,
                'dpRequestId':requestId}
 
    response = requests.get(url,params=parameters)
    runIds = []
 
    if (response.ok):
        r= json.loads(str(response.content,'utf-8')) # convert the json response to an object
        runIds = [run['dpRunId'] for run in r]
  
    else:
        if(response.status_code == 400):
            error = json.loads(str(response.content,'utf-8'))
            print(error) # json response contains a list of errors, with an errorMessage and parameter
        else:
            print ('Error {} - {}'.format(response.status_code,response.reason))
 
    return runIds
 
  
def downloadDataProductIndex(runId,                     # The ID of the run process to download the files for. RunIds are returned from the dataProductDelivery run method
                             indx=1,                    # The index of the file to be downloaded. Data files have an index of 1 or higher. The Metadata has an index of 'meta'
                             outPath='c:/temp',
                             fileCount=1,               # The actual or estimated file count, which is returned from the dataProductDelivery request method
                             estimatedProcessingTime=1, # The estimated processing time in seconds, which is used to determine how often to poll the web service. The estimated processing time is returned from the dataProductDelivery request method
                             maxRetries=100):           # Determines the maximum number of times the process will poll the service before it times out. The purpose of this property is to prevent hung processes on the Task server to hang this process.
 
  
    parameters = {'method':'download',
                'token':token,
                'dpRunId':runId,
                'index':indx}
    defaultSleepTime = 2
    downloadResult = {}
    tryCount = 0
    lastMessage = None
    global downloadedFile
 
    if (estimatedProcessingTime > 1):
        sleepTime = estimatedProcessingTime * 0.5
    else:
        sleepTime = defaultSleepTime
 
    while True:
        tryCount+=1
        if tryCount >= maxRetries:
            msg = 'Maximum number of retries ({}) exceeded'.format(maxRetries)
            print(msg)
            break
        with closing(requests.get(url,params=parameters,stream=True)) as streamResponse:
            if (streamResponse.ok): #Indicates that the request was successful and did not fail. The status code indicates if the stream contains a file (200) or
                if streamResponse.status_code == 200: #OK
                    tryCount=0
                    if 'Content-Disposition' in streamResponse.headers.keys():
                        content = streamResponse.headers['Content-Disposition']
                        filename = content.split('filename=')[1]
                    else:
                        print('Error: Invalid Header')
                        streamResponse.close()
                        break
                    if 'Content-Length' in streamResponse.headers.keys():
                        size = streamResponse.headers['Content-Length']
                    else:
                        size = 0
                    filePath = '{}/{}'.format(outPath,filename)
                    try:
                        if (indx==1):
                            print('')
                        if (not os.path.isfile(filePath)):
                            #Create the directory structure if it doesn't already exist
                            try:
                                os.makedirs(outPath)
                            except OSError as exc:
                                if exc.errno == errno.EEXIST and os.path.isdir(outPath):
                                    pass
                                else:
                                    raise
                            if fileCount == 0:
                                print ("  Downloading {} '{}' ({})".format(indx,filename,convertSize(float(size))))
                            else:
                                print ("  Downloading {}/{} '{}' ({})".format(indx,fileCount,filename,convertSize(float(size))))
                            with open(filePath,'wb') as handle:
                                try:
                                    for block in streamResponse.iter_content(1024):
                                        handle.write(block)
                                except KeyboardInterrupt:
                                    print('Process interupted: Deleting {}'.format(filePath))
                                    handle.close()
                                    streamResponse.close()
                                    os.remove(filePath)
                                    sys.exit(-1)
                        else:
                            if fileCount == 0:
                                print ("  Skipping {} '{}': File Already Exists".format(indx,filename))
                            else:
                                print ("  Skipping {}/{} '{}': File Already Exists".format(indx,fileCount,filename))
                    except:
                        msg = 'Error streaming response.'
                        print(msg)
                    downloadResult['url'] = url
                    streamResponse.close()
                    break
 
                elif streamResponse.status_code == 202: #Accepted - Result is not complete -> Retry
                    payload = json.loads(str(streamResponse.content,'utf-8'))
                    if len(payload) >= 1:
                        msg = payload['message']
                        if (msg != lastMessage): #display a new message if it has changed
                            print('\n  {}'.format(msg),end='')
                            sys.stdout.flush()
                            lastMessage=msg
                            tryCount=0
                        else: #Add a dot to the end of the message to indicate that it is still receiving the same message
                            print('.',end='')
                            sys.stdout.flush()
                    else:
                        print('Retrying...')
 
                elif streamResponse.status_code == 204: #No Content - No Data found
                    responseStr = str(streamResponse.content,'utf-8')
                    if not(responseStr == ''):
                        payload = json.loads(responseStr)
                        msg = '  {} [{}]'.format(payload['message'],streamResponse.status_code)
                    else:
                        msg = 'No Data found'
                    print('\n{}'.format(msg))
                    streamResponse.close()
                    break
 
                else:
                    msg = 'HTTP Status: {}'.format(streamResponse.status_code)
                    print(msg)
 
            elif streamResponse.status_code == 400: #Error occurred
                print('  HTTP Status: {}'.format(streamResponse.status_code))
                payload = json.loads(str(streamResponse.content,'utf-8'))
                if len(payload) >= 1:
                    if ('errors' in payload):
                        for e in payload['errors']:
                            msg = e['errorMessage']
                            printErrorMesasge(streamResponse,parameters)
                    elif ('message' in payload):
                        msg = '  {} [{}]'.format(payload['message'],streamResponse.status_code)
                        print('\n{}'.format(msg))
                    else:
                        print(msg)
                else:
                    msg = 'Error occurred processing data product request'
                    print(msg)
                streamResponse.close()
                break
            elif streamResponse.status_code == 404:  #Not Found - Beyond End of Index - Index # > Results Count
                streamResponse.close()
                downloadResult = None
                break
            elif streamResponse.status_code == 410: #Gone - file does not exist on the FTP server. It may not have been transfered to the FTP server  yet
                payload = json.loads(str(streamResponse.content,'utf-8'))
                if len(payload) >= 1:
                    msg = payload['message']
                    if (msg != lastMessage):
                        print('\n  Waiting... {}'.format(msg),end='')
                        sys.stdout.flush()
                        lastMessage=msg
                        tryCount=0
                    else:
                        print('.',end='',sep='')
                        sys.stdout.flush()
                else:
                    print('\nRunning... Writing File.')
            elif streamResponse.status_code == 500: #Internal Server Error occurred
                msg = printErrorMesasge(streamResponse,parameters)
                print('  URL: {}'.format(streamResponse.url))
                streamResponse.close()
                break
            else:
                try:
                    payload = json.loads(str(streamResponse.content,'utf-8'))
                    if len(payload) >= 1:
                        if ('errors' in payload):
                            for e in payload['errors']:
                                msg = e['errorMessage']
                                printErrorMesasge(streamResponse,parameters)
                        elif ('message' in payload):
                            msg = payload['message']
                            print('\n  {} [{}]'.format(msg,streamResponse.status_code))
                    streamResponse.close()
                    break
                except:
                    printErrorMesasge(streamResponse,parameters)
                    print('{} Retrying...'.format(msg))
                    streamResponse.close()
                    break
 
        streamResponse.close()
 
        if (tryCount <= 5) and (sleepTime > defaultSleepTime):
            sleepTime = sleepTime * 0.5
        time.sleep(sleepTime)
 
    return downloadResult
 
  
def convertSize(size):
 
   if (size == 0):
       return '0 KB'
 
   size_name = ("B","KB","MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size,1024)))
   p = math.pow(1024,i)
   s = round(size/p,2)
 
   return '%s %s' % (s,size_name[i])
 
 
def printErrorMesasge(response,
                      parameters,
                      showUrl=False,
                      showValue=False):
 
    if(response.status_code == 400):
        if showUrl:print('Error Executing: {}'.format(response.url))
 
        payload = json.loads(str(response.content,'utf-8'))
 
        if len(payload) >= 1:
            for e in payload['errors']:
                msg = e['errorMessage']
                parm = e['parameter']
                matching = [p for p in parm.split(',') if p in parameters.keys()]
                if len(matching) >=1:
                    for p in matching:print("  '{}' for {} - value: '{}'".format(msg,p,parameters[p]))
                else:
                    print("  '{}' for {}".format(msg,parm))
 
                if showValue:
                    for p in parm.split(','):
                        parmValue = parameters[p]
                        print("  {} for {} - value: '{}'".format(msg,p,parmValue))
 
            return payload
    else:
        msg = 'Error {} - {}'.format(response.status_code,response.reason)
        print (msg)
        return msg
    
def main():
    
<<<<<<< HEAD
    # previous value 
    # datefrom = '2022-08-20T09:00:00.000Z'
    # dateto = '2022-08-22T10:00:00.000Z'

    # datefrom = '2022-08-28T09:00:00.000Z'
    # ateto = '2022-08-29T10:00:00.000Z'

    #    datefrom = '2022-09-05T09:00:00.000Z'
    # dateto = '2022-09-06T10:00:00.000Z'py

    # datefrom = '2022-10-05T09:00:00.000Z'
    # dateto = '2022-10-06T10:00:00.000Z'

    #    datefrom = '2022-10-06T09:00:00.000Z'
    # dateto = '2022-10-07T10:00:00.000Z'

    #datefrom = '2022-07-08T09:00:00.000Z'
    #dateto = '2022-07-11T10:00:00.000Z'

    datefrom = '2022-07-20T09:00:00.000Z'
    dateto = '2022-07-24T10:00:00.000Z'

    downloadFile('SONAR',datefrom,dateto)
    downloadFile('VIDEOCAM',datefrom,dateto)
=======
    datefrom = '2022-10-12T09:00:00.000Z'
    dateto = '2022-10-12T10:00:00.000Z'

    downloadFile('SONAR',datefrom,dateto)
    #downloadFile('VIDEOCAM',datefrom,dateto)
>>>>>>> 205f635b9fc7bbc1c956c853cd4da77cb3cbf735

if __name__ == '__main__':
     main()