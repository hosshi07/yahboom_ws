import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # 1. 自分のパッケージ(move_pkg)のインストールパスを取得
    pkg_dir = get_package_share_directory('move_pkg')

    # 2. hand_control.launch.py を読み込む設定
    launch_hand = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'hand_control.launch.py')
        )
    )

    # 3. robot_move.launch.py を読み込む設定
    launch_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'robot_move.launch.py')
        )
    )

    # 4. 両方をリストに入れて実行
    return LaunchDescription([
        launch_hand,
        launch_robot
    ])