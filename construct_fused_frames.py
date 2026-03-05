import numpy as np
import os
import glob
import cv2
import datetime
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colorbar as clr
from download import downloadFile

from pymatreader import read_mat
from math import pi
from mpl_toolkits.mplot3d import Axes3D

dirPath = os.getcwd()
filePath = os.path.join(dirPath,'ONC Data')
videoWritePath =  os.path.join(dirPath,'Test Data','Video Data')
sonarRawWritePath =  os.path.join(dirPath,'Test Data','Raw Acoustic Data')
sonarSubWritePath =  os.path.join(dirPath,'Test Data','Processed Acoustic Data')
cameraCode = 'AXISCAMB8A44F04DEEA_'
sonarCode = "DIDSON3000SN374_"
activeCategory = 0

class NumpyArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyArrayEncoder, self).default(obj)

def getFileData(filePath,fileName):
    
    # Read mat file
    fullPath = os.path.join(filePath,fileName)
    mat = read_mat(fullPath)
    Data = mat['Data']
    Config = mat['Config']
    Meta = mat['Meta']
    acousticData = Data['acousticData']

    # Get parameters from file
    didsonParams = { 
        'winStart'          : Config['windowStart'][2],
        'winLength'         : Config['windowLength'][2],
        'beamStart'         : -14*2*pi/360,
        'beamEnd'           : 14*2*pi/360,
        'numFrames'         : len(acousticData[0,0,:]),
        'frameRate'         : Config['frameRate'],
        'numBeams'          : Config['numBeams'],
        'sampleRate'        : Config['sampleRate'],
        'samplesPerBeam'    : Config['samplesPerBeam'][0],
        'frameTime'         : Data['frameTimeStr'],
        'frameNumber'       : Data['frameNumber'],
        'fileName'          : fileName,
        'location'          : Meta['locationName'],
        'deviceName'        : Meta['deviceName'],
        'citation'          : Meta['citation'],
        'year'              : Data['year'],
        'month'             : Data['month'],
        'day'               : Data['day'],
        'hour'              : Data['hour'],
        'minute'            : Data['minute'],
        'second'            : Data['second'],
        'Hsecond'           : Data['hsecond'],
        'filePath'          : filePath}
    
    # Calculated parameters
    didsonParams.update({
        'sampleLength'      : (didsonParams['winLength']/didsonParams['samplesPerBeam']),
        'hourMedian'        : np.zeros((didsonParams['numBeams'],didsonParams['samplesPerBeam']))})
    
    return didsonParams, acousticData

def alreadyProcessed(didsonParams):
    # os.chdir(sonarSubWritePath)
    year = didsonParams['year'][0]
    month = didsonParams['month'][0]
    day = didsonParams['day'][0]
    hour = didsonParams['hour'][0]
    fileSearch = f'{sonarCode}{year}{month:02d}{day:02d}T{hour:02d}'
    fileStr = os.path.join(sonarSubWritePath,f'{fileSearch}*.png')
    files = glob.glob(fileStr)
    if len(files) != 0:
        return True
    else:
        return False


