from ultralytics import YOLO
import cv2
import os

# COCO class IDs for animals we care about
ANIMAL_CLASSES = {
    15: 'cat',
    16: 'dog',
    17: 'horse',
    18: 'sheep',
    19: 'cow',
    20: 'elephant',
    21: 'bear',
    23: 'bird',
}

# Focus classes for our task
TARGET_CLASSES = {15: 'Cat', 16: 'Dog'}

CLASS_COLORS = {
    'Cat': (255, 165, 0),   # orange
    'Dog': (0, 200, 255),  # cyan
}

class AnimalDetector:
    def __init__(self, model_name='yolov8n.pt', confidence=0.4):
        print(f"Загрузка модели {model_name}...")
        self.model = YOLO(model_name)
        self.confidence = confidence
        print("Модель загружена.")

    def _parse_results(self, results):
        detections = []
        stats = {'Cat': 0, 'Dog': 0, 'total': 0}

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id not in TARGET_CLASSES:
                    continue
                label = TARGET_CLASSES[cls_id]
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append({
                    'label': label,
                    'confidence': round(conf, 3),
                    'bbox': [x1, y1, x2, y2]
                })
                stats[label] += 1
                stats['total'] += 1

        return detections, stats

    def _draw_boxes(self, img, detections):
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            label = det['label']
            conf = det['confidence']
            color = CLASS_COLORS.get(label, (0, 255, 0))

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            text = f"{label} {conf:.2f}"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(img, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
            cv2.putText(img, text, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        return img

    def detect_image(self, input_path, output_path):
        img = cv2.imread(input_path)
        results = self.model(img, conf=self.confidence, verbose=False)
        detections, stats = self._parse_results(results)
        annotated = self._draw_boxes(img.copy(), detections)
        cv2.imwrite(output_path, annotated)
        return detections, stats

    def detect_video(self, input_path, output_frame_path):
        cap = cv2.VideoCapture(input_path)
        all_detections = []
        total_stats = {'Cat': 0, 'Dog': 0, 'total': 0}
        frame_count = 0
        best_frame = None
        best_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            # Process every 10th frame for speed
            if frame_count % 10 != 0:
                continue

            results = self.model(frame, conf=self.confidence, verbose=False)
            detections, stats = self._parse_results(results)

            if stats['total'] > best_count:
                best_count = stats['total']
                best_frame = self._draw_boxes(frame.copy(), detections)

            for det in detections:
                all_detections.append(det)
            for k in ['Cat', 'Dog', 'total']:
                total_stats[k] += stats[k]

        cap.release()

        if best_frame is not None:
            cv2.imwrite(output_frame_path, best_frame)
        elif frame_count > 0:
            # Save a plain frame if nothing detected
            cap2 = cv2.VideoCapture(input_path)
            _, frame = cap2.read()
            cv2.imwrite(output_frame_path, frame)
            cap2.release()

        # Average stats per processed frame
        processed = max(frame_count // 10, 1)
        avg_stats = {
            'Cat': round(total_stats['Cat'] / processed, 1),
            'Dog': round(total_stats['Dog'] / processed, 1),
            'total': round(total_stats['total'] / processed, 1),
            'frames_processed': processed
        }
        return all_detections[:50], avg_stats  # cap detections list
