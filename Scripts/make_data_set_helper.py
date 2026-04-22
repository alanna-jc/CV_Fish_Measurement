"""
Purpose: To aid with selecting frames for annotation, selects a a specified amount of uniformly spaced frames and adds a specified 
         amount of frames around it to a separate folder to help aid annotation.

         This script is mainly useful for getting a certain type of frame from multiple similar videos (like a set of videos with 
         lots of fish activity or a set of frames with no activity)

Usage: Change macros to specify the directory structure, how many frames you want from the amount you have, and how many frames to 
        save as context frames. 

To do: Have number of frames to target be something you input in as user at run time, make the check useful for if context window too big,
        check if path exists and create it if it doesn't

"""

import os
import shutil
from collections import defaultdict

CURRENT_DIR = os.getcwd()
SOURCE_DIR = os.path.join(CURRENT_DIR,'Test Data', 'Combined Data')
SELECTED_DIR = os.path.join(CURRENT_DIR,'Test Data', 'Combined Data', 'Selected Frames')
CONTEXT_DIR = os.path.join(CURRENT_DIR,'Test Data', 'Combined Data', 'Context Frames')

NUM_TARGET_FRAMES = 600
# there will be this many frames taken from either side 
NUM_CONTEXT_FRAMES = 5


def main():

    videos = defaultdict(dict)
    num_frames = 0

    # build video dictionary (it is nested)
    for f in os.listdir(SOURCE_DIR):

        if not f.endswith(".png"):
            continue

        num_frames += 1

        video = f.split(".Frame_")[0]
        frame_num = int(f.split(".Frame_")[1].split(".")[0])

        videos[video][frame_num] = f


    num_videos = len(videos)

    print(f"Number of frames = {num_frames}, number of videos = {num_videos}")

    selected_frames = []
    context_frames = []

    # uniform sampling step across the dataset
    step_size = max(1, num_frames // NUM_TARGET_FRAMES)
    
    print(f"step_size: {step_size}")
    
    if step_size < (NUM_CONTEXT_FRAMES*2):
        print(f"step size does not support context frames specified")


    for video, frames in videos.items():

        # sort because dict does not guarantee order
        sorted_frames = sorted(frames.keys())

        for i in range(NUM_CONTEXT_FRAMES, len(sorted_frames), step_size):

            selected_key = sorted_frames[i]
            # might need to append the key with the video name to make next section easier 
            selected_frames.append(frames[selected_key])

            # grab context frames from before and after, including the selected frame
            for j in range(i - NUM_CONTEXT_FRAMES, i + NUM_CONTEXT_FRAMES + 1):
                
                # crappy IndexError fix
                if (i + NUM_CONTEXT_FRAMES) >= len(sorted_frames):

                    continue

                context_key = sorted_frames[j]
                # might need to append the key with the video name to make next section easier 
                context_frames.append(frames[context_key])

    # Testing print statements
    #print(f"selected list: {selected_frames} \n")
    #print(f"context list: {context_frames} \n")

    # now copy all of the frames from the source dir that are selected into the selected folder
    # and copy all of the frames from the source dir that are cobtext frames into the context folder
    print("Copying selected frames to folder...")

    for frame in selected_frames:

        src = os.path.join(SOURCE_DIR, frame)
        dst = os.path.join(SELECTED_DIR, frame)

        shutil.copy(src, dst)

    # copy context frames
    print("Copying context frames to folder...")
    for frame in context_frames:

        src = os.path.join(SOURCE_DIR, frame)
        dst = os.path.join(CONTEXT_DIR, frame)

        shutil.copy(src, dst)

if __name__ == "__main__":
    main()
