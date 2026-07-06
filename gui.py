import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
root         = tk.Tk()
root.title("TL Extractor")
root.geometry("720x750")

progress_var = tk.IntVar()
input_mode   = tk.StringVar(value="file")
card_rows    = []

main_canvas  = tk.Canvas(root)
scroll_frame = tk.Frame(main_canvas)

main_canvas.pack(side="left", fill="both", expand=True)
v_scroll = tk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
v_scroll.pack(side="right", fill="y")
main_canvas.configure(yscrollcommand=v_scroll.set)
main_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

def on_frame_configure(event):
    main_canvas.configure(scrollregion=main_canvas.bbox("all"))

scroll_frame.bind("<Configure>", on_frame_configure)

def on_mousewheel(event):
    if event.num == 4:
        main_canvas.yview_scroll(-1, "units")
    elif event.num == 5:
        main_canvas.yview_scroll(1, "units")
    else:
        main_canvas.yview_scroll(-1 * int(event.delta / 120), "units")

main_canvas.bind_all("<MouseWheel>", on_mousewheel)
main_canvas.bind_all("<Button-4>",   on_mousewheel)
main_canvas.bind_all("<Button-5>",   on_mousewheel)


# ① 入力
input_frame = tk.LabelFrame(scroll_frame, text="① 入力", padx=10, pady=10)
input_frame.pack(fill="x", padx=15, pady=10)

mode_frame = tk.Frame(input_frame)
mode_frame.pack(anchor="w", pady=5)
tk.Radiobutton(mode_frame, text="動画ファイルを使用",   variable=input_mode, value="file",    command=update_input_mode).pack(anchor="w")
tk.Radiobutton(mode_frame, text="YouTubeリンクを使用", variable=input_mode, value="youtube", command=update_input_mode).pack(anchor="w")

file_frame = tk.Frame(input_frame)
file_frame.pack(fill="x", pady=5)
file_button = tk.Button(file_frame, text="動画ファイル選択", command=select_video)
file_button.pack(side="left")
file_label = tk.Label(file_frame, text="未選択")
file_label.pack(side="left", padx=10)

yt_frame = tk.Frame(input_frame)
yt_frame.pack(fill="x", pady=5)
tk.Label(yt_frame, text="YouTube URL").pack(side="left")
youtube_entry = tk.Entry(yt_frame, width=50, state="disabled")
youtube_entry.pack(side="left", padx=10)

update_input_mode()


# ② 実行
run_frame = tk.LabelFrame(scroll_frame, text="② 実行", padx=10, pady=10)
run_frame.pack(fill="x", padx=15, pady=10)

start_button = tk.Button(run_frame, text="解析開始", width=20, height=2, command=start_analysis)
start_button.pack(pady=5)
tk.Button(run_frame, text="検知位置指定", width=20, command=define_rois).pack(pady=5)

progress_bar = ttk.Progressbar(
    run_frame, orient="horizontal", length=500,
    mode="determinate", variable=progress_var, maximum=100
)
progress_bar.pack(pady=5)

status_label = tk.Label(run_frame, text="待機中", anchor="w")
status_label.pack(fill="x")


# ③ 検知対象登録
card_frame = tk.LabelFrame(scroll_frame, text="③ 検知対象登録", padx=10, pady=10)
card_frame.pack(fill="x", padx=15, pady=10)

add_btn_frame = tk.Frame(card_frame)
add_btn_frame.pack(fill="x", pady=(0, 5))


def add_card_row():
    frame = tk.Frame(card_frame)
    frame.pack(fill="x", pady=2, after=add_btn_frame)

    name_entry = tk.Entry(frame, width=20)
    name_entry.pack(side="left", padx=5)
    name_entry.insert(0, "キャラ名")

    path_entry = tk.Entry(frame, width=40)
    path_entry.pack(side="left", padx=5)

    row_data = {"character_entry": name_entry, "card_paths": []}
    card_rows.append(row_data)

    def browse_image():
        path = filedialog.askopenfilename(
            title="カード画像を選択",
            filetypes=[("画像ファイル", "*.png *.jpg *.jpeg *.bmp")]
        )
        if not path:
            return
        cropped_path = open_crop_window(path)
        if cropped_path:
            path_entry.delete(0, tk.END)
            path_entry.insert(0, cropped_path)
            row_data["card_paths"].append(cropped_path)

    def delete_row():
        frame.destroy()
        if row_data in card_rows:
            card_rows.remove(row_data)

    tk.Button(frame, text="参照", command=browse_image).pack(side="left", padx=5)
    tk.Button(frame, text="削除", command=delete_row).pack(side="left", padx=5)


tk.Button(add_btn_frame, text="行を追加", command=add_card_row).pack(pady=5)


# ④ 結果
result_frame = tk.LabelFrame(scroll_frame, text="④ 結果", padx=10, pady=10)
result_frame.pack(fill="both", expand=True, padx=15, pady=10)

tree_frame  = tk.Frame(result_frame)
tree_frame.pack(fill="both", expand=False)

tree_scroll = tk.Scrollbar(tree_frame)
tree_scroll.pack(side="right", fill="y")

columns = ("time", "cost", "character")
tree = ttk.Treeview(
    tree_frame, columns=columns, show="headings",
    yscrollcommand=tree_scroll.set, height=15
)
tree_scroll.config(command=tree.yview)

tree.heading("time",      text="時間")
tree.heading("cost",      text="コスト")
tree.heading("character", text="キャラ名")
tree.column("time",      width=130)
tree.column("cost",      width=80,  anchor="center")
tree.column("character", width=250)
tree.pack(fill="both", expand=True, pady=5)

tk.Button(result_frame, text="CSVで保存", width=20, height=2, command=export_csv).pack(pady=5)
