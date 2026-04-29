"""
The annotations are done on a composite image. This script moves those annotations over and finds the original unaltered sonar frame associated with it.

"""


# imports
import os
import cv2
import glob


# save it to the right places
script_dir = os.path.dirname(os.path.abspath(__file__))

# project root
project_root = os.path.dirname(script_dir)

label_filepath = os.path.join(project_root, 'Model', 'dataset', 'labels', 'val')
src_new_img_filepath = os.path.join(project_root, 'Scripts', 'Test Data', 'Processed Acoustic Data')
dst_new_img_filepath = os.path.join(project_root, 'Model', 'dataset', 'images', 'val')

# hardcoded oops
# tuple of (height, width, channels)
old_image_shape = (300, 1333, 3)

def read_yolo_annotations(filepath):
    '''
    Reads a YOLO .txt file and assigns the values to clearly named variables.
    Returns a list of dictionaries.
    '''
    bounding_boxes = []
    
    if not os.path.exists(filepath):
        print(f"Error: The file {filepath} does not exist.")
        return bounding_boxes

    with open(filepath, 'r') as file:
        for line in file:
            parts = line.strip().split()
            
            # safety check
            if len(parts) == 5:
                # create dictionary
                box = {
                    'class_id': int(parts[0]),
                    'x_center': float(parts[1]),
                    'y_center': float(parts[2]),
                    'width': float(parts[3]),
                    'height': float(parts[4])
                }
                bounding_boxes.append(box)
                
    return bounding_boxes

# TODO alter this
def modify_yolo_annotations(original_shape, new_shape, bounding_boxes, shift_x=400):
    '''
    Adjusts YOLO normalized coordinates when an image is cropped or shifted.
    
    Params:
        original_shape: Tuple of (height, width) of the original composite image.
        new_shape: Tuple of (height, width) of the target image size.
        bounding_boxes: List of dictionaries containing the YOLO box variables.
        shift_x: The number of pixels to shift the annotations to the left.
                           
    Returns:
        List of dictionaries with updated normalized coordinates.
    '''
    
    # get height and widths from passed shapes
    orig_h, orig_w = original_shape[:2]
    new_h, new_w = new_shape[:2]

    updated_boxes = []
    
    for box in bounding_boxes:
        # convert the normalized YOLO coordinates to their original scaled coordinates
        abs_x = box['x_center'] * orig_w
        abs_y = box['y_center'] * orig_h
        abs_width = box['width'] * orig_w
        abs_height = box['height'] * orig_h
        
        # shift the x coordinate left by 400 pixels (as the composite image is annotated on the background subtracted version to the right of og)
        new_abs_x = abs_x - shift_x
        new_abs_y = abs_y # no change to y
        
        # renormalize the coords given the new image shape
        updated_box = {
            'class_id': box['class_id'],
            'x_center': new_abs_x / new_w,
            'y_center': new_abs_y / new_h,
            'width': abs_width / new_w,
            'height': abs_height / new_h
        }
        
        # Optional Check: If the box was completely outside the new 400x300 area, 
        # you might want to discard it rather than clamping it to the edge.
        # if (updated_box['x_center'] + (updated_box['width'] / 2) < 0) or \
        #    (updated_box['x_center'] - (updated_box['width'] / 2) > 1):
        #     continue

        # Safety constraint: Ensure math didn't push values out of bounds (clips to edge)
        # updated_box['x_center'] = max(0.0, min(updated_box['x_center'], 1.0))
        # updated_box['y_center'] = max(0.0, min(updated_box['y_center'], 1.0))
        # updated_box['width'] = max(0.0, min(updated_box['width'], 1.0))
        # updated_box['height'] = max(0.0, min(updated_box['height'], 1.0))
        
        updated_boxes.append(updated_box)
        
    return updated_boxes


def write_yolo_annotations(filepath, bounding_boxes):
    '''
    Writes to a YOLO .txt
    '''
    with open(filepath, 'w') as file:
        for box in bounding_boxes:
            # Reconstruct format, keeping same precision as YOLO
            line = f"{box['class_id']} {box['x_center']:.6f} {box['y_center']:.6f} {box['width']:.6f} {box['height']:.6f}\n"
            file.write(line)


def main():
    
    to_alter = 0
    # i need this script to work for my data without fish, which is already separated, so no worry there
    answer = input("Do the labels need altering? (yes/no): ").strip().lower()

    if answer in ['yes', 'y']:
        to_alter = 1
        print('Altering labels...')
    elif answer in ['no', 'n']:
        to_alter = 0
        print('Not altering labels...')
    elif answer not in ['yes', 'no', 'y', 'n']:
        print("Invalid input. Please run the program again and type 'yes' or 'no' (or 'y' or 'n').")
        return
    
    # create if does not exist file paths
    # the other file paths must already exist to have files in them
    print('Starting conversions')
    try:
        os.makedirs(os.path.dirname(dst_new_img_filepath), exist_ok=True)
        print("Directories created")  
    except OSError as error:
        print("Error creating directory")
        
    # annotation files
    if not os.path.exists(label_filepath) or not os.path.isdir(label_filepath):
        raise FileNotFoundError(f"The directory '{label_filepath}' does not exist.")
    
    txt_files = sorted(glob.glob(os.path.join(label_filepath, '*.txt')))
    if not txt_files:
        raise ValueError(f"The directory '{label_filepath}' contains 0 .txt files.")
    
    # original sonar images
    if not os.path.exists(src_new_img_filepath) or not os.path.isdir(src_new_img_filepath):
        raise FileNotFoundError(f"The directory '{src_new_img_filepath}' does not exist.")
    
    sonar_images = sorted(glob.glob(os.path.join(src_new_img_filepath, '*.png')))
    if not sonar_images:
        raise ValueError(f"The directory '{src_new_img_filepath}' contains 0 .png files.")

    # Loop through each file
    for file in txt_files:
        
        txt_filename = os.path.basename(file)
        txt_basename, _ = os.path.splitext(txt_filename)
        expected_png_filename = f"{txt_basename}.png"
        img_path = os.path.join(src_new_img_filepath, expected_png_filename)
        
        if not os.path.exists(img_path):
            print(f"Missing sonar image for {img_path}. Skipping")
            continue 
        
        # get image shape
        img = cv2.imread(img_path)
        shape = img.shape
        
        # save image to correct place
        # TODO add check if image already there? ir dies cv2.imwrite do for
        img_new_path = os.path.join(dst_new_img_filepath, expected_png_filename)
        success = cv2.imwrite(img_new_path, img)
        
        if not success:
            raise AssertionError(f"could not write {expected_png_filename} to new directory")
        
        if to_alter == 1:
            # read yolo annotations
            annotation = read_yolo_annotations(file)
            # modify yolo annotations
            new_annotation = modify_yolo_annotations(old_image_shape, shape, annotation)
            # write yolo annotations
            write_yolo_annotations(file, new_annotation)
        
    print('Alterations complete')

    
if __name__ == '__main__':
    main()
