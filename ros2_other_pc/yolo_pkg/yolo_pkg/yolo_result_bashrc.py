import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import torch
import os


# カスタムメッセージのインポート
from yolo_msgs.msg import DetectionArray, Detection, BoundingBox2D

class YoloDetectorNode(Node):
    def __init__(self):
        super().__init__('yolo_detector_node')

        
        model_path = os.getenv("YOLO_MODEL", "yolov8m.pt")

        # YOLOモデルの初期化
        self.model = YOLO(model_path)
        self.bridge = CvBridge()

        # サブスクライバ: カメラ画像
        self.subscription = self.create_subscription(
            Image,
            '/camera/camera/color/image_raw',
            self.image_callback,
            10)

        # パブリッシャ: 検出結果
        self.publisher_ = self.create_publisher(DetectionArray, '/yolo_result', 10)
        
        self.get_logger().info(f'YOLO Node has started with model: {model_path}')

    def image_callback(self, msg):
        # ROS ImageからOpenCV形式へ変換
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # 推論の実行
        results = self.model(cv_image, verbose=False)

        # DetectionArrayメッセージの作成
        detection_array = DetectionArray()
        detection_array.header = msg.header  # 元の画像のヘッダー（Timestamp等）をコピー

        for result in results:
            boxes = result.boxes
            for box in boxes:
                det = Detection()
                
                # クラス情報とスコア
                det.class_id = int(box.cls[0])
                det.class_name = self.model.names[det.class_id]
                det.score = float(box.conf[0])
                
                # 2D Bounding Box (中心x, 中心y, 幅w, 高さh)
                # .xywh[0] は [center_x, center_y, width, height]
                xywh = box.xywh[0]
                bbox = BoundingBox2D()
                bbox.center.position.x = float(xywh[0])
                bbox.center.position.y = float(xywh[1])
                bbox.size.x = float(xywh[2])
                bbox.size.y = float(xywh[3])
                
                det.bbox = bbox
                
                # リストに追加
                detection_array.detections.append(det)

        # パブリッシュ
        self.publisher_.publish(detection_array)

def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()