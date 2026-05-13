from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='yahboomcar_bringup',      
            executable='Mcnamu_driver_M1', 
            name='rosmaster_bringup'                
        ),
        Node(
            package='move_pkg',
            executable='base_control',
            name='base_control',
        )
    ])