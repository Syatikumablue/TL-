import cv2
import numpy as np
import os
import config
from utils import imread_unicode

# ============================================================
# 数字テンプレート生成・ロード（タイマー・コスト共用）
# ============================================================

def generate_digit_templates(folder_name, target_height=24):
    templates = {}
    chars = [str(i) for i in range(10)]
    if folder_name in ["タイマー", "timer"]:
        chars += [":", "."]
    
    found_dir = None
    for d in [folder_name, folder_name.lower()]:
        if os.path.exists(d):
            found_dir = d
            break

    for char in chars:
        filename = f"{char}.png"
        if char == ":": filename = "colon.png"
        if char == ".": filename = "dot.png"
        
        path = os.path.join(found_dir, filename) if found_dir else None
        
        # 1. 外部画像がある場合
        if path and os.path.exists(path):
            img = imread_unicode(path)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                templates[char] = cv2.Canny(gray, 50, 150)
                continue
        
        # 2. フォールバック（自動生成）
        canvas = np.zeros((target_height * 2, target_height * 2), dtype=np.uint8)
        cv2.putText(canvas, char, (int(target_height * 0.2), int(target_height * 1.5)),
                    cv2.FONT_HERSHEY_DUPLEX, target_height / 30.0, 255, thickness=2, lineType=cv2.LINE_AA)
        pts = np.argwhere(canvas > 0)
        if pts.size > 0:
            y_min, x_min = pts.min(axis=0)
            y_max, x_max = pts.max(axis=0)
            char_crop = canvas[y_min:y_max+1, x_min:x_max+1]
            scale = target_height / char_crop.shape[0]
            char_resized = cv2.resize(char_crop, (int(char_crop.shape[1] * scale), target_height), interpolation=cv2.INTER_CUBIC)
            templates[char] = cv2.Canny(char_resized, 50, 150)
            
    return templates

def detect_integer_from_roi(roi_img, digit_templates, threshold=config.COST_MATCH_THRESH):
    if roi_img is None or roi_img.size == 0: return 0
    
    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    found_digits = []
    
    for digit, templ in digit_templates.items():
        if digit in [":", "."]: continue
        res = cv2.matchTemplate(edges, templ, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            found_digits.append((pt[0], digit))
            
    found_digits.sort(key=lambda x: x[0])
    cleaned = []
    for d in found_digits:
        if not cleaned or abs(d[0] - cleaned[-1][0]) > 5:
            cleaned.append(d)
    return int("".join([c[1] for c in cleaned])) if cleaned else 0

def detect_cost_fill_ratio(cost_bar_roi):
    if cost_bar_roi is None or cost_bar_roi.size == 0: return 0.0
    hsv = cv2.cvtColor(cost_bar_roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([80, 50, 50]), np.array([130, 255, 255]))
    col_sums = np.sum(mask, axis=0)
    filled = np.where(col_sums > 0)[0]
    return float(filled[-1] / cost_bar_roi.shape[1]) if len(filled) > 0 else 0.0

def load_card_template_matching(path, roi_size=None):
    raw = imread_unicode(path)
    if raw is None: return None
    if roi_size is not None:
        target_w, target_h = roi_size
        orig_h, orig_w = raw.shape[:2]
        scale = min(target_w / orig_w, target_h / orig_h)
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        resized = cv2.resize(raw, (new_w, new_h), interpolation=cv2.INTER_AREA)
        template_img = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        dy, dx = (target_h - new_h) // 2, (target_w - new_w) // 2
        template_img[dy:dy+new_h, dx:dx+new_w] = resized
    else:
        template_img = raw
    return template_img

def match_card_template(roi_color, template_img):
    try:
        res = cv2.matchTemplate(roi_color, template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return float(max_val)
    except cv2.error: return 0.0

def detect_card(slot_img, card_registry, threshold=config.MATCH_THRESH):
    lab = cv2.cvtColor(slot_img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    slot_normalized = cv2.cvtColor(cv2.merge((cl,a,b)), cv2.COLOR_LAB2BGR)
    best_card, best_score = None, -1.0
    for card in card_registry.all_cards():
        if card.template is None: continue
        score = match_card_template(slot_normalized, card.template)
        if score > best_score:
            best_score = score
            best_card  = card
    return (best_card, best_score) if best_score >= threshold else (None, best_score)

def detect_game_timer(timer_img, digit_templates):
    if timer_img is None or timer_img.size == 0: return None
    gray = cv2.cvtColor(timer_img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    found_chars = []
    for char, templ in digit_templates.items():
        res = cv2.matchTemplate(edges, templ, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= config.TIMER_MATCH_THRESH)
        for pt in zip(*loc[::-1]):
            found_chars.append((pt[0], char, res[pt[1], pt[0]]))
    found_chars.sort(key=lambda x: x[0])
    cleaned = []
    for item in found_chars:
        if not cleaned or abs(item[0] - cleaned[-1][0]) > 8:
            cleaned.append(item)
    res_str = "".join([c[1] for c in cleaned])
    return res_str if ":" in res_str and len(res_str) >= 4 else None