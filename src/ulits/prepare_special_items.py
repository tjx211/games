import cv2
import numpy as np
import os

def process_special_item(source_filename, output_name, target_size=128):
    """
    专门处理单张 JPG 素材：抠白底、生成透明通道、居中、调整大小。
    严格对齐之前使用的 Solid Fill 抠图方法论。
    """
    source_path = source_filename
    # 根据需求表，定义新的功能文件夹路径
    output_dir = os.path.join("assets", "images", "special")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{output_name}.png")

    print(f"正在处理特殊素材: {source_path} -> {output_path}")

    # 1. 读取 JPG 原图
    img = cv2.imread(source_path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"❌ 错误：无法读取原图 {source_path}，请确保原图在当前目录下！")
        return

    # 2. 转为灰度图并轻微模糊，减少噪点对边缘判断的干扰
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. 严格二值化阈值：假设背景是纯白，将接近纯白(>245)的设为黑(0背景)，其余设为白(255物体)
    _, thresh = cv2.threshold(blurred, 245, 255, cv2.THRESH_BINARY_INV)

    # 4. 寻找最外层轮廓 (RETR_EXTERNAL)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("❌ 警告：未找到有效轮廓，无法安全抠图。")
        return
        
    # 找到面积最大的轮廓，即星星/饼干本体
    c = max(contours, key=cv2.contourArea)

    # 5. 【实心填充抠图法】：创建一个全黑遮罩，并将最大轮廓内部强行画满纯白
    solid_mask = np.zeros_like(gray)
    cv2.drawContours(solid_mask, [c], -1, 255, cv2.FILLED)

    # 轻微抗锯齿处理（平滑边缘）
    solid_mask = cv2.GaussianBlur(solid_mask, (3, 3), 0)

    # 6. 提取 BGR 颜色通道，并合成包含透明通道的 RGBA
    b, g, r = cv2.split(img)
    rgba_img = cv2.merge([b, g, r, solid_mask])

    # 7. 根据轮廓提取包围盒，并贴紧裁剪
    x, y, cw, ch = cv2.boundingRect(c)
    cropped_rgba = rgba_img[y:y+ch, x:x+cw]

    # 8. 居中、缩放 (留出安全边距)
    margin = 15 # 为发光动画留出空间
    safe_size = target_size - margin * 2
    
    scale = min(safe_size / cw, safe_size / ch)
    new_w, new_h = int(cw * scale), int(ch * scale)
    
    # 使用 INTER_AREA 插值算法在缩小图片时保持最高画质
    resized_rgba = cv2.resize(cropped_rgba, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 创建一个完全透明的目标底板
    final_img = np.zeros((target_size, target_size, 4), dtype=np.uint8)
    offset_x = (target_size - new_w) // 2
    offset_y = (target_size - new_h) // 2
    
    # 将裁剪缩放后的素材贴到底板中央
    final_img[offset_y:offset_y+new_h, offset_x:offset_x+new_w] = resized_rgba

    # 9. 保存为目标 PNG 文件
    cv2.imwrite(output_path, final_img)
    print(f"✅ 处理完成，素材已存入: {output_path}")

if __name__ == "__main__":
    # 处理您上传的果冻原图
    process_special_item("image_b328ca.png", "jelly")
    # 处理您上传的宝箱(饼干)原图
    process_special_item("image_b38dc9.png", "chest")