import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

def choose_video():
    files = filedialog.askopenfilenames(
        title="選擇 LINE 錄影影片",
        filetypes=[("MP4 影片", "*.mp4"), ("所有檔案", "*.*")]
    )

    if not files:
        return

    listbox.delete(0, tk.END)

    for file in files:
        path = Path(file)
        size_mb = path.stat().st_size / 1024 / 1024
        listbox.insert(tk.END, f"{path.name}  |  {size_mb:.1f} MB")

    messagebox.showinfo("完成", f"已選擇 {len(files)} 支影片")

root = tk.Tk()
root.title("LINE 發文統計工具")
root.geometry("600x400")

title = tk.Label(root, text="LINE 發文統計工具", font=("Microsoft JhengHei", 20))
title.pack(pady=20)

btn = tk.Button(root, text="選擇影片", font=("Microsoft JhengHei", 14), command=choose_video)
btn.pack(pady=10)

listbox = tk.Listbox(root, font=("Microsoft JhengHei", 12), width=60, height=12)
listbox.pack(pady=10)

root.mainloop()