# using bounding boxes track a fish. get a count. find biggest bounding box of fish
import cv2 as cv
import numpy as np
import os
from skimage.morphology import skeletonize
from skan import Skeleton, summarize
# skan: https://skeleton-analysis.org/stable/getting_started/getting_started.html#extracting-a-skeleton-from-an-image
# skiimage: https://scikit-image.org/docs/stable/auto_examples/edges/plot_skeleton.html
# it appears yolo does this itself

def get_bboxes(dict_tracked_boxes, results):

    for r in results:
            if r.boxes is None or r.boxes.id is None:
                continue

            
            # strike through: get ids. Note .cpu moves them fro gpu to cpu
            # tolist() moves to cpu
            ids = r.boxes.id.tolist()
            
            # get bounding boxes
            boxes = r.boxes.xyxy.tolist()
            
            # get frame
            full_path = r.path
            #file_path = os.path.basename(full_path)
            
            # for loop if there are multiple fishies in an image
            # zip makes sure zip and box are connected
            for id, box in zip(ids, boxes):
                
                # packaging box with frame
                box_package = {
                    "box": box,
                    "frame": full_path
                }
                dict_tracked_boxes[int(id)].append(box_package)
                
            
def get_max_length(dict_tracked_boxes, dict_max_lengths, threshold):
    
    for id, box_packages in dict_tracked_boxes.items():
        # If there are less than threshold number of bounding boxes, skip to the next fish_id
        if len(box_packages) < threshold:
            continue 
        
        lengths = []
        
        for package in box_packages:
            box = package["box"]
            frame_path = package["frame"]
            
            frame = cv.imread(frame_path)
            
            length = calc_length(frame, box)
            lengths.append(length)
        
        # TODO loop through list and retrieve largest value
        max_length = max(lengths)
    
        # TODO append largest value to dict along with associated id
        dict_max_lengths[int(id)].append(max_length)

    return
            
            
def calc_length(frame, bbox):
            
    # look at part of image that bounding box covers
    x1, y1, x2, y2 = map(int, bbox)
    cropped_frame = frame[y1:y2, x1:x2]
    
    # must be greyscale (it should be but i forgot to do this)
    if len(cropped_frame.shape) == 3:
        grey = cv.cvtColor(cropped_frame, cv.COLOR_BGR2GRAY)
    else:
        grey = cropped_frame
    
    # NOTE: can also use skan.pre.threshold
    # TODO eval
    blurred = cv.medianBlur(grey, 5)
    
    # binary the image
    # using otsu's threshold which calcs optimal threshold
    _, thresh = cv.threshold(blurred, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

    # morphology to make it unified
    # TODO eval
    kernel = np.ones((5, 5), np.uint8)
    closing = cv.morphologyEx(thresh, cv.MORPH_CLOSE, kernel)

    # skeletize it
    skeleton0 = skeletonize(closing) # zha84 method
    
    extracted_data = summarize(Skeleton(skeleton0))
    # AC ai helped line, what is iloc?
    length = extracted_data['branch-distance'].iloc[0]
    
    # TODO convert this length to actual real life lengths rather than pixel lengths
    
    return length
