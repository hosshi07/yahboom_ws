import threading
import tkinter as tk
from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy


#GUIとROS2の通信のspinミスマッチがこのムズさ
class CommanderNode(Node):

    def __init__(self):
        super().__init__("commander_node")
        self.gui = None  # 後からGUIのインスタンスをセットする
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT, # これを合わせる！
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # パブリッシャー
        self.publisher_ = self.create_publisher(Bool, "hand_sign/enable", 10)
        self.cmd_pub = self.create_publisher(Twist, "/cmd_val", 10)

        # サブスクライバー
        self.subscription = self.create_subscription(
            String, "hand_sign", self.hand_sign_callback, qos_profile
        )

        self.get_logger().info("ROS2 Node has been started.")

    def set_gui(self, gui):
        """GUIのインスタンスを登録するシンプルなメソッド"""
        self.gui = gui

    def publish_message(self, state):
        msg = Bool()
        twist = Twist()
        msg.data = state
        self.publisher_.publish(msg)
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.cmd_pub.publish(twist)
        self.get_logger().info(f"Published: '{msg.data}'")

    def hand_sign_callback(self, msg):
        """トピックを受け取ったら、登録されたGUIの更新関数を呼び出す"""
        if self.gui is not None:
            # Tkinterの画面更新は「.after」を使うとスレッド安全で確実です
            self.gui.root.after(0, self.gui.update_direction_ui, msg.data)


class AppGUI:

    def __init__(self, root, node):
        self.root = root
        self.node = node

        # --- 【改善】大きくなった矢印に合わせてウィンドウサイズを最適化 ---
        self.root.title("ROSMASTERコマンダー")
        self.root.geometry("600x320")  # 縦横を少し広げてゆとりを持たせました

        # 矢印と文字の対応マップ
        self.arrow_map = {
            "FORWARD": ("▲", "#2ECC71"),
            "LEFT": ("◀", "#3498DB"),
            "RIGHT": ("▶", "#9B59B6"),
            "BEHIND": ("▼", "#E74C3C"),
            "STOP": ("■", "#7F8C8D"),
        }

        # --- 画面レイアウトの分割 ---
        # 左側フレーム（ステータス表示用）
        self.left_frame = tk.Frame(root)
        self.left_frame.pack_propagate(False)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # 右側フレーム（操作ボタン用）
        self.right_frame = tk.Frame(root)
        self.right_frame.pack_propagate(False)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        # --- 左側：巨大矢印UI（配置をスッキリ整理） ---
        self.status_title = tk.Label(
            self.left_frame, text="認識されたサイン", font=("Arial", 12, "bold")
        )
        self.status_title.pack(pady=(20, 0))  # 上部に少し余白

        # 160サイズの巨大矢印をきれいに収める
        self.arrow_label = tk.Label(
            self.left_frame, text="■", font=("Arial", 140), fg="#7F8C8D"
        )
        self.arrow_label.pack(expand=True)  # フレーム中央に自動配置

        self.text_label = tk.Label(
            self.left_frame, text="WAITING", font=("Arial", 16, "bold"), fg="#7F8C8D"
        )
        self.text_label.pack(pady=(0, 20))  # 下部に少し余白

        # --- 右側：操作ボタンUI（中央に綺麗に並ぶように調整） ---
        self.right_container = tk.Frame(self.right_frame)
        self.right_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.label = tk.Label(
            self.right_container, text="ハンドコントローラ", font=("Arial", 14, "bold")
        )
        self.label.pack(pady=(0, 15))

        self.button = tk.Button(
            self.right_container,
            text="RUNNING",
            command=self.on_button_click,
            bg="#E99242",
            fg="white",
            font=("Arial", 12, "bold"),
            width=18,
            height=2,  # ボタンを少し押しやすく厚みを持たせました
        )
        self.button.pack(pady=10)

        self.button_off = tk.Button(
            self.right_container,
            text="WAITING(緊急停止)",
            command=self.on_button_off_click,
            bg="#4244C5",
            fg="white",
            font=("Arial", 12, "bold"),
            width=18,
            height=2,
        )
        self.button_off.pack(pady=5)

    def on_button_click(self):
        self.node.publish_message(True)

    def on_button_off_click(self):
        self.node.publish_message(False)
        self.update_direction_ui("STOP")

    def update_direction_ui(self, direction):
        """受け取ったトピックを元に表示を更新"""
        arrow, color = self.arrow_map.get(direction, self.arrow_map["STOP"])
        self.arrow_label.config(text=arrow, fg=color)
        self.text_label.config(text=direction, fg=color)


def ros2_spin(node):
    rclpy.spin(node)


def main(args=None):
    rclpy.init(args=args)

    # 1. まず普通にROS2ノードを作ります（激ムズlambdaを廃止！）
    node = CommanderNode()

    # 2. ROS2の通信スレッドを開始
    ros_thread = threading.Thread(target=ros2_spin, args=(node,), daemon=True)
    ros_thread.start()

    # 3. GUIを起動し、ノードを渡す
    root = tk.Tk()
    app = AppGUI(root, node)

    # 4. ノード側に「このGUI画面を更新してね」と教えてあげる
    node.set_gui(app)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()