def processData(didsonParams,acousticData):

    orgTitle = 'Original'
    orgCmap = 'Raw Backscatter Amplitude'
    subTitle = 'Background Subtracted'
    subCmap = 'Background Subtracted Backscatter Amplitude'
    rawDidsonData = []
    subDidsonData = []

    # Calculate hourly median
    subtractBgData = np.zeros(np.shape(acousticData))
    hourMedian = np.median(acousticData,axis=(2))
    for frames in np.arange(didsonParams['numFrames']):
            subtractBgData[:,:,frames] = np.subtract(acousticData[:,:,frames],hourMedian)

    # Set range for polar plot
    range = np.linspace(didsonParams['winStart'],didsonParams['winLength']+didsonParams['winStart'],didsonParams['samplesPerBeam'])
    azm = 2*np.linspace(didsonParams['beamStart'],didsonParams['beamEnd'],didsonParams['numBeams'])

    # Define data
    r,th = np.meshgrid(range,azm)

    # Get corresponding video file
    videoFile = getVideoFile(didsonParams)
    if videoFile == None:
        print(f'Video file not found')
        return

    # Loop through all sonar frames
    for frames in np.arange(didsonParams['numFrames']): 

        zOriginal = acousticData[:,:,frames]
        zOriginal[zOriginal<0]=0
        zSubtracted = subtractBgData[:,:,frames]
        zSubtracted[zSubtracted<0]=0

        #if frames > 1000 and frames < 2000 and frames % 5 == 0: 
        if detectMotion(zSubtracted) == True:
            
            validFrame, sonarTimeString, videoFrame = getVideoFrame(frames,videoFile,didsonParams)
            
            # If video frame is valid, plot and write sonar data to png
            if(validFrame == True):
                print(f'Processing frame {frames}')
                sonarRawImgPath = os.path.join(sonarRawWritePath,f'{sonarCode}{sonarTimeString}.png')
                sonarSubImgPath = os.path.join(sonarSubWritePath,f'{sonarCode}{sonarTimeString}_BGS.png')

                plotPolarFigure(1,th,r,zOriginal,orgTitle,orgCmap,didsonParams,frames,sonarRawImgPath)
                plotPolarFigure(1,th,r,zSubtracted,subTitle,subCmap,didsonParams,frames,sonarSubImgPath)
                
                rawDidsonData = zOriginal
                subDidsonData = zSubtracted

                updateJson(rawDidsonData, subDidsonData, videoFrame, sonarTimeString)
                

# Video data is recorded for approx. 5 minutes every hour, starting 10 mins after the hour
# DIDSON data is recorded for approx. 10 minutes every hour, starting 5 mins after the hour
# Expects: Single .mp4 file corresponding to the same hour interval as the SONAR data
# Returns: file name
def getVideoFile(didsonParams):
    
    videoFile = None
    cameraCode = 'AXISCAMB8A44F04DEEA_'
    os.chdir(didsonParams['filePath'])
    year = didsonParams['year'][0]
    month = didsonParams['month'][0]
    day = didsonParams['day'][0]
    hour = didsonParams['hour'][0]
    fileSearch = f'{cameraCode}{year}{month:02d}{day:02d}T{hour:02d}'
    fileStr = f'{fileSearch}*.mp4'
    for file in glob.glob(fileStr):
        videoFile = file
    return videoFile

