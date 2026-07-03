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

date_pattern = re.compile(r"(\d{1,2})/(\d{1,2})")

records = []

def fix_store_name(text):
    text = text.replace(" ", "").replace("店", "")
    matches = get_close_matches(text, stores, n=1, cutoff=0.55)
    return matches[0] if matches else None

def find_date(text):
    m = date_pattern.search(text)
    if m:
        return f"{int(m.group(1))}/{int(m.group(2))}"

    m2 = re.search(r"0?(\d{1,2})(\d{2})", text)
    if m2:
        month = int(m2.group(1))
        day = int(m2.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{month}/{day}"

    return None

for video_path in VIDEOS_DIR.glob("*.mp4"):
    print(f"分析影片：{video_path.name}")

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * 1)  # 每 1 秒擷取一次

    frame_no = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_no % frame_interval == 0:
            results = reader.readtext(frame, detail=0)
            texts = [t.strip() for t in results if t.strip()]
            joined = " ".join(texts)

            date = None
            store = None

            for t in texts:
                if date is None:
                    date = find_date(t)

                if store is None:
                    fixed = fix_store_name(t)
                    if fixed:
                        store = fixed

            if date and store:
                records.append({
                    "影片": video_path.name,
                    "日期": date,
                    "店名": store,
                    "OCR文字": joined
                })
                print(date, store)

        frame_no += 1

    cap.release()

df = pd.DataFrame(records)

if df.empty:
    print("沒有辨識到資料")
    exit()

df = df.drop_duplicates(subset=["日期", "店名"])

dates = sorted(df["日期"].unique(), key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))

daily_rows = []
posted_rows = []
missing_rows = []
matrix_rows = []

for date in dates:
    posted = sorted(df[df["日期"] == date]["店名"].unique())
    missing = [s for s in stores if s not in posted]

    daily_rows.append({
        "日期": date,
        "有發文店數": len(posted),
        "未發文店數": len(missing),
        "總店數": len(stores)
    })

    for s in posted:
        posted_rows.append({"日期": date, "店名": s})

    for s in missing:
        missing_rows.append({"日期": date, "店名": s})

for s in stores:
    row = {"店名": s}
    for date in dates:
        row[date] = "✓" if s in list(df[df["日期"] == date]["店名"]) else "✗"
    matrix_rows.append(row)

output_file = OUTPUT_DIR / "LINE發文統計.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    pd.DataFrame(daily_rows).to_excel(writer, sheet_name="每日統計", index=False)
    pd.DataFrame(posted_rows).to_excel(writer, sheet_name="每日有發文店家", index=False)
    pd.DataFrame(missing_rows).to_excel(writer, sheet_name="每日未發文店家", index=False)
    pd.DataFrame(matrix_rows).to_excel(writer, sheet_name="店家每日表", index=False)
    df.to_excel(writer, sheet_name="原始辨識紀錄", index=False)

print(f"完成！Excel 已輸出：{output_file}")