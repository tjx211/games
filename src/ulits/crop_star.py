import cv2
import numpy as np
import os

def process_single_image(source_path, output_path, target_size=128):
    # 1. 读取原图
    img = cv2.imread(source_path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"错误：无法读取原图，请检查 {source_path} 是否在当前目录！")
        return

    print(f"正在使用【轮廓实心填充法】处理单张素材: {source_path}")

    # 2. 转为灰度图并轻微模糊
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # 3. 严格二值化阈值：抠掉纯白背景
    _, thresh = cv2.threshold(blurred, 245, 255, cv2.THRESH_BINARY_INV)

    # 4. 闭运算：修补星星内部可能的高光断层
    kernel = np.ones((3, 3), np.uint8)
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 5. 寻找最外层轮廓
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("未找到星星轮廓！")
        return
        
    c = max(contours, key=cv2.contourArea)

    # 6. 核心：创建全黑遮罩，并将星星轮廓内部强行画满纯白
    solid_mask = np.zeros_like(gray)
    cv2.drawContours(solid_mask, [c], -1, 255, cv2.FILLED)

    # 轻微抗锯齿模糊
    solid_mask = cv2.GaussianBlur(solid_mask, (3, 3), 0)

    # 7. 提取 RGBA 并贴紧轮廓裁剪
    x, y, cw, ch = cv2.boundingRect(c)
    b, g, r = cv2.split(img)
    rgba_img = cv2.merge([b, g, r, solid_mask])
    cropped_rgba = rgba_img[y:y+ch, x:x+cw]

    # 8. 居中并缩放到底板上
    margin = 10 # 星星可以稍微饱满一点，边距留小点
    scale = min((target_size - margin) / cw, (target_size - margin) / ch)
    new_w, new_h = int(cw * scale), int(ch * scale)
    resized_rgba = cv2.resize(cropped_rgba, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 创建完全透明的底板
    final_img = np.zeros((target_size, target_size, 4), dtype=np.uint8)
    offset_x = (target_size - new_w) // 2
    offset_y = (target_size - new_h) // 2
    final_img[offset_y:offset_y+new_h, offset_x:offset_x+new_w] = resized_rgba

    # 9. 保存为支持透明通道的 PNG！
    # 注意：即便原图是 .jpg，输出也必须是 .png，否则透明底会变成黑底
# 9. 保存为支持透明通道的 PNG！
    out_dir = os.path.dirname(output_path)
    if out_dir:  # 只有当路径里真的包含文件夹时，才去创建目录
        os.makedirs(out_dir, exist_ok=True)
    
    cv2.imwrite(output_path, final_img)
    print(f"✅ 已完美抠图并生成透明素材: {output_path}")

if __name__ == "__main__":
    # 假设您的原图叫 start.jpg，我们在当前目录生成一个透明的 start.png
    process_single_image("start.jpg", "start.png")