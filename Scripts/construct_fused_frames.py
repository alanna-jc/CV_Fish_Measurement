"""
Created by Adriel Ngo, edited by Alanna Cunha 2025/11/17

Sonar and Video Data Processing Pipeline

This script processes DIDSON sonar data and corresponding video recordings to create output png files 
of sonar plot, corresponding video png, and COCO-like JSON

Workflow of the code:
1. Extract data from .mat sonar files.
2. Check if the file has already been processed.
3. Find the corresponding video file recorded for the same hourly interval.
4. Process sonar data:
   - Perform background subtraction.
   - Detect motion in each sonar frame.
   - Synchronize valid sonar frames with video frames.
   - Generate polar plots for raw and background-subtracted sonar data.
   - Save frames and data to PNG images and JSON files.
5. Repeat for multiple sonar files, up to a specified limit (default: 50 files).

Key Features:
- Polar plotting of sonar frames with configurable beam and window limits.
- Motion detection using pixel intensity thresholds and weighted row sums.
- Synchronization of sonar frames with video frames using timestamps.
- Automatic creation of required directories and JSON files.
- Handling of missing or incomplete video data.

Directory Structure:
- 'Startle Dataset/Acoustic Data': source .mat files
- 'Test Data/Video Data': saved video frames
- 'Test Data/Raw Acoustic Data': saved raw sonar images
- 'Test Data/Processed Acoustic Data': saved background-subtracted sonar images
- 'Test Data', 'Combined Data': combined image

Resources:
 - Didson data wiki: https://wiki.oceannetworks.ca/spaces/DP/pages/49447779/119

Usage:
Run the script directly. The main() function will scan the 'ONC Data' folder, process 
unprocessed files, and output processed images and JSON files. 
"""

import numpy as np
import os
import glob
import cv2
import datetime
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colorbar as clr
from download_ONC_data import downloadFile

from pymatreader import read_mat
from math import pi
from mpl_toolkits.mplot3d import Axes3D

dirPath = os.getcwd()
# AC change this name
filePath = os.path.join(dirPath,'Startle Dataset','Acoustic Data')
videoWritePath =  os.path.join(dirPath,'Test Data','Video Data')
sonarRawWritePath =  os.path.join(dirPath,'Test Data','Raw Acoustic Data')
sonarSubWritePath =  os.path.join(dirPath,'Test Data','Processed Acoustic Data')
combinedWritePath = os.path.join(dirPath, 'Test Data', 'Combined Data')
cameraCode = 'AXISCAMB8A44F04DEEA_'
sonarCode = "DIDSON3000SN374_"
activeCategory = 0

# Helper
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

# Step 1
def getFileData(filePath,fileName):
    """
    Extract the data from the .mat file. You can look at the entries directly using matlab
    You can look at what each entry means on ONC website

    Parameters:
        didsonParams: sonar paramaters extracted from sonar .mat file

    Returns:
        didsonParams: the parameters
        acousticData: the actual data

    """
    # Read mat file
    fullPath = os.path.join(filePath,fileName)
    mat = read_mat(fullPath)
    Data = mat['Data']
    Config = mat['Config']
    Meta = mat['Meta']
    acousticData = Data['acousticData']

    SonarFileBaseName = os.path.basename(fileName)
    position = SonarFileBaseName.find("T")
    #print(SonarFileBaseName[(position+1):(position+3)])

    # Extract parameters
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
        #'hour'              : Data['hour'], # this was shown to be wrong in the files
        'minute'            : Data['minute'],
        'second'            : Data['second'],
        'Hsecond'           : Data['hsecond'],
        'filePath'          : filePath}
    
    # Calculated parameters
    didsonParams.update({
        'sampleLength'      : (didsonParams['winLength']/didsonParams['samplesPerBeam']),
        'hourMedian'        : np.zeros((didsonParams['numBeams'],didsonParams['samplesPerBeam'])),
        'hour'              : int(SonarFileBaseName[(position+1):(position+3)])})
    
    return didsonParams, acousticData

