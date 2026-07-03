import cv2
import re
import pandas as pd
import easyocr
from pathlib import Path
from difflib import get_close_matches

BASE = Path(__file__).parent
VIDEOS_DIR = BASE / "Videos"
OUTPUT_DIR = BASE / "Output"
STORES_FILE = BASE / "stores.txt"

OUTPUT_DIR.mkdir(exist_ok=True)

stores = [s.strip() for s in STORES_FILE.read_text(encoding="utf-8").splitlines() if s.strip()]
reader = easyocr.Reader(["ch_tra", "en"], gpu=False)

records = []

def fix_store_name(text):
    text = text.replace(" ", "").replace("　", "")
    text = text.replace("店", "").replace("無誤", "")
    text = re.sub(r"[0-9０-９/:\(\)（）上午下午]", "", text)
    matches = get_close_matches(text, stores, n=1, cutoff=0.5)
    return matches[0] if matches else None

def find_line_date(text):
    text = text.replace(" ", "")
    m = re.search(r"(\d{1,2})/(\d{1,2})", text)
    if m:
        month = int(m.group(1))
        day = int(m.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{month}/{day}"
    return None

def ocr_text(image):
    result = reader.readtext(image, detail=0)
    return " ".join([r.strip() for r in result if r.strip()])

for video_path in sorted(VIDEOS_DIR.glob("*.mp4")):
    print(f"分析影片：{video_path.name}")

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    interval = max(1, int(fps * 0.7))

    frame_no = 0
    last_pair = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_no % interval == 0:
            h, w = frame.shape[:2]

            # 依照你的 LINE 畫面位置裁切：
            # 上半部：抓留言標題文字，例如 0531林口 (2) 無誤
            # 下半部：抓 LINE 日期，例如 6/1 上午11:02
            title_area = frame[int(h * 0.15):int(h * 0.88), int(w * 0.10):int(w * 0.75)]
            date_area = frame[int(h * 0.25):int(h * 0.95), int(w * 0.10):int(w * 0.75)]

            title_text = ocr_text(title_area)
            date_text = ocr_text(date_area)

            store = None
            date = None

            # 店名從標題文字找
            for part in re.split(r"\s+", title_text):
                fixed = fix_store_name(part)
                if fixed:
                    store = fixed
                    break

            # 日期從 LINE 下面時間找
            for part in re.split(r"\s+", date_text):
                d = find_line_date(part)
                if d:
                    date = d
                    break

            if date and store:
                pair = (date, store)

                if pair != last_pair:
                    records.append({
                        "日期": date,
                        "店名": store,
                        "影片": video_path.name,
                        "標題OCR": title_text,
                        "日期OCR": date_text
                    })
                    print(date, store)

                last_pair = pair

        frame_no += 1

    cap.release()

df = pd.DataFrame(records)

if df.empty:
    print("沒有辨識到資料，可能需要調整裁切區域")
    raise SystemExit

df = df.drop_duplicates(subset=["日期", "店名"])

dates = sorted(df["日期"].unique(), key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))

daily_summary = []
posted_rows = []
missing_rows = []
matrix_rows = []

for date in dates:
    posted = sorted(df[df["日期"] == date]["店名"].unique())
    missing = [s for s in stores if s not in posted]

    daily_summary.append({
        "日期": date,
        "有發文店數": len(posted),
        "未發文店數": len(missing),
        "有發文店家": "、".join(posted),
        "未發文店家": "、".join(missing)
    })

    for s in posted:
        posted_rows.append({"日期": date, "店名": s})

    for s in missing:
        missing_rows.append({"日期": date, "店名": s})

for s in stores:
    row = {"店名": s}
    for date in dates:
        row[date] = "✓" if s in set(df[df["日期"] == date]["店名"]) else "✗"
    matrix_rows.append(row)

output_file = OUTPUT_DIR / "LINE發文統計_V2.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    pd.DataFrame(daily_summary).to_excel(writer, sheet_name="每日統計", index=False)
    pd.DataFrame(posted_rows).to_excel(writer, sheet_name="每日有發文店家", index=False)
    pd.DataFrame(missing_rows).to_excel(writer, sheet_name="每日未發文店家", index=False)
    pd.DataFrame(matrix_rows).to_excel(writer, sheet_name="店家每日表", index=False)
    df.to_excel(writer, sheet_name="原始辨識紀錄", index=False)

print(f"完成！Excel 已輸出：{output_file}")