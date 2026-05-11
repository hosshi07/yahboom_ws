# happy_mobility/base_control/base.py

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, Quaternion
import math
from rclpy.executors import MultiThreadedExecutor
# ReentrantCallbackGroup をインポート
from rclpy.callback_groups import ReentrantCallbackGroup

from jetson_interfaces.srv import Translatedist, Rotateangle

class BaseControlServer(Node):
    def __init__(self):
        super().__init__('base_control_server_node')

        # --- ▼ 1. コールバックグループを作成 ▼ ---
        # これにより、グループ内の処理が並行して実行可能になる
        self.callback_group = ReentrantCallbackGroup()
        
        # Publisherはコールバックを持たないのでグループは不要
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # --- ▼ 2. Subscriberにコールバックグループを割り当て ▼ ---
        self.odom_sub = self.create_subscription(
            Odometry, 
            '/odom', 
            self.odom_callback, 
            10,
            callback_group=self.callback_group)
            
        # --- ▼ 3. Serviceサーバーにも同じコールバックグループを割り当て ▼ ---
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

        self.current_pose = None
        self.current_yaw = 0.0
        self.odom_received = False
        
        self.get_logger().info('Base Control Server has been started. Ready to receive requests.')

    def odom_callback(self, msg):
        self.current_pose = msg.pose.pose
        self.current_yaw = self.quaternion_to_yaw(msg.pose.pose.orientation)
        if not self.odom_received:
            self.odom_received = True

    # handle_translate_request 関数（変更なし）
    def handle_translate_request(self, request, response):
        distance = request.distance
        velocity = request.velocity
        self.get_logger().info(f"Received request: move {distance:.2f}m at {velocity:.2f}m/s")
        
        while not self.odom_received and rclpy.ok():
            self.get_logger().warn('Waiting for first odometry message...')
            self.get_clock().sleep_for(rclpy.duration.Duration(seconds=0.5))
        
        if self.current_pose is None:
            self.get_logger().error('Could not get odometry. Aborting.')
            response.success = False
            return response

        start_pose = self.current_pose
        twist_msg = Twist()
        twist_msg.linear.x = abs(velocity) if distance > 0 else -abs(velocity)
        
        distance_traveled = 0.0
        loop_rate = self.create_rate(50)

        while distance_traveled < abs(distance) and rclpy.ok():
            self.cmd_vel_pub.publish(twist_msg)
            
            if self.current_pose:
                dx = self.current_pose.position.x - start_pose.position.x
                dy = self.current_pose.position.y - start_pose.position.y
                distance_traveled = math.sqrt(dx*dx + dy*dy)
            
            loop_rate.sleep()

        twist_msg.linear.x = 0.0
        self.cmd_vel_pub.publish(twist_msg)
        
        self.get_logger().info('Target distance reached. Sending response.')
        response.success = True
        return response

    # quaternion_to_yaw, normalize_angle, handle_rotate_request 関数（変更なし）
    # ... (省略) ...
    def quaternion_to_yaw(self, q: Quaternion) -> float:
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def normalize_angle(self, angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

    def handle_rotate_request(self, request, response):
        angle_deg = request.angle
        velocity_deg = request.velocity
        self.get_logger().info(f"Received request: rotate {angle_deg:.2f} deg at {velocity_deg:.2f} deg/s")

        target_angle_rad = math.radians(angle_deg)
        angular_velocity_rad = math.radians(velocity_deg)
        
        while not self.odom_received and rclpy.ok():
            self.get_logger().warn('Waiting for first odometry message...')
            self.get_clock().sleep_for(rclpy.duration.Duration(seconds=0.5))

        start_yaw = self.current_yaw
        twist_msg = Twist()
        twist_msg.angular.z = angular_velocity_rad if target_angle_rad > 0 else -angular_velocity_rad

        angle_traveled = 0.0
        loop_rate = self.create_rate(50)

        while angle_traveled < abs(target_angle_rad) and rclpy.ok():
            self.cmd_vel_pub.publish(twist_msg)
            angle_traveled = abs(self.normalize_angle(self.current_yaw - start_yaw))
            loop_rate.sleep()

        twist_msg.angular.z = 0.0
        self.cmd_vel_pub.publish(twist_msg)
        
        self.get_logger().info('Target angle reached. Sending response.')
        response.success = True
        return response

# main 関数（変更なし）
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