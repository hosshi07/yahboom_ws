from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. depth_pkg: request_depth
        Node(
            package='gui_pkg',
            executable='arm_gui_node',
            name='arm_gui_node',
            output='screen'
        ),
    ])