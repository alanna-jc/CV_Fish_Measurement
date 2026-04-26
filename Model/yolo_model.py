from ultralytics import YOLO

# Load YOLOv3 pretrained
model = YOLO("yolov3.pt")

# https://docs.ultralytics.com/modes/train/#musgd-optimizer
model.train(data = "dataset.yaml")

print("Starting training...")
model.train(data="dataset.yaml", 
            epochs = 20, # cause small dataset sample
            imgsz = 416, # not 400 cause of mulitple of 32??
            val = True, # default
            plots = True # default
            )

best_model = YOLO("runs/detect/train/weights/best.pt")

# https://docs.ultralytics.com/modes/predict/#inference-sources
results = best_model.predict(
    source="path/to/test/images",  
    save=True,                     # saves images with boxes
    conf=0.25                      # confidence threshold (what is it?)
)