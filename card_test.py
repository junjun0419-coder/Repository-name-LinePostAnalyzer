import cv2
from pathlib import Path

BASE = Path(__file__).parent
VIDEO = BASE / "Videos" / "1.mp4"
OUT = BASE / "Output" / "card_test"
OUT.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(str(VIDEO))
fps = cap.get(cv2.CAP_PROP_FPS) or 30

seconds = [10, 20, 30]

for sec in seconds:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * sec))
    ret, frame = cap.read()
    if not ret:
        continue

    h, w = frame.shape[:2]

    # 只抓 LINE 留言區，不抓上方狀態列與下方輸入框
    area = frame[int(h * 0.12):int(h * 0.88), int(w * 0.05):int(w * 0.80)]

    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)

    # 找灰色留言卡片
    mask = cv2.inRange(gray, 25, 80)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    result = area.copy()
    card_count = 0

    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)

        if cw > 180 and ch > 80:
            card_count += 1
            cv2.rectangle(result, (x, y), (x + cw, y + ch), (0, 255, 0), 3)

            card = area[y:y+ch, x:x+cw]
            cv2.imwrite(str(OUT / f"card_{sec}s_{card_count}.jpg"), card)

    cv2.imwrite(str(OUT / f"detected_{sec}s.jpg"), result)
    print(f"{sec} 秒：偵測到 {card_count} 張卡片")

cap.release()
print("完成，請查看 Output/card_test")