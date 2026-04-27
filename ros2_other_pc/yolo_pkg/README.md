# 物体認識(YOLO)のパッケージ

## 詳細
yoloの認識をROS2用に改造したものである。  
これはリアルセンスから流れたカメラ情報 `/camera/camera/color/rect_raw`をもとにyoloで推定しそれをトピックとしてパブリッシュしている


## 起動方法

```py
# ノード1: 人検知用
ros2 run yolo_pkg yolo_result --ros-args -p model_path:='yolov8m.pt' -p output_topic:='/yolo/human'
# ノード2: 車検知用
ros2 run yolo_pkg yolo_result --ros-args -p model_path:='rcj_extra.pt' -p output_topic:='/yolo/car'
```

トピック通信
| トピック名 | メッセージの型 | メッセージ |
| --- | --- | --- |
| `/yolo_result` | [yolo_msgs/DetectionArray](https://github.com/mgonzs13/yolo_ros/blob/main/yolo_msgs/msg/DetectionArray.msg) | detections |

パブリッシュている情報が膨大で上記の内容ではおそらく役に立たない  
まず、`detections`に入っているものが認識したものがリストで出力されます‥  

これをfor構文で単体としてみるとこのようになります  
`for detect in msg.detections`として`detection`に単体の情報があるとする (モデルはyolov8mとする)
| 変数名 | 表しているもの |
| --- | --- |
| `detection.class_name` | 認識した物体の名前(bottle, personなど) |
| `detection.class_id` | 認識した物体のID(personの場合は0) |
| `detection.score` | 認識した物体の正確さ 確率% (0 ~ 1として出力) |
| `detection.bbox.center.position.x` | 認識した物体の中心のX座標(バウンディングボックスの中心X) |
| `detection.bbox.center.position.y` | 認識した物体の中心のY座標(バウンディングボックスの中心Y) |
| `detection.bbox.size.x` | バウンディングボックスのサイズ(横幅) |
| `detection.bbox.size.y` | バウンディングボックスのサイズ(縦幅) |

上記のようになっている‥  
バウンディングボックスとはyoloで認識した際に出てくる四角の枠のことである  


実装例としてこのようなものがあります  
これは人間の数を数えるモジュールです  
```py
import sys 
import rclpy
from rclpy.node import Node
from custom_msgs.srv import SetInt
from happy_interfaces.msg import PersonTrackingArray, TrackedPerson
from yolo_msgs.msg import DetectionArray, Detection

class TrackInfo(Node):
    def __init__(self):
        super().__init__('ai_node')
        self.info_get = self.create_subscription(DetectionArray, '/yolo_result', self.get_callback, 10)
        self.create_service(SetInt, 'person_number', self.result)
        
    def get_callback(self, msg):
        self.person_all = 0
        #このdetectionsに認識したすべてのものがありdetectionにそれぞれの情報がある
        for detection in msg.detections:
		        #認識したものが人ならば
            if detection.class_name == "person":
                self.person_all += 1
                #それぞれの情報
                print(f"人間発見  id: {detection.class_name}, center_x: {detection.bbox.center.position.x:.3f}, center_y: {detection.bbox.center.position.y:.3f}")

    def result(self, request, response):
        response.number = self.person_all
        return response
        
        

def main(args=None):
    rclpy.init(args=args)
    node = TrackInfo()
    print("Start!")
    rclpy.spin(node)
    node.get_logger().info("finish")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```