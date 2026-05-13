import cv2
import mediapipe as mp


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1, 
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

def get_gesture(landmarks):
    # 指が立っているかどうかのリスト (親指以外)
    fingers = []
    # 各指の先端(TIP)と第2関節(PIP)のy座標を比較
    # 8:人差し指, 12:中指, 16:薬指, 20:小指
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        fingers.append(landmarks[tip].y < landmarks[pip].y)

    # 1. 停止 (パー): 全ての指が立っている
    if all(fingers):
        return "STOP"
    
    # 2. 前進 (人差し指だけ): 人差し指が立っていて、他が寝ている
    if fingers[0] and not any(fingers[1:]):
        return "FORWARD"

    # 3. 右・左: 人差し指の先端と手首(landmark 0)のX座標の比較
    if landmarks[8].x > landmarks[0].x + 0.1:
        return "RIGHT"
    elif landmarks[8].x < landmarks[0].x - 0.1:
        return "LEFT"
        
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