# Step 2
def alreadyProcessed(didsonParams):
    """
    Checks if processed file already exists

    Parameters:
        didsonParams: sonar paramaters extracted from sonar .mat file

    Returns:
        Bool: True if already processed, False otherwise
    
    """
    # os.chdir(sonarSubWritePath)
    year = didsonParams['year'][0]
    month = didsonParams['month'][0]
    day = didsonParams['day'][0]
    hour = didsonParams['hour'] # not an array as pulled from file name
    
    fileSearch = f'{sonarCode}{year}{month:02d}{day:02d}T{hour:02d}'
    
    fileStr = os.path.join(sonarSubWritePath,f'{fileSearch}*.png')
    files = glob.glob(fileStr)
    if len(files) != 0:
        return True
    else:
        return False

# Step 3            
def getVideoFile(didsonParams):
    """
    Gets video file corresponding to sonar data file
    
    Video data is recorded for approx. 5 minutes every hour, starting 10 mins after the hour
    dIDSON data is recorded for approx. 10 minutes every hour, starting 5 mins after the hour

    Parameters:
        didsonParams: sonar paramaters extracted from sonar .mat file

    Returns:
        videoFile: corresponding video file path string. Returns none if none returned from search

    """
    videoFile = None
    
    # Fetching needed params
    basePath = (didsonParams['filePath'])
    #print(basePath)
    year = didsonParams['year'][0]
    month = didsonParams['month'][0]
    day = didsonParams['day'][0]
    hour = didsonParams['hour'] # not an array as pulled from file name
    #print(f"hour {hour}")
    
    fileSearchPath = f'{cameraCode}{year}{month:02d}{day:02d}T{hour:02d}*.mp4'
    #print(f'File search path {fileSearchPath}')

    for file in glob.glob(os.path.join(basePath, fileSearchPath)):
        #print(f'file {file}')
        videoFile = file
        
    return videoFile

# Step 4
def processData(didsonParams, acousticData, videoFile):
    """
    Created background subtration. Detects motion. If motion detected processes sonar and video at that time.

    Parameters:
        didsonParams: sonar paramaters extracted from sonar .mat file
        acousticData: the sonar data
        videoFile: string to video file location

    Returns:
        None

    """
    orgTitle = 'Original'
    orgCmap = 'Raw Backscatter Amplitude'
    subTitle = 'Background Subtracted'
    subCmap = 'Background Subtracted Backscatter Amplitude'
    rawDidsonData = []
    subDidsonData = []

    # Background subtration prep: Calculate hourly median and create background subtractor
    subtractBgData = np.zeros(np.shape(acousticData))
    hourMedian = np.median(acousticData,axis=(2))
    for frame in np.arange(didsonParams['numFrames']):
            subtractBgData[:,:,frame] = np.subtract(acousticData[:,:,frame],hourMedian)

    # Set range for polar plot
    range = np.linspace(didsonParams['winStart'],didsonParams['winLength']+didsonParams['winStart'],didsonParams['samplesPerBeam'])
    azm = 2*np.linspace(didsonParams['beamStart'],didsonParams['beamEnd'],didsonParams['numBeams'])

    # Define data
    r,th = np.meshgrid(range,azm)

    # Frames processed count
    processedFrames = 0

    # Loop through all sonar frames
    for frame in np.arange(didsonParams['numFrames']): 

        zOriginal = acousticData[:,:,frame]
        zOriginal[zOriginal<0]=0
        zSubtracted = subtractBgData[:,:,frame]
        zSubtracted[zSubtracted<0]=0

        #if frames > 1000 and frames < 2000 and frames % 5 == 0: 
        if True:
        #if detectMotion(zSubtracted):
            
            validFrame, sonarTimeString, videoFrame = getVideoFrame(frame,videoFile,didsonParams)
            
            # If video frame is valid, plot and write sonar data to png
            if(validFrame == True):

                processedFrames += 1
                print(f'Processing valid frame {processedFrames}')

                shortSonarTimeString = sonarTimeString[0:11]

                sonarRawImgPath = os.path.join(sonarRawWritePath,f'{shortSonarTimeString}.Frame_{processedFrames}.png')
                sonarSubImgPath = os.path.join(sonarSubWritePath,f'{sonarCode}{sonarTimeString}_BGS.png')
                combinedPath = os.path.join(combinedWritePath, f'{shortSonarTimeString}.Frame_{processedFrames}.png')

                sonarBeamToImage(zOriginal, r, th, didsonParams, sonarRawImgPath)
                sonarBeamToImage(zSubtracted, r, th, didsonParams, sonarSubImgPath)
                
                #plotPolarFigure(1,th,r,zOriginal,orgTitle,orgCmap,didsonParams,frame,sonarRawImgPath)
                #plotPolarFigure(1,th,r,zSubtracted,subTitle,subCmap,didsonParams,frame,sonarSubImgPath)
                
                rawDidsonData = zOriginal
                subDidsonData = zSubtracted

                updateJson(rawDidsonData, subDidsonData, videoFrame, sonarTimeString)
                
                success = combineSonarAndVideo(sonarRawImgPath, sonarSubImgPath, videoFrame, combinedPath)
                print(f'Combined sonar data made = {success}')
                
    return processedFrames            
    

