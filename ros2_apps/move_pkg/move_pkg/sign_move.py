import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

class GestureController(Node):
    def __init__(self):
        super().__init__('gesture_controller')
        
        # Subscriber: 手のサインを受け取る
        self.subscription = self.create_subscription(
            String,
            'hand_sign',
            self.listener_callback,
            10)
            
        # Publisher: ロボットへの速度指令
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        
        # チャタリング防止用の変数
        self.current_gesture = "NONE"
        self.last_pending_gesture = "NONE"
        self.counter = 0
        self.threshold = 3  # 何回連続で一致したら確定するか
        
        self.get_logger().info('Gesture Controller Node has started.')

    def listener_callback(self, msg):
        new_gesture = msg.data

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
        elif self.current_gesture == "STOP":
            twist.linear.x = 0.0
            twist.angular.z = 0.0
        elif self.current_gesture == "LEFT":
            #twist.angular.z = 0.5  # 左旋回
            twist.angular.z = -0.5 
        elif self.current_gesture == "RIGHT":
            #twist.angular.z = -0.5 
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