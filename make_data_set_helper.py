import os
import shutil
from collections import defaultdict

SOURCE_DIR = "all_frames"

SELECTED_DIR = "dataset/selected_frames"
CONTEXT_DIR = "dataset/context_frames"

NUM_TARGET_FRAMES = 400
# there will be this many frames taken from either side 
NUM_CONTEXT_FRAMES = 15


def main():

    videos = defaultdict(dict)
    num_frames = 0

    # build video dictionary (it is nested)
    for f in os.listdir(SOURCE_DIR):

        if not f.endswith(".png"):
            continue

        num_frames += 1

        video = f.split("_frame")[0]
        frame_num = int(f.split("_frame")[1].split(".")[0])

        videos[video][frame_num] = f


    num_videos = len(videos)

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

            # grab 15 before and after
            for j in range(i - NUM_CONTEXT_FRAMES, i + NUM_CONTEXT_FRAMES + 1):
                
                # skip the selected frame
                if i == j:
                    continue

                context_key = sorted_frames[j]
                # might need to append the key with the video name to make next section easier 
                context_frames.append(frames[context_key])


    # now copy all of the frames from the source dir that are selected into the selected folder
    # and copy all of the frames from the source dir that are cobtext frames into the context folder
    '''
    for frame in selected_frames:

        src = os.path.join(SOURCE_DIR, frame)
        dst = os.path.join(SELECTED_DIR, frame)

        shutil.copy(src, dst)

    # copy context frames
    for frame in context_frames:

        src = os.path.join(SOURCE_DIR, frame)
        dst = os.path.join(CONTEXT_DIR, frame)

        shutil.copy(src, dst)
    '''


if __name__ == "__main__":
    main()