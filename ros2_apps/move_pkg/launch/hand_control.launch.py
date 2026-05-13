from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
                Node(
            package='camera_info',
            executable='camera_get',
            name='camera_node',
        ),
        Node(
            package='recognition_pkg',      
            executable='hand_sign_node', 
            name='hand_sign'                
        ),
        Node(
            package='move_pkg',
            executable='sign_move',
            name='sing_getter',
        )
    ])