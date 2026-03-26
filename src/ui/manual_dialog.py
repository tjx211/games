import os
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from src.managers.config_manager import ConfigManager

class ManualDialog(ModalView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.size_hint = (0.8, 0.65)
        self.auto_dismiss = True 
        
        self.overlay_color = [0, 0, 0, 0.6]
        self.background_color = [0, 0, 0, 0] 

        layout = BoxLayout(orientation='vertical', padding=[20, 20, 20, 20], spacing=10)

        with layout.canvas.before:
            Color(224/255.0, 215/255.0, 207/255.0, 1) 
            self.bg_rect = RoundedRectangle(pos=layout.pos, size=layout.size, radius=[15])
        layout.bind(pos=self.update_bg, size=self.update_bg)

        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        title = Label(
            text="游戏说明书", font_size=26, bold=True, 
            color=(0.2, 0.15, 0.1, 1), font_name='simhei', halign='left', valign='middle'
        )
        title.bind(size=title.setter('text_size'))
        
        # ⭐ 修复乱码：将 ✖ 替换为 ×
        close_btn = Button(
            text="×", font_size=35, font_name='simhei', size_hint_x=None, width=40,
            background_color=(0,0,0,0), color=(0.8, 0.3, 0.3, 1)
        )
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(title)
        header.add_widget(close_btn)
        layout.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1))
        self.content_box = BoxLayout(orientation='vertical', size_hint_y=None, padding=[0, 10, 0, 10], spacing=15)
        self.content_box.bind(minimum_height=self.content_box.setter('height'))
        scroll.add_widget(self.content_box)
        
        layout.add_widget(scroll)
        self.add_widget(layout)
        
        self.load_content()

    def update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def load_content(self):
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
            assets_cfg = ConfigManager.get('assets')
            if not isinstance(assets_cfg, dict): assets_cfg = {}
            img_dict = assets_cfg.get('manual_images', {})
            if not isinstance(img_dict, dict): img_dict = {}
            
            txt_path = os.path.join(base_dir, 'assets', 'manual.txt')
            
            if not os.path.exists(txt_path) and os.path.exists(txt_path + '.txt'):
                txt_path = txt_path + '.txt'
            
            if not os.path.exists(txt_path):
                err = f"说明书文件未找到！\n\n请确认文件是否放在:\n{txt_path}\n\n(提示:请检查文件名是否不小心变成了 manual.txt.txt)"
                lbl = Label(text=err, color=(0.8, 0.1, 0.1, 1), font_size=18, font_name='simhei', size_hint_y=None, height=150)
                self.content_box.add_widget(lbl)
                return
                
            with open(txt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            current_text = ""
            for line in lines:
                line = line.strip()
                if line.startswith('[IMAGE:') and line.endswith(']'):
                    if current_text.strip():
                        self.content_box.add_widget(self.create_label(current_text))
                        current_text = ""
                    
                    img_key = line[7:-1]
                    img_rel_path = img_dict.get(img_key, '')
                    
                    safe_img_rel_path = img_rel_path.replace('/', os.sep) if img_rel_path else ''
                    img_path = os.path.join(base_dir, safe_img_rel_path) if safe_img_rel_path else ''
                    
                    if os.path.exists(img_path):
                        img = Image(source=img_path, size_hint_y=None, height=100, allow_stretch=True, keep_ratio=True)
                        self.content_box.add_widget(img)
                else:
                    current_text += line + "\n"
                    
            if current_text.strip():
                self.content_box.add_widget(self.create_label(current_text))
                
        except Exception as e:
            err_msg = f"解析异常:\n{str(e)}"
            lbl = Label(text=err_msg, color=(0.8, 0.1, 0.1, 1), font_size=18, font_name='simhei', size_hint_y=None, height=150)
            self.content_box.add_widget(lbl)

    def create_label(self, text):
        lbl = Label(
            text=text.strip(), color=(0.15, 0.15, 0.15, 1), font_size=18, 
            font_name='simhei', size_hint_y=None, halign='left', valign='top'
        )
        lbl.bind(width=lambda *x: lbl.setter('text_size')(lbl, (lbl.width, None)), 
                 texture_size=lambda *x: lbl.setter('height')(lbl, lbl.texture_size[1]))
        return lbl