# Step 4 Helper 1
def detectMotion(z):
    """
    Detects whether an object is present in a 2D data array.

    The function counts pixels above a threshold (30% of expected max) and evaluates
    weighted row sums to determine if an object is present. If enough pixels exceed 
    the threshold and any row's weighted sum passes the limit, the function returns True;
    otherwise, it returns False.

    Returns:
        bool: True if an object is detected, False otherwise.
    """
    thresh = 200*0.3       #Threshold is 30% of expected max
    pixels = (z>thresh).sum()
    maxRows = len(z[0])

    if pixels > 17:
        rowIdx = 0

        # For each radius value
        for rows in z.transpose():
            weight = rowIdx/maxRows
            rowWeight = weight * rows.sum()
            rowIdx += 1 
            # making this not sensitive enough will result in fish frames being missed especially if fish is diagonal
            if(rowWeight>350): 
                print( "Motion Detected")
                objectDetected = True
                break   
            else:   
                objectDetected = False
              
    else:
        objectDetected = False
    
    return objectDetected

# Step 4 Helper 2
def getVideoFrame(frame,videoFile,didsonParams):
    """
    Synchronizes video data with sonar data and saves video frame as png
    frame time in format: 'YYYYmmddTHHMMSS.FFFZ'
    
    NOTE 1:
    - Video data is recorded for approx. 5 minutes every hour, starting 10 mins after the hour
    - DIDSON data is recorded for approx. 10 minutes every hour, starting 5 mins after the hour

    NOTE 2:
    - video filename timestamp IS accurate
    - didson filename timestamp is NOT accurate (includes latency of data retrieval)
    - didson 'frameTime' attribute is ALWAYS accurate

    Parameters:
        frame: frame to get
        videoFile: string of video file location
        didsonParams: sonar paramaters extracted from sonar .mat file

    Returns:
        validFrame: Is there a frame here
        sonarTimeString: what time we at
        videoFrame: the video frame returned 
    """

    # Open video
    video = cv2.VideoCapture(videoFile)
    fps = video.get(cv2.CAP_PROP_FPS)
    totalFrames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    videoFrame = []

    year = didsonParams['year'][0]
    month = didsonParams['month'][0]
    day = didsonParams['day'][0]
    hour = didsonParams['hour'] # not an array as pulled from file name

    # Synchronized instrument time at desired frame
    sonarMinute = didsonParams['minute'][frame]
    sonarSecond = didsonParams['second'][frame]
    # not a milli but i think still correct outcome
    sonarMillisecond = didsonParams['Hsecond'][frame] 
    
    sonarTime = datetime.datetime(year,month,day,hour,sonarMinute,sonarSecond,sonarMillisecond)
    sonarTimeString = sonarTime.strftime("%Y%m%dT%H%M%S.%f")[:-3]
    sonarTimeString += 'Z'
    
    # Time at start of video (taken from file name)
    videoFileBaseName = os.path.basename(videoFile)
    position = videoFileBaseName.find("T")
    
    # ONC website says latency would be ~2.5 seconds
    # 32 seconds of latency was determined experimentally
    vidLatency = datetime.timedelta(seconds=32) 
    vidMinute = int(videoFileBaseName[(position+3):(position+5)])
    vidSecond = int(videoFileBaseName[(position+5):(position+7)])
    vidMicrosecond = int(videoFileBaseName[(position+8):(position+10)])*1000
    vidTime = datetime.datetime(year,month,day,hour,vidMinute,vidSecond,vidMicrosecond)
    
    """ Checking Print statement """
    print(f'Video file name: {videoFileBaseName}. Video time: {vidTime}. Sonar time: {sonarTime}')
    
    # due to arrival time being different (network latency stuff
    vidTimeCorrected = vidTime - vidLatency
    
    # Ignore sonar frames that occur before video starts
    if(sonarTime < vidTimeCorrected):
        print("Sonar frame occured before video starts")
        validFrame = False
    else:
        # Calculate video frame number using elapsed time
        deltaT = sonarTime - vidTimeCorrected
        #print(f'Delta T = {deltaT} = sonartTime {sonarTime} - vidTimeCorrected {vidTimeCorrected}')

        vidFrame = deltaT.total_seconds()*fps

        #This is the line that actually pulls the frame 
        #print(f"vidFrame: {vidFrame}")
        video.set(cv2.CAP_PROP_POS_FRAMES,vidFrame)
        ret, videoFrame = video.read()

        # If frame is valid, write to png
        if ret == True:

            thisVidTime = vidTime + deltaT
            vidTimeString = thisVidTime.strftime("%Y%m%dT%H%M%S.%f")[:-3]
            vidTimeString += 'Z'
            #videoFrame = cv2.resize(frame, (400, 300), fx = 0, fy = 0,
            #                    interpolation = cv2.INTER_CUBIC)

            videoImgPath = os.path.join(videoWritePath,f'{cameraCode}{vidTimeString}.jpg')

            cv2.imwrite(videoImgPath,videoFrame)
            #cv2.imshow('frame', frame); cv2.waitKey(5000)

            validFrame = True
        else:
            validFrame = False
            print("Video Finished")

    video.release()
    
    return validFrame, sonarTimeString, videoFrame


