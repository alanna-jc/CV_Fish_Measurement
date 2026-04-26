# Automated Fish Measurer using Sonar Vision
## Objective
Using sonar data from Ocean Networks Canada (ONC), develop a model that can detect a fish, find it's length, and report back the average fish length over a specified time period. 

The motivation is to track the health of sablefish population. 

## Repo Structure
### Model
**yolo_model.py**

Trains data using YOLO pretrained model and outputs predictions using best found model

### Scripts
**download_ONC_data** (Step 1) [Made by Declan]

Downloads sonar and video files from ONC data base using Alanna token.

[insert table of what is downloaded]


**contruct_fused_frames.py** (Step 2) [Draft by Adriel, Edited by Alanna]

Creates PNG of .mat sonar code

[insert image of that]

Uses Gaussian Mixture Model (GMM) background subtraction to create background subtracted version (bgs)

[insert image of that]

Finds associated video frame

[insert image of that]

And combines them all into one image for annotation

[insert image of that]


**make_data_set_helper.py** (Step 3)

Toy script to extract a specified amount of constructed frames along with some context frames, to help form the dataset. 


**alter_annotations.py** (Step 4)

Annotations are done on Background subtracted section of combined image. After annotation, this script finds the corresponding original sonar image to the annotated one, and adjust bounding boxes.

[insert some sort of image explaining?]

## TODO

