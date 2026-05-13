import cv2
import mediapipe as mp
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from std_msgs.msg import String



mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1, 
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils


class SignNode(Node):
    def __init__(self):
        super().__init__("sign_node")
        self.subscription = self.create_subscription(
            Image,
            '/camera/camera/color/image_raw',  
            self.image_callback,
            10)
        self.bridge = CvBridge()
        self.pub = self.create_publisher(String, 'hand_sign', 10)
        
    def get_gesture(self, landmarks):
        # 指の立ち状態を取得
        fingers = []
        for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
            fingers.append(landmarks[tip].y < landmarks[pip].y)

        # 1. 停止 (パー) - 最優先のため・
        if all(fingers):
            return "STOP"
        
        # 2. 前進 (人差し指)
        if fingers[0] and not any(fingers[1:]):
            return "FORWARD"

        # 3. 左右判定 (人差し指が立っているときのみ → 誤検知が減少が狙い)
        if landmarks[8].x > landmarks[0].x + 0.1:
            return "RIGHT"
        elif landmarks[8].x < landmarks[0].x - 0.1:
            return "LEFT"
                
        return "WAITING..."
        
    def image_callback(self, msg):
        try:
            # ROS2画像 → OpenCV画像に変換
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'CV Bridge error: {e}')
            return

        
        image = cv2.flip(frame, 1)
        debug_image = image.copy()
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
         # MediaPipeで検出
        results = hands.process(image_rgb)

        gesture_text = "NONE"

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # ランドマークを描画
                mp_draw.draw_landmarks(debug_image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # ジェスチャー判定
                gesture_text = self.get_gesture(hand_landmarks.landmark)

        # 判定結果を画面に表示
        cv2.putText(debug_image, f"Gesture: {gesture_text}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow('Gesture Control Feed', debug_image)
        
        msg_result = String()
        msg_result.data = gesture_text
        self.pub.publish(msg_result)
        


def main(args=None):
    rclpy.init(args=args)
    node = SignNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()