# Step 4 Helper 3
# AC to add description
def sonarBeamToImage(z, r, th, didsonParams, sonarFullPath):
    """

    """
    
    # matlab code from ONC: 
    # rangeToBinStart = linspace(Config.windowStart(2), Config.windowLength(2) + Config.windowStart(2), size(Data.acousticData,2));
    rangeToBinStart = np.linspace(didsonParams['winStart'], didsonParams['winLength'] + didsonParams['winStart'], z.shape[1])    
                                    
    # matlab code from ONC:                         
    # theta = ANGLEAMP*linspace(-14*(2*pi)/360,14*2*pi/360,size(Data.acousticData,1));
    # ignore angle amp .we working with REAL numbers hear      
    theta = np.linspace(-14*(2*np.pi)/360, 14*2*np.pi/360, z.shape[0])

    # meshgrid: r along first axis, theta along second
    r, th = np.meshgrid(rangeToBinStart, theta, indexing='ij')  # use indexing='ij' to match z

    fig, ax = plt.subplots(
                            figsize=(4, 3),              # 4×3 inches
                            dpi=100,                     # 100 dpi → 400×300 pixels
                            subplot_kw={'projection': 'polar'}
                        )                   

    # black background
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black') 


    ax.set_theta_zero_location('N')
    plot = ax.contourf(th.T, r.T, z, 50)   
    ax.axis('off')
    
    # makes it so that full circle is not drawn
    ax.set_thetamin(-14)
    ax.set_thetamax(14)
    
    fig.tight_layout(pad=0)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_aspect('equal')
    
    fig.savefig(sonarFullPath, pad_inches=0)
    plt.close("all")

    return

