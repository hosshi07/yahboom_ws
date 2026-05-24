import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

class GestureController(Node):
    def __init__(self):
        super().__init__('gesture_controller')
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT, # これを合わせる！
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        # Subscriber
        self.subscription = self.create_subscription(
            String,
            'hand_sign',
            self.listener_callback,
            qos_profile)
        
        self.enable_sub = self.create_subscription(Bool, '/hand_sign/enable', self.listener_enable, 10)
        
            
        # Publisher
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        
        self.last_pending_gesture = "NONE"
        self.current_gesture = "NONE"
        self.counter = 0
        self.threshold = 2  # 何回連続で一致したら確定するか
        self.enable = True
        
        self.get_logger().info('Gesture Controller Node has started.')

    def listener_enable(self, msg):
        self.enable = msg.data
        
    def listener_callback(self, msg):
        new_gesture = msg.data

        if self.enable:
            # --- チャタリング防止ロジック ---
            if new_gesture == self.last_pending_gesture:
                self.counter += 1
            else:
                self.counter = 0
                self.last_pending_gesture = new_gesture

            # 規定回数連続して同じポーズなら、現在のジェスチャーとして確定
            if self.counter >= self.threshold:
                if self.current_gesture != new_gesture:
                    self.current_gesture = new_gesture
                    self.get_logger().info(f'Gesture confirmed: {self.current_gesture}')
                    # --- 速度指令の作成 ---
            self.send_velocity_command()

    def send_velocity_command(self):
        twist = Twist()
        
        # ジェスチャーに応じた速度設定
        if self.current_gesture == "FORWARD":
            twist.linear.x = 0.2  # 前進
        elif self.current_gesture == "BEHIND":
            twist.linear.x = -0.2
        elif self.current_gesture == "STOP":
            twist.linear.x = 0.0
            twist.angular.z = 0.0
        elif self.current_gesture == "LEFT":
            twist.angular.z = -0.5 
        elif self.current_gesture == "RIGHT":
            twist.angular.z = 0.5 
        else:
            # WAITING...やNONEの場合は安全のために停止
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            
        self.publisher_.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = GestureController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()