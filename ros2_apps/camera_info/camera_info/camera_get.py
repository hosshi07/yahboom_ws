import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool
from cv_bridge import CvBridge
import cv2
# QoS
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')
        
        # 1. リアルタイム画像転送に最適なQoSプロファイルを作成
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT, 
            history=HistoryPolicy.KEEP_LAST,
            depth=1                          
        )
        
        # パブリッシャーにQoSを適用
        self.publisher_ = self.create_publisher(Image, '/camera/camera/color/image_raw', qos_profile)
        
        self.num = 0
        self.cap = cv2.VideoCapture(self.num)  # カメラの初期化
        
        # 解像度を 640x480 (VGA) に設定
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
        # 2. 【重要】カメラの撮影能力（30fps）に合わせてタイマーを最適化
        # 0.033秒ごとに設定することで、OpenCV内部での詰まり（バッファ遅延）を完全に防ぎます by gemini
        self.create_timer(0.033, self.publish_image)  
        
        self.br = CvBridge()  
        self.get_logger().info("Camera Publisher Service Ready! (QoS: Best Effort / 30fps)")

    def publish_image(self):
        #バッファのの初期化 古いフレームを破棄
        self.cap.grab()
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().error("カメラからの映像を取得できませんでした。")
            return
            

        image_msg = self.br.cv2_to_imgmsg(frame, encoding='bgr8')
        
        # 画像をパブリッシュ
        self.publisher_.publish(image_msg)

    def destroy_node(self):
        self.cap.release()  # カメラを解放
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    camera_publisher = CameraPublisher()
    try:
        rclpy.spin(camera_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        camera_publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()