# Step 4 Helper 4
def updateJson(rawData,subData,videoFrame,sonarTimeString):
    """
    Updates or creates JSON files for sonar and video data in COCO-like format.

    The function ensures that JSON files exist for raw sonar data, background-subtracted 
    sonar data, and video frames. If a file does not exist, it is initialized with a 
    creation timestamp. The function then writes the provided data under the key 
    'images' -> 'raw_data', using a custom encoder to handle NumPy arrays.

    Parameters:
        rawData (array-like): Raw sonar data to save in JSON.
        subData (array-like): Background-subtracted sonar data to save in JSON.
        videoFrame (array-like): Corresponding video frame data.
        sonarTimeString (str): Timestamp string used to name the JSON files.

    Returns:
        None
    """
    
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

def combineSonarAndVideo(rawPath, subPath, videoFrame, combinedPath):
    """
    Combines two saved sonar images with a video frame side by side and saves the combined image.

    Parameters:
        rawPath (str): path to raw sonar image
        subPath (str): path to background-subtracted sonar image
        videoFrame (np.array): video frame (BGR)
        combinedPath (str): path to save the combined image
        targetHeight (int): height to resize all images to (maintains aspect ratio)
    """

    # Load sonar images
    rawImg = cv2.imread(rawPath)
    subImg = cv2.imread(subPath)

    # Resize video frame to be same height as sonar images
    videoFrame = cv2.resize(videoFrame, (533, 300), interpolation=cv2.INTER_AREA)

    # Concatenate images horizontally
    combined = np.hstack([rawImg, subImg, videoFrame])

    # CV2 hates you and me and outputs things as BGR and its hard to tell
    # imwrite will expect BGR inputs and will flip it to rgb when it saves it
    # Given this we will have to convert nothing to RGB
    success = cv2.imwrite(combinedPath, combined)
    return success



def main():

    # Create directories to write images to if they do not exist
    try:
        os.makedirs(os.path.dirname(videoWritePath), exist_ok=True)
        os.makedirs(os.path.dirname(sonarRawWritePath), exist_ok=True)
        os.makedirs(os.path.dirname(sonarSubWritePath), exist_ok=True)
        print("Directories created")  
    except OSError as error:
        print("Error creating directory")

    # Get that Sonar data
    sonarData = sorted(glob.glob(os.path.join(filePath,'*.mat')))

    # Total files in sonar data
    numFiles = len(sonarData)
    # Current File tracker
    currentFile = 0
    # Count numfiles processed
    processedFiles = 0
    # Count frames processed
    totalFramesProcessed = 0

    if numFiles == 0:
        print('No files to process')
        
    else:
        print(f'Found {numFiles} file(s)')
            
        for files in sonarData:
            
            currentFile += 1
            print(f'Checking file {currentFile} of {numFiles}')
            #print(files)
            
            # Collecting the data from the sonar file
            didsonParams, acousticData = getFileData(filePath,files)
                
            # Check for corresponding data in the dataset before processing
            if(alreadyProcessed(didsonParams) == False):
                print(f'Processing file : {files}')
                
                # Get corresponding video file
                videoFile = getVideoFile(didsonParams)
                
                if videoFile == None:
                    print(f'Video file not found. Skipping Processsing')
                    continue
            
                # Process this file
                totalFramesProcessed += processData(didsonParams, acousticData, videoFile)
                
                processedFiles += 1
                
            else:
                print('File already processed, skipping processing')
                
        print(f'{processedFiles} file(s) of {currentFile} scanned. Number of frames processed: {totalFramesProcessed}')

    # files = 'BarkleyCanyon_BarkleyNode_MultibeamNon-rotatingSonar_20220901T110500.708Z_20220901T112000.000Z.mat'
    # didsonParams, acousticData = getFileData(filePath,files)
    # processData(didsonParams,acousticData)

if __name__ == '__main__':
    main()
