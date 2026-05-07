import numpy as np
import os
import datetime
import matplotlib.pyplot as plt
from pymatreader import read_mat


def process_matfile(file_path, file_name):
    """
    Get that mat data and do file level calcs for later use
    
    Returns:
        didsonParams:
        acousticData:

    """
    # Read mat file
    fullPath = os.path.join(file_path, file_name)
    mat = read_mat(fullPath)
    
    Data = mat['Data']
    Config = mat['Config']
    Meta = mat['Meta']
    acousticData = Data['acousticData']

    # Extract parameters
    didsonParams = { 
        'winStart'          : Config['windowStart'][2],
        'winLength'         : Config['windowLength'][2],
        'numFrames'         : len(acousticData[0,0,:]),
        'frameRate'         : Config['frameRate'],
        'numBeams'          : Config['numBeams'],
        'sampleRate'        : Config['sampleRate'],
        'samplesPerBeam'    : Config['samplesPerBeam'][0],
        'frameTime'         : Data['frameTimeStr'],
        'frameNumber'       : Data['frameNumber'],
        'fileName'          : file_name,
        'year'              : Data['year'],
        'month'             : Data['month'],
        'day'               : Data['day'], # this was shown to be sometimes wrong in the files see update
        'hour'              : Data['hour'], # this was shown to be sometimes wrong in the files see update
        'minute'            : Data['minute'],
        'second'            : Data['second'],
        'Hsecond'           : Data['hsecond'],
        'filePath'          : file_path}
    
    # ------------------------ calculations -------------------------------
    file_basename = os.path.basename(file_name)
    position = file_basename.find("T")

    # Set range for polar plot
    range = np.linspace(didsonParams['winStart'],didsonParams['winLength']+didsonParams['winStart'],didsonParams['samplesPerBeam'])
    
    # matlab code from ONC:                         
    # theta = ANGLEAMP*linspace(-14*(2*pi)/360,14*2*pi/360,size(Data.acousticData,1));
    # ignore angle amp .we working with REAL numbers hear      
    theta = np.linspace(-14*(2*np.pi)/360, 14*2*np.pi/360, didsonParams['numBeams'])

    # meshgrid: r along first axis, theta along second
    r, th = np.meshgrid(range, theta, indexing='ij')  # use indexing='ij' to match z
    # ----------------------------------------------------------------------
    
    # Calculated parameters
    didsonParams.update({
        'range'             : r,
        'theta'             : th,
        'dataMedian'        : np.median(acousticData,axis=(2)), # for bgs
        # 'day'               : int(file_basename[(position+1):(position+3)]), TODO put in correct one
        'hour'              : int(file_basename[(position+1):(position+3)])
        })
    
    return didsonParams, acousticData


def get_date_and_time(frame, didsonParams):

    year = didsonParams['year'][0]
    month = didsonParams['month'][0]
    day = didsonParams['day'][0]
    hour = didsonParams['hour'] # not an array as pulled from file name

    # Synchronized instrument time at desired frame
    minute = didsonParams['minute'][frame]
    second = didsonParams['second'][frame]
    millisec = didsonParams['Hsecond'][frame]   # not a milli but i think still correct outcome
    
    temp_datetime = datetime.datetime(year, month, day, hour, minute, second, millisec)
    full_datetime = temp_datetime.strftime("%Y%m%dT%H%M%S.%f")[:-3]
    full_datetime += 'Z'
    
    frame_datetime = full_datetime[0:11]
    
    return frame_datetime
 

def process_frame(frame, acousticData, didsonParams, bgs_write_path, frame_count):

    z_subtracted = np.subtract(acousticData[:,:,frame], didsonParams['dataMedian'])
    z_subtracted[z_subtracted<0]=0
    
    frame_timestamp = get_date_and_time(frame, didsonParams)
    
    # :04d adds zero pad at beginning of numbers so they are in correct order
    frame_write_path = os.path.join(bgs_write_path, f'{frame_timestamp}.Frame_{frame_count:04d}.png')

    create_image(z_subtracted, didsonParams['range'], didsonParams['theta'], frame_write_path)
    
    print(f'PNG of frame {frame_count} created')
    
    return

       
def  create_image(z, r, th, frame_path):
    """
    Creates png given data
    """
    fig, ax = plt.subplots(
                            figsize=(4, 3),              # 4×3 inches
                            dpi=100,                     # 100 dpi → 400×300 pixels
                            subplot_kw={'projection': 'polar'}
                        )                   

    # ---------- settings -----------
    # black background
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black') 
    
    ax.set_theta_zero_location('N')
    ax.axis('off')
    
    # makes it so that full circle is not drawn
    ax.set_thetamin( -14 )
    ax.set_thetamax( 14 )
    
    fig.tight_layout(pad=0)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_aspect('equal')
    # -------------------------------
    
    ax.contourf(th.T, r.T, z, 50)   
    
    fig.savefig(frame_path, pad_inches=0)
    plt.close("all")

    return