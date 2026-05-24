import cv2
import mediapipe as mp
import math


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,        # 動画ストリームとして処理（これ重要）
    max_num_hands=1,                # 認識する手は「1つ」に制限（計算量が半減！）
    model_complexity=0,             # 【超重要】0:最速, 1:標準。0にすると劇的に軽くなります
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils


# def get_gesture(landmarks):
#     # 8: 人差し指先端, 9: 中指付け根(手の中心に近い)
#     index_tip = landmarks[8]
#     middle_mcp = landmarks[9] 
    
#     # 指の立ち状態（簡易版：人差し指と中指だけ見る）
#     index_up = landmarks[8].y < landmarks[6].y
#     middle_up = landmarks[12].y < landmarks[10].y
#     ring_up = landmarks[16].y < landmarks[14].y

#     # 停止: パー
#     if index_up and middle_up and ring_up:
#         return "STOP"

#     # 前進: 人差し指だけ立っていて、かつ左右に振れていない
#     if index_up and not middle_up:
#         # X座標の差分で判定
#         diff_x = index_tip.x - middle_mcp.x
        
#         if diff_x > 0.05: # しきい値を調整
#             return "RIGHT"
#         elif diff_x < -0.05:
#             return "LEFT"
#         else:
#             return "FORWARD"

#     return "WAITING..."

# import math

# def get_gesture(landmarks):
#     # ポイント抽出
#     idx_tip = landmarks[8]   # 人差し指先端
#     idx_mcp = landmarks[5]   # 人差し指付け根
#     rng_tip = landmarks[16]  # 薬指先端
#     rng_mcp = landmarks[13]  # 薬指付け根
#     wrist = landmarks[0]     # 手首
#     mid_mcp = landmarks[9]   # 中指付け根

#     # --- STEP 1: 距離による「薬指の伸び」判定 ---
#     # 1. 手のひらのサイズを基準（分母）にする (手首から中指付け根までの距離)
#     palm_size = math.sqrt((mid_mcp.x - wrist.x)**2 + (mid_mcp.y - wrist.y)**2)
    
#     # 2. 薬指の現在の長さ（先端から付け根まで）を計算
#     ring_finger_len = math.sqrt((rng_tip.x - rng_mcp.x)**2 + (rng_tip.y - rng_mcp.y)**2)
    
#     # 3. 比率を計算 (手のひらに対して薬指がどのくらい伸びているか)
#     # 概ね 0.9以上なら「伸びている」、0.5以下なら「握っている」となります
#     ring_extension_ratio = ring_finger_len / palm_size if palm_size > 0 else 0

#     # デバッグ用に比率を表示させたい場合はここ（オプション）
#     # self.get_logger().info(f"Ring ratio: {ring_extension_ratio:.2f}")

#     # 薬指がしっかり伸びている（比率が大きい）ならSTOP
#     # このしきい値(0.8)を調整することで、STOPの「固さ」を自由に変えられます
#     if ring_extension_ratio > 0.8:
#         return "STOP"

#     # --- STEP 2: 移動の判定 (薬指を曲げている時のみ) ---
#     if idx_tip.y < idx_mcp.y:
#         dx = idx_tip.x - idx_mcp.x
#         dy = idx_tip.y - idx_mcp.y
#         deg = math.degrees(math.atan2(-dy, dx))
#         cv2.putText(debug_image, f"deg: {int(deg)}", (10, 150),
#                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 111, 0), 2, cv2.LINE_AA)
#         # 以前確立した完璧な角度判定
#         if deg > 130:
#             return "LEFT"
#         elif deg < 55:
#             return "RIGHT"
#         else:
#             return "FORWARD"

#     return "WAITING..."



def get_gesture(landmarks):
    idx_tip = landmarks[8]   # 人差し指先端
    idx_mcp = landmarks[5]   # 人差し指付け根
    rng_tip = landmarks[16]  # 薬指先端
    rng_mcp = landmarks[13]  # 薬指付け根
    wrist = landmarks[0]     # 手首
    mid_mcp = landmarks[9]   # 中指付け根

    #共通の基準
    palm_size = math.sqrt((mid_mcp.x - wrist.x)**2 + (mid_mcp.y - wrist.y)**2)
    if palm_size == 0: return "WAITING..."

    # 薬指の長さでSTOP判定
    ring_len = math.sqrt((rng_tip.x - rng_mcp.x)**2 + (rng_tip.y - rng_mcp.y)**2)
    if (ring_len / palm_size) > 0.8:
        return "STOP"

    # y座標の比較をやめ、人差し指が「伸びているか」を見ます
    idx_len = math.sqrt((idx_tip.x - idx_mcp.x)**2 + (idx_tip.y - idx_mcp.y)**2)
    
    # 手のひらに対して人差し指が一定以上の長さ（例: 0.7以上）なら操作中
    if (idx_len / palm_size) > 0.7:
        dx = idx_tip.x - idx_mcp.x
        dy = idx_tip.y - idx_mcp.y
        deg = math.degrees(math.atan2(-dy, dx))
        if deg < 0:
            deg += 360
        cv2.putText(debug_image, f"deg: {int(deg)}", (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        if 150 < deg <= 230:
            return "LEFT"
        elif deg < 35 or deg >= 300:
            return "RIGHT"
        elif 231 < deg < 299:
            return "BEHYND"
        else:
            return "FORWARD"

    # 指を曲げている（グーの状態）
    return "WAITING..."
cap = cv2.VideoCapture(0)

print("プログラムを開始します。'q'キーで終了します。")

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    # 鏡のように表示するため左右反転し、BGRからRGBに変換
    image = cv2.flip(image, 1)
    debug_image = image.copy()
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # MediaPipeで検出
    results = hands.process(image_rgb)

    gesture_text = "NONE"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # ランドマークを描画
            mp_draw.draw_landmarks(debug_image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            landmarks = results.multi_hand_landmarks[0].landmark
            diff_x = landmarks[8].x - landmarks[9].x
            cv2.putText(debug_image, f"DiffX: {diff_x:.3f}", (10, 100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)              
            # ジェスチャー判定
            gesture_text = get_gesture(hand_landmarks.landmark)

    # 判定結果を画面に表示
    cv2.putText(debug_image, f"Gesture: {gesture_text}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.imshow('Gesture Control Feed', debug_image)

    # 'q' キーでループを抜ける
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()