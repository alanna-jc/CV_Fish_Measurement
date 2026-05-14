# Autonomaus Fish Measurer using Sonar Vision
## Objective
Using sonar data from Ocean Networks Canada (ONC), develop a model that can detect a fish, find it's length, and report back the average fish length over a specified time period. 

*The motivation is to track the health of sablefish population.* 

## Program Description
| <img src="Assets/sonar_example.png" width="200" alt="Example of Sonar">| <img src="Assets/tracked_fish_1.jpg" width="200" alt="Tracked fish frame 1"> <img src="Assets/tracked_fish_1.jpg" width="200" alt="Tracked fish frame 2"> |
| :---: | :---: |
| 1. Downloads and constructs sonar data | 2. Detects and tracks fish |

[insert table with images  of 3. processes image and skeletonizes to find most accurate length]
[ TODO 4. reports it via csv]

## TODO
- Try FFIR instead of GMM bgs
- Add 'download' and 'CSV generation' to program
- Create user prompts for use ease
- Create python package of program
- Develop further testing
- Increase dataset
- Build in more generalization for future use cases

## Repo Structure
### Model
**yolo_model.py**

Trains data using YOLOv11 and outputs predictions using best found model

### Program
**construct_frames.py**
<br>Contains functions for creation of background subtracted frames

**calc_length.py**
<br>Calculates the length of the fish given the largest view from tracking. Length is found using skeletonization.

**main.py**
<br>Runs full pipeline that creates constructed image, runs AI detection on, tracks fish, finds length, reports.

### Scripts
**download_ONC_data** (Step 1) [Made by Declan]
<br>Downloads sonar and video files from ONC data base.
<br><img src="Assets/download_result.png" width="200" alt="Results of download">

**contruct_fused_frames.py** (Step 2) [Draft by Adriel, Edited by Alanna] <br>
1. Creates PNG of .mat sonar code
2. Uses Gaussian Mixture Model (GMM) background subtraction to create background subtracted version (bgs)
3. Finds associated video frame
4. And combines them all into one image for annotation

Resulting in...<br>
<img src="Assets/combined_image.png" width="600" alt="Combined image">

**make_data_set_helper.py** (Step 3)
<br>Toy script to extract a specified amount of constructed frames along with some context frames, to help form the dataset. 

**alter_annotations.py** (Step 4)
<br>Annotations are done on Background subtracted section of combined image. After annotation, this script finds the corresponding original sonar image to the annotated one, and adjust bounding boxes.


