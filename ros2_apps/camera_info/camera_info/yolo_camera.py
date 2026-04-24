import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO
colors = {
    0: (255, 0, 0),    # クラスID 0 の物体（例: 人）
    1: (0, 255, 0),    # クラスID 1 の物体（例: 自転車）
    2: (0, 0, 255),    # クラスID 2 の物体（例: 車）
    67: (100, 20, 0),
    # 必要に応じて他のクラスを追加
}
class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')
        self.publisher_ = self.create_publisher(Image, 'camera/yolo', 10)
        command = input("カメラのモデルは?(lap or logi): ")
        # カメラ番号の設定
        self.num = 4 if command == "logi" else 0
        self.img_sub = self.create_subscription(Image, '/camera/image', self.get_img, 10)
        self.timer = self.create_timer(0.01, self.publish_image)  # 0.1秒ごとに画像をパブリッシュ
        self.cap = cv2.VideoCapture(self.num)  # カメラ番号を指定
        self.br = CvBridge()  # CvBridgeのインスタンスを作成
        self.model = YOLO("yolov8n.pt")
        
    def get_img(self, img):
        try:
            self.img = self.br.imgmsg_to_cv2(img, "bgr8")
        except:
            self.get_logger().info("imgがない")
            
    def publish_image(self):
        ret, frame_e = self.cap.read()  # カメラからフレームを取得
        if not ret:
            #self.get_logger().error("カメラからの映像を取得できませんでした。")
            try:
                frame_e = self.img
            except:
                return
            frame = cv2.flip(frame_e, 1)  # 水平反転
        # 物体検出
        else:
            frame = cv2.flip(frame_e, 1)
        results = self.model(frame)  # フレームをモデルに渡して検出を実行

        # 検出結果の描画
        for result in results:
            boxes = result.boxes  # 検出ボックスを取得
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]  # バウンディングボックスの座標
                conf = box.conf[0]  # 信頼度
                cls = int(box.cls[0])  # クラスIDを整数に変換

                # クラスIDに基づいて色を取得
                color = colors.get(cls, (255, 255, 255))  # 指定された色がない場合は白を使用

                # バウンディングボックスを描画
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                cv2.putText(frame, f'ID: {cls}, Conf: {conf:.2f}', (int(x1), int(y1) - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv2.imshow('Pub YOLO', frame)
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

