import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2  # OpenCVを追加

# カスタムメッセージのインポート
from yolo_msgs.msg import DetectionArray, Detection, BoundingBox2D

class YoloDetectorNode(Node):
    def __init__(self):
        super().__init__('yolo_detector_node')

        # パラメータの宣言
        self.declare_parameter('model_name', 'yolo26n.pt')
        self.declare_parameter('input_topic', '/camera/camera/color/image_raw')
        self.declare_parameter('output_topic', '/yolo_result')
        self.declare_parameter('show_gui', True)  # GUI表示のON/OFF用

        model_path = self.get_parameter('model_name').get_parameter_value().string_value
        input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        self.model = YOLO(model_path)
        self.bridge = CvBridge()

        # サブスクライバ
        self.subscription = self.create_subscription(
            Image,
            input_topic,
            self.image_callback,
            10)

        # パブリッシャ
        self.publisher_ = self.create_publisher(DetectionArray, output_topic, 10)
        
        self.get_logger().info(f'YOLO Node has started. GUI: {self.get_parameter("show_gui").value}')

    def image_callback(self, msg):
        # ROS ImageからOpenCV形式へ変換
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # 推論の実行
        results = self.model(cv_image, verbose=False)

        # --- 視覚化処理 ---
        # YOLOのplot()メソッドを使うと、バウンディングボックスが描画された画像が簡単に得られます
        annotated_frame = results[0].plot()

        # ウィンドウに表示
        if self.get_parameter('show_gui').value:
            cv2.imshow("YOLO Detection", annotated_frame)
            # GUIの更新のためにwaitKeyが必要
            cv2.waitKey(1)

        # --- DetectionArrayメッセージの作成 (既存のロジック) ---
        detection_array = DetectionArray()
        detection_array.header = msg.header

        for result in results:
            boxes = result.boxes
            for box in boxes:
                det = Detection()
                det.class_id = int(box.cls[0])
                det.class_name = self.model.names[det.class_id]
                det.score = float(box.conf[0])
                
                xywh = box.xywh[0]
                bbox = BoundingBox2D()
                bbox.center.position.x = float(xywh[0])
                bbox.center.position.y = float(xywh[1])
                bbox.size.x = float(xywh[2])
                bbox.size.y = float(xywh[3])
                
                det.bbox = bbox
                detection_array.detections.append(det)

        self.publisher_.publish(detection_array)

def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # 終了時にウィンドウを閉じる
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()