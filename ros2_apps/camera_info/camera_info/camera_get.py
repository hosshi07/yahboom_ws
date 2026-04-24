import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')
        self.publisher_ = self.create_publisher(Image, '/camera/camera/color/image_raw', 10)
        try:
            self.num = int(input("カメラのusb番号は: "))
        except:
            self.num = 0
        self.timer = self.create_timer(0.01, self.publish_image)  # 0.1秒ごとに画像をパブリッシュ
        self.cap = cv2.VideoCapture(self.num)  # カメラ番号を指定
        self.br = CvBridge()  # CvBridgeのインスタンスを作成
        self.get_logger().info("service ready!")

    def publish_image(self):
        ret, frame = self.cap.read()  # カメラからフレームを取得
        if not ret:
            self.get_logger().error("カメラからの映像を取得できませんでした。")
            return
        image = cv2.flip(frame, 1)  # 水平反転
        cv2.imshow('Pub Image', image)
        cv2.waitKey(1)
        # OpenCVのBGR画像をROSのImageメッセージに変換
        image_msg = self.br.cv2_to_imgmsg(frame, encoding='bgr8')
        # 画像をパブリッシュ
        self.publisher_.publish(image_msg)
        #self.get_logger().info("画像をパブリッシュしました。")

    def destroy_node(self):
        cv2.destroyAllWindows()
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

