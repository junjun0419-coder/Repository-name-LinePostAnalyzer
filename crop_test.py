import cv2
from pathlib import Path

BASE = Path(__file__).parent
VIDEO = BASE / "Videos" / "1.mp4"
OUT = BASE / "Output" / "crop_test"

OUT.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(str(VIDEO))

if not cap.isOpened():
    print("讀不到影片，請確認 Videos/1.mp4 存在")
    raise SystemExit

fps = cap.get(cv2.CAP_PROP_FPS) or 30

# 先抓第 10 秒、第 20 秒、第 30 秒畫面測試
seconds = [10, 20, 30]

for sec in seconds:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * sec))
    ret, frame = cap.read()

    if not ret:
        print(f"第 {sec} 秒讀不到畫面")
        continue

    h, w = frame.shape[:2]

    # 先把整張畫面存起來
    full_path = OUT / f"full_{sec}s.jpg"
    cv2.imwrite(str(full_path), frame)

    # 店名區：大約抓每則留言上方文字區
    title_crop = frame[int(h * 0.18):int(h * 0.90), int(w * 0.10):int(w * 0.75)]
    title_path = OUT / f"title_area_{sec}s.jpg"
    cv2.imwrite(str(title_path), title_crop)

    # 日期區：大約抓每則留言下方時間區
    date_crop = frame[int(h * 0.25):int(h * 0.95), int(w * 0.10):int(w * 0.75)]
    date_path = OUT / f"date_area_{sec}s.jpg"
    cv2.imwrite(str(date_path), date_crop)

    print(f"已輸出第 {sec} 秒裁切圖片")

cap.release()

print("完成，請查看 Output/crop_test 資料夾")