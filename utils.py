import os
import cv2
import numpy as np
import yt_dlp
import uuid
import tempfile

# ============================================================
# 画像読み込み
# ============================================================

def imread_unicode(path):
    try:
        data = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"[ERROR] imread_unicode failed for {path}: {e}")
        return None


# ============================================================
# ユーティリティ関数
# ============================================================

def extract_roi(frame, roi):
    x1, y1, x2, y2 = roi
    return frame[y1:y2, x1:x2]


def get_roi_size(roi):
    x1, y1, x2, y2 = roi
    return (x2 - x1, y2 - y1)


def format_time_mmss(frame_idx, fps):
    total_sec = frame_idx / fps
    m  = int(total_sec // 60)
    s  = int(total_sec % 60)
    ms = int((total_sec - int(total_sec)) * 1000)
    return f"{m:02d}:{s:02d}.{ms:03d}"


# ============================================================
# YouTube ダウンロード
# ============================================================

def download_youtube(url, progress_hook_cb):
    unique_name = f"tl_extractor_{uuid.uuid4().hex}.%(ext)s"
    opts = {
        'format'         : 'bestvideo+bestaudio/best',
        'outtmpl'        : os.path.join(tempfile.gettempdir(), unique_name),
        'quiet'          : False,
        'no_warnings'    : False,
        'progress_hooks' : [progress_hook_cb],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info     = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename