# Bounding boxes ++
import numpy as np
import os
import glob
from ultralytics import YOLO
from collections import defaultdict

from construct_frames import process_matfile, process_frame
from calc_lengths import get_bboxes, get_max_length



# for now lets not download from onc lets just get matlab files from a folder
dirPath = os.getcwd()
file_path = os.path.join(dirPath,'Sonar Data')
bgs_write_path = os.path.join(dirPath,'Processed Frames')
MIN_BOX_THRESHOLD = 3

def main():
    # set up model
    model = YOLO("weights/best.pt")
    
    try:
        os.makedirs(os.path.dirname(bgs_write_path), exist_ok=True)
        print("Directories created")  
    except OSError as error:
        print("Error creating directory")

    # Get that Sonar data
    sonar_files = sorted(glob.glob(os.path.join(file_path,'*.mat')))

    # Total files in sonar data
    num_files = len(sonar_files)
    if num_files == 0:
        print('No files to process')
        
    else:
        print(f'Found {num_files} file(s)')
    
    # TODO add in extraction of file name for csv   
    for file in sonar_files:

        # AC temp for debug
        """
        didsonParams, acousticData = process_matfile(file_path, file)

        count = 1
        
        for frame in np.arange(didsonParams['numFrames']): 
            process_frame(frame, acousticData, didsonParams, bgs_write_path, count)
            count += 1
        """
        
        # Use bytetrac

        # save to json. 
        results = model.track(
            source = bgs_write_path,
            tracker="bytetrack.yaml",
            save = True,
            persist = True,
            conf = 0.5
        )
        
        tracked_boxes = defaultdict(list)
        
        # python auto passes dict as a pointer
        # get all bounding boxes 
        get_bboxes(tracked_boxes, results)
        
        list_o_lengths = defaultdict(list)
        
        get_max_length(tracked_boxes, list_o_lengths, MIN_BOX_THRESHOLD)
        
        # debug
        #print(list_o_lengths)

        # TODO create the dict to end all dicts
 
     # csv stuff
    #df = pd.DataFrame( data )
    #df.to_csv('csv')   
    
    
if __name__ == '__main__':
    main()