from ultralytics import YOLO

# Load YOLOv3 pretrained
model = YOLO("yolov3.pt")

# https://docs.ultralytics.com/modes/train/#musgd-optimizer
model.train(data = dataset.yaml)

results = model.predict()  