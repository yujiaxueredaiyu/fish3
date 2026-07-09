import math
import sys

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    HAS_MP_TASKS = True
except ImportError:
    HAS_MP_TASKS = False

try:
    from mediapipe.solutions import hands as mp_hands
    HAS_MP_SOLUTIONS = True
except ImportError:
    HAS_MP_SOLUTIONS = False


class HandDetector:
    def __init__(self):
        self.detector = None
        self.use_tasks_api = False
    
    def init_detector(self, model_path='hand_landmarker.task'):
        if HAS_MP_TASKS:
            try:
                base_options = python.BaseOptions(model_asset_path=model_path)
                options = vision.HandLandmarkerOptions(
                    base_options=base_options,
                    num_hands=1,
                    min_hand_detection_confidence=0.5,
                    min_hand_presence_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.detector = vision.HandLandmarker.create_from_options(options)
                self.use_tasks_api = True
                print("Using MediaPipe Tasks API")
                sys.stdout.flush()
                return True
            except Exception:
                pass
        
        if HAS_MP_SOLUTIONS:
            try:
                self.detector = mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.use_tasks_api = False
                print("Using MediaPipe Solutions API")
                return True
            except Exception:
                pass
        
        print("No MediaPipe API available")
        return False
    
    def detect_hand(self, frame_rgb):
        if self.use_tasks_api and HAS_MP_TASKS:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            result = self.detector.detect(mp_image)
            
            if hasattr(result, 'hand_landmarks') and result.hand_landmarks:
                landmarks = result.hand_landmarks[0]
                wrist = landmarks[0]
                return {
                    'x': wrist.x,
                    'y': wrist.y,
                    'landmarks': landmarks,
                    'is_fist': self._detect_fist(landmarks)
                }
            return None
        elif not self.use_tasks_api and HAS_MP_SOLUTIONS:
            result = self.detector.process(frame_rgb)
            
            if result.multi_hand_landmarks:
                landmarks = result.multi_hand_landmarks[0]
                wrist = landmarks.landmark[0]
                return {
                    'x': wrist.x,
                    'y': wrist.y,
                    'landmarks': landmarks.landmark,
                    'is_fist': self._detect_fist(landmarks.landmark)
                }
            return None
        return None
    
    def _detect_fist(self, landmarks):
        if not landmarks or len(landmarks) < 21:
            return False
        
        def is_finger_folded(tip_idx, pip_idx):
            tip_y = landmarks[tip_idx].y
            pip_y = landmarks[pip_idx].y
            return tip_y > pip_y + 0.02
        
        folded_count = 0
        
        if is_finger_folded(8, 6):
            folded_count += 1
        if is_finger_folded(12, 10):
            folded_count += 1
        if is_finger_folded(16, 14):
            folded_count += 1
        if is_finger_folded(20, 18):
            folded_count += 1
        
        thumb_tip = landmarks[4]
        wrist = landmarks[0]
        thumb_dist = math.sqrt((thumb_tip.x - wrist.x)**2 + (thumb_tip.y - wrist.y)**2)
        if thumb_dist < 0.15:
            folded_count += 1
        
        return folded_count >= 4