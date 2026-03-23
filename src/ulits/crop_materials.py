import cv2
import numpy as np
import os

def process_materials_solid(source_image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    names = ['fish', 'palette', 'paper', 'bow', 'flower', 'heart']
    
    img = cv2.imread(source_image_path, cv2.IMREAD_COLOR)
    if img is None:
        print("错误：无法读取原图！")
        return

    h, w = img.shape[:2]
    slice_width = w // 6
    target_size = 128
    
    print(f"正在使用【轮廓实心填充法】处理素材，原图尺寸: {w}x{h}")

    for i in range(6):
        left = i * slice_width
        right = (i + 1) * slice_width
        slice_img = img[:, left:right]

        # 1. 转为灰度图
        gray = cv2.cvtColor(slice_img, cv2.COLOR_BGR2GRAY)

        # 2. 轻微高斯模糊，减少噪点对边缘判断的干扰
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # 3. 严格二值化阈值：假设背景是纯白，将接近纯白(>245)的设为黑(0背景)，其余设为白(255物体)
        _, thresh = cv2.threshold(blurred, 245, 255, cv2.THRESH_BINARY_INV)

        # 4. 闭运算 (先膨胀后腐蚀)：将花瓣高光处可能断裂的边缘线条强行连接起来
        kernel = np.ones((3, 3), np.uint8)
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

        # 5. 只寻找最外层轮廓 (RETR_EXTERNAL)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            continue
            
        # 找到面积最大的轮廓，即素材本体
        c = max(contours, key=cv2.contourArea)

        # 6. 【核心修复】：创建一个全黑遮罩，并将最大轮廓内部强行画满纯白 (cv2.FILLED)
        # 这一步直接无视了素材内部的高光孔洞，保证遮罩绝对完整
        solid_mask = np.zeros_like(gray)
        cv2.drawContours(solid_mask, [c], -1, 255, cv2.FILLED)

        # 7. 对生成的遮罩做轻微模糊，实现抗锯齿(平滑边缘)
        solid_mask = cv2.GaussianBlur(solid_mask, (3, 3), 0)

        # 8. 根据遮罩合成 RGBA 图像并裁剪包围盒
        x, y, cw, ch = cv2.boundingRect(c)
        b, g, r = cv2.split(slice_img)
        rgba_img = cv2.merge([b, g, r, solid_mask])
        cropped_rgba = rgba_img[y:y+ch, x:x+cw]

        # 9. 居中、缩放 (留出20px安全边距)
        margin = 20
        scale = min((target_size - margin) / cw, (target_size - margin) / ch)
        new_w, new_h = int(cw * scale), int(ch * scale)
        resized_rgba = cv2.resize(cropped_rgba, (new_w, new_h), interpolation=cv2.INTER_AREA)

        final_img = np.zeros((target_size, target_size, 4), dtype=np.uint8)
        offset_x = (target_size - new_w) // 2
        offset_y = (target_size - new_h) // 2
        final_img[offset_y:offset_y+new_h, offset_x:offset_x+new_w] = resized_rgba

        save_path = os.path.join(output_dir, f"{names[i]}.png")
        cv2.imwrite(save_path, final_img)
        print(f"已完美抠图并生成: {save_path}")

if __name__ == "__main__":
    process_materials_solid("source.jpg", "assets/images/materials/")