# Synchronizes video data with sonar data and saves video frame as png
# frame time in format: 'YYYYmmddTHHMMSS.FFFZ'
def getVideoFrame(frames,videoFile,didsonParams):
    
    # Note: video filename timestamp is accurate
    #       didson filename timestamp is not accurate (includes latency of data retrieval)
    #       didson 'frameTime' attribute is always accurate

    # Open video
    video = cv2.VideoCapture(videoFile)
    fps = video.get(cv2.CAP_PROP_FPS)
    totalFrames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    videoFrame = []

    year = didsonParams['year'][0]
    month = didsonParams['month'][0]
    day = didsonParams['day'][0]
    hour = didsonParams['hour'][0]

    # Synchronized instrument time at desired frame
    sonarMinute = didsonParams['minute'][frames]
    sonarSecond = didsonParams['second'][frames]
    sonarMillisecond = didsonParams['Hsecond'][frames]
    # AC change , H second is hundreth of a second to * by 10 to get ms
    sonarTime = datetime.datetime(year,month,day,hour,sonarMinute,sonarSecond,sonarMillisecond*10)
    sonarTimeString = sonarTime.strftime("%Y%m%dT%H%M%S.%f")[:-3]
    sonarTimeString += 'Z'
    
    # Time at start of video (taken from file name)
    vidLatency = datetime.timedelta(seconds=2.5)
    vidMinute = int(videoFile[31:33])
    vidSecond = int(videoFile[33:35])
    vidMicrosecond = int(videoFile[36:39])*1000
    vidTime = datetime.datetime(year,month,day,hour,vidMinute,vidSecond,vidMicrosecond)
    vidTimeCorrected = vidTime - vidLatency
    # Ignore sonar frames that occur before video starts
    if(sonarTime < vidTime):
        validFrame = False
    else:
        # Calculate video frame number using elapsed time
        deltaT = sonarTime - vidTimeCorrected
        vidFrame = deltaT.total_seconds()*fps
        thisVidTime = vidTimeCorrected + deltaT
        vidTimeString = thisVidTime.strftime("%Y%m%dT%H%M%S.%f")[:-3]
        vidTimeString += 'Z'

        video.set(cv2.CAP_PROP_POS_FRAMES,vidFrame)
        ret, videoFrame = video.read()

        # If frame is valid, write to png
        if ret == True:
            #videoFrame = cv2.resize(frame, (400, 300), fx = 0, fy = 0,
            #                    interpolation = cv2.INTER_CUBIC)

            videoImgPath = os.path.join(videoWritePath,f'{cameraCode}{vidTimeString}.jpg')

            cv2.imwrite(videoImgPath,videoFrame)
            #cv2.imshow('frame', frame); cv2.waitKey(5000)

            validFrame = True
        else:
            validFrame = False

    video.release()
    return validFrame, sonarTimeString, videoFrame

# Create polar plots and write as png
def plotPolarFigure(figIdx,th,r,z,title,cbarLabel,didsonParams,frames,sonarFullPath):

    beamLim = [didsonParams['beamStart'],didsonParams['beamEnd']]
    winLim = [didsonParams['winStart'],didsonParams['winStart']+didsonParams['winLength']]

    fig = plt.figure(figIdx)
    ax = Axes3D(fig)
    ax = fig.add_subplot(projection='polar')
    plot = ax.contourf(th,r,z,50)
    ax.grid()
    ax.set_thetamin(np.rad2deg(beamLim[0])-10)
    ax.set_thetamax(np.rad2deg(beamLim[1])+10)
    ax.set_theta_offset(pi/2)
    ax.set_ylim(winLim)
    ax.set_ylabel('Range [m]')
    ax.set_title(title)
    ax.set_rticks(np.linspace(winLim[0],winLim[1],11,dtype=int))
    # textstr =  "\n".join([
    #      f'Location: {location}, Device: {deviceName}',
    #      f'Synchronized Instrument Time: {frameTime}',
    #      f'Frame Index: {frames} of {numFrames}',])
    # props = dict(boxstyle='round', facecolor='white', alpha=0.5)

    # # place a text box in upper left in axes coords
    # ax.text(0.05, 1.4, textstr, transform=ax.transAxes, fontsize=10,
    #         verticalalignment='top', bbox=props)
    # ax.text(0,-0.1,
    #     f'{fileName}',
    #     fontsize = 6,
    #     horizontalalignment='left',
    #     verticalalignment='center',
    #     transform=ax.transAxes)
    #fig.subplots_adjust(top=0.7,bottom=0.1,left=-1.0,right=1.0,hspace=0,wspace=0)
    cax,_ = clr.make_axes(ax,shrink=0.8)
    cbar = fig.colorbar(plot,cax=cax)
    cbar.ax.set_ylabel(cbarLabel,fontsize = 8)
    fig.tight_layout

    # plt.show()
    # cv2.waitKey(0)

    # Write plot to png
    plt.savefig(sonarFullPath)

    # Clumsy fix to resize in pixel values
    image = cv2.imread(sonarFullPath)
    image = cv2.resize(image,(400,300),interpolation = cv2.INTER_CUBIC)
    #cv2.imshow('Image',image)
    #cv2.waitKey(0)
    cv2.imwrite(sonarFullPath,image)

    plt.close("all")

