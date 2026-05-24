import sys
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64  # 例として角度を送る
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QSlider, QLabel, QComboBox, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from happy_manipulation_msgs.srv import ArmPose
import yaml


#ROS2の通信側のクラス
class ArmGuiNode(Node):
    def __init__(self):
        super().__init__('arm_gui_node')
        self.publisher_ = self.create_publisher(Float64, '/servo/head', 10)
        self.end = self.create_publisher()
        self.arm_sub = self.create_subscription(Float64, '/servo/head', self.callback_head, 10)
        self.arm_pose_cli = self.create_client(ArmPose, '/servo/arm')
        
        self.gui = None

    def send_command(self, value):
        msg = Float64()
        msg.data = float(value)
        self.publisher_.publish(msg)
        self.get_logger().info(f'Sent: {msg.data}')
        
    def callback_head(self, msg):
        if self.gui and not self.gui.slider.isSliderDown(): 
            self.gui.update_slider_from_ros(msg.data)
            
    def arm_pose_run(self, name):
        while not self.arm_pose_cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('サービスが利用不可です...')
            return
        req = ArmPose.Request()
        req.name = name
        future = self.arm_pose_cli.call_async(req)


#GUIのクラス
class ControlWindow(QWidget):
    def __init__(self, ros_node):
        super().__init__()
        self.ros_node = ros_node
        self.yaml_file_path = '/home/mimi/happy_ws/src/happy_manipulation/happy_manipulation/dynamixel_controller/config/mimi_specification.yaml'
        try:
            with open(self.yaml_file_path, 'r') as file:
                config = yaml.safe_load(file)
            self.poses_from_yaml = {
                k: v for k, v in config.items() 
                if isinstance(k, str) and k.endswith('_Pose')
            }
            self.ros_node.get_logger().info(f"Loaded poses: {list(self.poses_from_yaml.keys())}")
        except Exception as e:
            self.ros_node.get_logger().error(f"Failed to load YAML: {str(e)}")
            self.poses_from_yaml = {}
        
        self.init_ui()
        self.mode = 1
        self.head_value = 0

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.head_label = QLabel("0")
        
        # --- ポーズ選択エリア ---
        pose_layout = QHBoxLayout()
        self.combo_box = QComboBox()
        # YAMLから読み込んだポーズ名をセット
        pose_names = list(self.poses_from_yaml.keys())
        self.combo_box.addItems(pose_names)
        
        self.btn_pose_exec = QPushButton("ポーズ実行")
        self.btn_pose_exec.clicked.connect(self.on_pose_execute)
        
        pose_layout.addWidget(self.combo_box)
        pose_layout.addWidget(self.btn_pose_exec)
        # ----------------------

        # スライダー（既存）
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(-30, 30)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.slider_value)
        self.slider.sliderReleased.connect(self.on_slider_change)
    
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(100)
        
        # 送信ボタン（既存）
        self.btn = QPushButton("緊急停止")
        self.btn.clicked.connect(lambda: self.off_set_arm())
        
        self.btn_change = QPushButton("モード：自動制御（待機）")
        self.btn_change.setStyleSheet("background-color: #ccffcc;")
        self.btn_change.clicked.connect(self.change_mode)

        # レイアウトへの追加
        layout.addWidget(self.head_label)
        layout.addWidget(self.slider)
        layout.addLayout(pose_layout) # コンボボックスとボタンの横並びレイアウト
        layout.addWidget(self.btn_change)
        layout.addWidget(self.btn)
        
        self.setLayout(layout)
        self.setWindowTitle('Arm Controller v1.0')
        
    def on_pose_execute(self):
        """ポーズ実行ボタンが押された時の処理"""
        selected_pose = self.combo_box.currentText()
        if selected_pose:
            self.ros_node.get_logger().info(f"Service Call: {selected_pose}")
            # ROSノード側のサービス送信メソッドを呼び出す
            self.ros_node.arm_pose_run(selected_pose)
    
    def change_mode(self):
        self.mode *= -1
        if self.mode == -1:
            self.btn_change.setText("モード：マニュアル操作中")
            self.btn_change.setStyleSheet("background-color: #ffcccc;") # 薄い赤
        else:
            self.btn_change.setText("モード：自動制御（待機）")
            self.btn_change.setStyleSheet("background-color: #ccffcc;") # 薄い緑
            
    def update_slider_from_ros(self, head_value):
        self.head_value = head_value
        self.head_label.setText(str(self.head_value))
        
    def update_gui(self):
        self.slider.setValue(int(self.head_value))
        
    def off_set_arm(self):
        self.head_value = 0
        
    def slider_value(self):
        if self.mode == -1:
            self.head_value = self.slider.value()
            self.head_label.setText(str(self.head_value))
        
    def on_slider_change(self):
        if self.mode == -1:
            self.head_value = self.slider.value()
            self.ros_node.send_command(self.head_value)
        else:
            self.ros_node.get_logger().warn("マニュアルモードではありません")

def main():
    # ROS 2の初期化
    rclpy.init()
    node = ArmGuiNode()
    
    #GUI
    app = QApplication(sys.argv)
    #ROSのclass参照
    window = ControlWindow(node)
    
    # ノードにGUIのclass参照を教える（相互参照成立！）
    node.gui = window

    # 2. ROSのspinを別スレッドで回す（GUIを止めないため）
    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()

    window.show()
    
    # GUIが閉じられたら終了
    exit_code = app.exec()
    rclpy.shutdown()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()