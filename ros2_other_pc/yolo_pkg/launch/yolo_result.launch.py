import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # 引数の宣言（コマンドラインから変更可能にする）
    model_name_arg = DeclareLaunchArgument(
        'model_name',
        default_value='yolov8m.pt',
        description='Name or path of the YOLO model'
    )

    input_topic_arg = DeclareLaunchArgument(
        'input_topic',
        default_value='/camera/camera/color/image_raw',
        description='Topic name for input camera images'
    )

    output_topic_arg = DeclareLaunchArgument(
        'output_topic',
        default_value='/yolo_result',
        description='Topic name for detection results'
    )

    # ノードの設定
    yolo_node = Node(
        package='yolo_pkg',
        executable='yolo_result',
        name='yolo_result',
        parameters=[{
            'model_name': LaunchConfiguration('model_name'),
            'input_topic': LaunchConfiguration('input_topic'),
            'output_topic': LaunchConfiguration('output_topic'),
        }],
        output='screen'
    )

    return LaunchDescription([
        model_name_arg,
        input_topic_arg,
        output_topic_arg,
        yolo_node
    ])