def detectMotion(z):
    thresh = 200*0.3           #Threshold is 30% of expected max
    pixels = (z>thresh).sum()
    maxRows = len(z[0])

    if pixels > 20:
        rowIdx = 0

        # For each radius value
        for rows in z.transpose():
            weight = rowIdx/maxRows
            rowWeight = weight * rows.sum()
            rowIdx += 1 
            if(rowWeight>600):
                objectDetected = True
                break   
            else:   
                objectDetected = False
              
    else:
        objectDetected = False
    
    return objectDetected

def updateJson(rawData,subData,videoFrame,sonarTimeString):
    
    sonarRawJsonPath = os.path.join(sonarRawWritePath,f'{sonarCode}{sonarTimeString}_RawData.json')
    sonarSubJsonPath = os.path.join(sonarSubWritePath,f'{sonarCode}{sonarTimeString}_BGS_RawData.json')
    videoJsonPath = os.path.join(videoWritePath,f'{cameraCode}{sonarTimeString}_RawData.json')

    # If json files don't exist, create empty files
    tempData = {'File Created'  :   datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}
    if os.path.exists(sonarRawJsonPath) == False:
        with open(sonarRawJsonPath,"w") as outfile:
            json.dump(tempData,outfile)

    if os.path.exists(sonarSubJsonPath) == False:
        with open(sonarSubJsonPath,"w") as outfile:
            json.dump(tempData,outfile)

    if os.path.exists(videoJsonPath) == False:
       with open(videoJsonPath,"w") as outfile:
           json.dump(tempData,outfile)

    # Added 'raw_data' key to COCO formatting
    rawDidsonData   = {'images'   : {'raw_data' : rawData}}
    subDidsonData   = {'images'   : {'raw_data' : subData}}
    videoData       = {'images'   : {'raw_data' : np.array(videoFrame)}}

    try:
        with open(sonarRawJsonPath,"w") as outfile:
            json.dump(rawDidsonData,outfile,cls=NumpyArrayEncoder)
        with open(sonarSubJsonPath,"w") as outfile:
            json.dump(subDidsonData,outfile,cls=NumpyArrayEncoder)
        # with open(videoJsonPath,"w") as outfile:
        #     json.dump(videoData,outfile,cls=NumpyArrayEncoder)
    except Exception as e:
        print(e)

def main():

    # Create directories to write images to if they do not exist
    try:
        os.makedirs(os.path.dirname(videoWritePath), exist_ok=True)
        os.makedirs(os.path.dirname(sonarRawWritePath), exist_ok=True)
        os.makedirs(os.path.dirname(sonarSubWritePath), exist_ok=True)
        print("Directories created")  
    except OSError as error:
        print("Error creating directory")

    # Open ONC Data folder & process each .mat file in it
    sonarData = sorted(glob.glob(os.path.join(filePath,'*.mat')))
    
    # Set how many files to process
    processedFiles = 1

    # Keep track of how many files we've seen
    allFiles = 1

    if len(sonarData) == 0:
        print('No files to process')
        processedFiles = 0
    else:
        while processedFiles <= 50 and processedFiles <= len(sonarData):
            for files in sonarData:
                numFiles = len(sonarData)
                print(f'Checking file {allFiles} of {numFiles}')
                didsonParams, acousticData = getFileData(filePath,files)
                    
                # Check for corresponding data in the dataset before processing
                if(alreadyProcessed(didsonParams) == False):

                    print(f'Processing file : {files}')
                    processData(didsonParams,acousticData)
                    processedFiles += 1

                allFiles += 1

    print(f'Finished processing {processedFiles-1} files')
    # files = 'BarkleyCanyon_BarkleyNode_MultibeamNon-rotatingSonar_20220901T110500.708Z_20220901T112000.000Z.mat'
    # didsonParams, acousticData = getFileData(filePath,files)
    # processData(didsonParams,acousticData)

if __name__ == '__main__':
     main()