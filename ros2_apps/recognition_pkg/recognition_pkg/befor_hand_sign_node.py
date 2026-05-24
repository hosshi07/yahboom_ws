import cv2
import mediapipe as mp
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from std_msgs.msg import String
import math



mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,        # 動画ストリームとして処理（これ重要）
    max_num_hands=1,                # 認識する手は「1つ」に制限（計算量が半減！）
    model_complexity=0,             # 【超重要】0:最速, 1:標準。0にすると劇的に軽くなります
    min_detection_confidence=0.5,
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
        idx_tip = landmarks[8]   # 人差し指先端
        idx_mcp = landmarks[5]   # 人差し指付け根
        rng_tip = landmarks[16]  # 薬指先端
        rng_mcp = landmarks[13]  # 薬指付け根
        wrist = landmarks[0]     # 手首
        mid_mcp = landmarks[9]   # 中指付け根

        #共通の基準
        palm_size = math.sqrt((mid_mcp.x - wrist.x)**2 + (mid_mcp.y - wrist.y)**2)
        if palm_size == 0: return "WAITING..."

        # 薬指の長さでSTOP判定
        ring_len = math.sqrt((rng_tip.x - rng_mcp.x)**2 + (rng_tip.y - rng_mcp.y)**2)
        if (ring_len / palm_size) > 0.8:
            return "STOP"

        # y座標の比較をやめ、人差し指が「伸びているか」を見ます
        idx_len = math.sqrt((idx_tip.x - idx_mcp.x)**2 + (idx_tip.y - idx_mcp.y)**2)
        
        # 手のひらに対して人差し指が一定以上の長さ（例: 0.7以上）なら操作中
        if (idx_len / palm_size) > 0.7:
            dx = idx_tip.x - idx_mcp.x
            dy = idx_tip.y - idx_mcp.y
            deg = math.degrees(math.atan2(-dy, dx))
            if deg < 0:
                deg += 360

            if 150 < deg <= 230:
                return "LEFT"
            elif deg < 35 or deg >= 300:
                return "RIGHT"
            elif 231 < deg < 299:
                return "BEHYND"
            else:
                return "FORWARD"

        # 指を曲げている（グーの状態）
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
        rclpy.shutdown()

if __name__ == '__main__':
    main()