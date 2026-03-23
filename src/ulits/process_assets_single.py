import cv2
import numpy as np
import os

# 定义专用文件夹路径
SPECIAL_DIR = "assets/images/special"
os.makedirs(SPECIAL_DIR, exist_ok=True)

def matted_png_solid_fill(source_path, output_filename, target_size=128):
    """专门针对 JPG 或带白底 PNG 进行抠图和居中处理"""
    # 1. 加载图片
    img = cv2.imread(source_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"❌ 找不到图片: {source_path}")
        return

    print(f"正在处理素材: {source_path}...")

    # 2. 如果是 3 通道 (JPG)，则不需要分离 Alpha，直接处理白底
    if img.shape[2] == 3:
        b, g, r = cv2.split(img)
        # 将白底转为全黑，提取蒙版
        _, thresh = cv2.threshold(b, 250, 255, cv2.THRESH_BINARY_INV)
        # 3通道合成支持Alpha的4通道
        img = cv2.merge([b, g, r, thresh])

    # 3. 分离 RGBA 
    b, g, r, alpha = cv2.split(img)

    # 4. 【核心优化】：对不透明区域进行轮廓检测
    contours, _ = cv2.findContours(alpha, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("❌ 警告：未找到有效物体，无法安全抠图。")
        return
        
    c = max(contours, key=cv2.contourArea)
    x, y, cw, ch = cv2.boundingRect(c)

    # 5. 【实心填充抠图法】：创建一个黑蒙版，并在最大轮廓内部强行画满纯白
    solid_mask = np.zeros_like(alpha)
    cv2.drawContours(solid_mask, [c], -1, 255, cv2.FILLED)

    # 6. 将新的 Alpha 蒙版应用回图片
    final_rgba = cv2.merge([b, g, r, solid_mask])

    # 7. 贴紧轮廓裁剪
    cropped_img = final_rgba[y:y+ch, x:x+cw]

    # 8. 居中并缩放到底板
    margin = 8 # 留白，防止紧贴边缘
    safe_size = target_size - margin * 2
    
    scale = min(safe_size / cw, safe_size / ch)
    new_w, new_h = int(cw * scale), int(ch * scale)
    resized_img = cv2.resize(cropped_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 创建一个完全透明的目标底板
    out_canvas = np.zeros((target_size, target_size, 4), dtype=np.uint8)
    offset_x = (target_size - new_w) // 2
    offset_y = (target_size - new_h) // 2
    
    # 将裁剪后的图片贴入底板
    out_canvas[offset_y:offset_y+new_h, offset_x:offset_x+new_w] = resized_img

    # 9. 保存到特殊文件夹下
    output_path = os.path.join(SPECIAL_DIR, output_filename)
    cv2.imwrite(output_path, out_canvas)
    print(f"✅ 处理完成，素材已存入: {output_path}")

if __name__ == "__main__":
    # 执行处理：源文件路径 -> 目标 PNG 文件名
    matted_png_solid_fill("barrier.png", "barrier.png")
    matted_png_solid_fill("basket.png", "basket.png")