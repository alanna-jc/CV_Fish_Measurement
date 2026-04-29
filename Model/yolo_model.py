from ultralytics import YOLO


def main():
    # Load YOLOv3 pretrained
    model = YOLO("yolov3.pt")

    # https://docs.ultralytics.com/modes/train/#musgd-optimizer
    print("Starting training...")
    model.train(data="dataset.yaml", 
            epochs = 20, # cause small dataset sample
            batch = 4,
            patience = 5, # number of epochs to wait with little improvement to loss
            imgsz = 416, # not 400 cause of mulitple of 32??
            rect = True, # enables minimum padding
            cos_lr = False, #cosine learning rate (default)
            close_mosaic = 0, # data augmentation
            lr0 = 0.01, # inital learning rate (default)
            lrf = 0.01, # final learning rate as a fraction of og. lr0*lrf
            val = True, # default
            plots = True, # default
            hsv_h = 0,
            hsv_s = 0,
            hsv_v = 0,
            translate = 0,
            scale = 0,
            fliplr = 0,
            mosaic = 0,
            erasing = 0 # randomly erases parts of image
            )

    # change so we know where this goes ( i think i sometimes use old one?)
    best_model = YOLO("runs/detect/train/weights/best.pt")

    # https://docs.ultralytics.com/modes/predict/#inference-sources
    results = best_model.predict(
    source="dataset/images/test",  
    save=True,                     # saves images with boxes
    conf=0.25                      # confidence threshold (what is it?)
    )

if __name__ == "__main__":
    main()