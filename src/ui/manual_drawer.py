import os
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from src.managers.config_manager import ConfigManager

class ManualDialog(ModalView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ⭐ 1. 弹出小窗页面：固定位置和大小 (占屏幕宽85%，高75%)
        self.size_hint = (0.85, 0.75)
        self.auto_dismiss = True # 允许点击蒙版外部自动关闭
        
        # ⭐ 2. 自定义蒙版颜色：使用 RGB (224, 215, 207) #E0D7CF
        # 换算为 0~1：(0.878, 0.843, 0.811)
        # 降低亮度(乘以0.6) 并 增加透明度(Alpha=0.85)
        self.overlay_color = [0.878 * 0.6, 0.843 * 0.6, 0.811 * 0.6, 0.85]
        
        # 去除系统默认的弹窗底色贴图，改为纯透明，方便自定义
        self.background = ''
        self.background_color = [0, 0, 0, 0]

        # ⭐ 3. 弹窗本身的背景绘制（使用带点暖色的偏白底色，与蒙版呼应）
        with self.canvas.before:
            Color(0.98, 0.96, 0.94, 1) 
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        # 弹窗主布局
        layout = BoxLayout(orientation='vertical', padding=[20, 20, 20, 20], spacing=10)

        # 顶部：标题 + 关闭按钮
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        title = Label(
            text="游戏说明书", font_size=28, bold=True, 
            color=(0.4, 0.3, 0.2, 1), font_name='simhei', halign='left', valign='middle'
        )
        title.bind(size=title.setter('text_size'))
        
        close_btn = Button(
            text="✖", font_size=26, font_name='simhei', size_hint_x=None, width=40,
            background_color=(0,0,0,0), color=(0.7, 0.4, 0.3, 1)
        )
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(title)
        header.add_widget(close_btn)
        layout.add_widget(header)

        # ⭐ 4. 核心：外框位置不变，内部可上下滑动 (ScrollView)
        scroll = ScrollView(size_hint=(1, 1))
        self.content_box = BoxLayout(orientation='vertical', size_hint_y=None, padding=[0, 10, 0, 10], spacing=15)
        self.content_box.bind(minimum_height=self.content_box.setter('height'))
        scroll.add_widget(self.content_box)
        
        layout.add_widget(scroll)
        self.add_widget(layout)
        
        # 触发内容加载
        self.load_content()

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def load_content(self):
        # ⭐ 5. 从配置文件读取 .txt 文件路径和图片映射表
        txt_path = ConfigManager.get('assets', 'manual_file')
        img_dict = ConfigManager.get('assets', 'manual_images') or {}
        
        if not os.path.exists(txt_path):
            lbl = Label(text="说明书文件丢失...", color=(1,0,0,1), font_name='simhei', size_hint_y=None, height=50)
            self.content_box.add_widget(lbl)
            return
            
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_text = ""
        for line in lines:
            line = line.strip()
            # ⭐ 6. 动态解析：遇到 [IMAGE:xxx] 占位符时，切断文字，插入图片
            if line.startswith('[IMAGE:') and line.endswith(']'):
                # 先把累计的文字生成 Label 放入滑动框
                if current_text.strip():
                    self.content_box.add_widget(self.create_label(current_text))
                    current_text = ""
                
                # 读取占位符中的键名，去 yaml 里找图片路径
                img_key = line[7:-1]
                img_path = img_dict.get(img_key, '')
                if os.path.exists(img_path):
                    img = Image(source=img_path, size_hint_y=None, height=120, allow_stretch=True, keep_ratio=True)
                    self.content_box.add_widget(img)
            else:
                # 累加普通文字
                current_text += line + "\n"
                
        # 补齐最后一段文字
        if current_text.strip():
            self.content_box.add_widget(self.create_label(current_text))

    def create_label(self, text):
        # ⭐ 7. 文字标签自适应高度，确保长文本能完美下拉滑动
        lbl = Label(
            text=text.strip(), color=(0.3, 0.3, 0.3, 1), font_size=16, 
            font_name='simhei', size_hint_y=None, halign='left', valign='top'
        )
        lbl.bind(width=lambda *x: lbl.setter('text_size')(lbl, (lbl.width, None)), 
                 texture_size=lambda *x: lbl.setter('height')(lbl, lbl.texture_size[1]))
        return lbl