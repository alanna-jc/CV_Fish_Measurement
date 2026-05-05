# Automated Fish Measurer using Sonar Vision
## Objective
Using sonar data from Ocean Networks Canada (ONC), develop a model that can detect a fish, find it's length, and report back the average fish length over a specified time period. 

The motivation is to track the health of sablefish population. 

## TODO
- Try FFIR instead of GMM bgs
- Implement tracking Program
- Create polished program full pipeline
- Improve dataset generation scripts

## Repo Structure
### Model
**yolo_model.py**

Trains data using YOLOv11 and outputs predictions using best found model

### Program
**construct_frames.py**

Contains functions for creation of background subtracted frames

**calc_length.py**

Calculates the length of the fish given the largest bounding box from tracking

**main.py**

Runs full pipeline that creates constructed image, runs AI detection on, tracks fish, finds length, reports.

### Scripts
**download_ONC_data** (Step 1) [Made by Declan]

Downloads sonar and video files from ONC data base using Alanna token.

[insert table of what is downloaded]


**contruct_fused_frames.py** (Step 2) [Draft by Adriel, Edited by Alanna]

1. Creates PNG of .mat sonar code
2. Uses Gaussian Mixture Model (GMM) background subtraction to create background subtracted version (bgs)
3. Finds associated video frame
4. And combines them all into one image for annotation

Resulting in...<br>
[insert image of that]


**make_data_set_helper.py** (Step 3)

Toy script to extract a specified amount of constructed frames along with some context frames, to help form the dataset. 


**alter_annotations.py** (Step 4)

Annotations are done on Background subtracted section of combined image. After annotation, this script finds the corresponding original sonar image to the annotated one, and adjust bounding boxes.


