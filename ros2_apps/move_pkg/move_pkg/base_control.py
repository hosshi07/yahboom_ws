import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math
import time # 時間計測のために追加
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup

from jetson_interfaces.srv import Translatedist, Rotateangle

class BaseControlServer(Node):
    def __init__(self):
        super().__init__('base_control_server_node')

        self.callback_group = ReentrantCallbackGroup()
        
        # Publisherはそのまま
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Serviceサーバーの設定
        self.translate_srv = self.create_service(
            Translatedist, 
            'translate_dist', 
            self.handle_translate_request,
            callback_group=self.callback_group)
        self.rotate_srv = self.create_service(
            Rotateangle, 
            'rotate_angle', 
            self.handle_rotate_request,
            callback_group=self.callback_group)

        self.get_logger().info('Base Control Server (Time-based) has been started.')

    def handle_translate_request(self, request, response):
        distance = request.distance
        velocity = abs(request.velocity) # 速度は正の値として扱う
        
        # 計算: 時間 = 距離 / 速度
        duration = abs(distance) / velocity
        
        self.get_logger().info(f"Moving {distance}m at {velocity}m/s (Duration: {duration:.2f}s)")

        twist_msg = Twist()
        twist_msg.linear.x = velocity if distance > 0 else -velocity
        
        # 移動実行
        start_time = self.get_clock().now()
        while (self.get_clock().now() - start_time).nanoseconds / 1e9 < duration:
            self.cmd_vel_pub.publish(twist_msg)
            time.sleep(0.02) # 50Hz相当のループ

        # 停止
        twist_msg.linear.x = 0.0
        self.cmd_vel_pub.publish(twist_msg)
        
        response.success = True
        return response

    def handle_rotate_request(self, request, response):
        angle_deg = request.angle
        velocity_deg = abs(request.velocity)
        
        # 計算: 時間 = 角度 / 角速度
        duration = abs(angle_deg) / velocity_deg
        
        self.get_logger().info(f"Rotating {angle_deg}deg at {velocity_deg}deg/s (Duration: {duration:.2f}s)")

        twist_msg = Twist()
        # 度数法からラジアンに変換してセット
        angular_vel_rad = math.radians(velocity_deg)
        twist_msg.angular.z = angular_vel_rad if angle_deg > 0 else -angular_vel_rad
        
        # 回転実行
        start_time = self.get_clock().now()
        while (self.get_clock().now() - start_time).nanoseconds / 1e9 < duration:
            self.cmd_vel_pub.publish(twist_msg)
            time.sleep(0.02)

        # 停止
        twist_msg.angular.z = 0.0
        self.cmd_vel_pub.publish(twist_msg)
        
        response.success = True
        return response

def main(args=None):
    rclpy.init(args=args)
    node = BaseControlServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()