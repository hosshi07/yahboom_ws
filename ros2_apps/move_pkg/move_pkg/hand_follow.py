import threading
from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from jetson_interfaces.msg import Coordinates
from yahboomcar_msgs.msg import ServoControl
# QoS
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy




GAIN_X = 7.0
GAIN_Y = 7.0


class FollowNode(Node):

    def __init__(self):
        super().__init__("commander_node")
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.create_subscription(Coordinates, '/hand_coodinate', self.callback, qos_profile)
        self.servo_pub = self.create_publisher(ServoControl, '/Servo', 10)
        self.current_pan = 90.0 
        self.current_tilt = 45
        init_msg = ServoControl()
        init_msg.s1 = self.current_pan
        init_msg.s2 = self.current_tilt
        self.servo_pub.publish(init_msg)
        self.get_logger().info("ROS2 Node has been started.")
        
    def track_hand(self, mediapipe_x, mediapipe_y):
        error_x = -(mediapipe_x - 0.5)
        error_y = mediapipe_y - 0.5

        self.current_pan += error_x * GAIN_X
        
        self.current_tilt += error_y * GAIN_Y
        
        self.current_pan = max(0.0, min(180.0, self.current_pan))
        self.current_tilt = max(0.0, min(90.0, self.current_tilt)) 
        
        return int(self.current_pan), int(self.current_tilt)

    def callback(self, msg):
        x = msg.x
        y = msg.y
        pan, tilt = self.track_hand(x, y)
        msg = ServoControl()
        msg.s1 = pan
        msg.s2 = tilt
        self.servo_pub.publish(msg)
        



def main(args=None):
    rclpy.init(args=args)

    node = FollowNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()