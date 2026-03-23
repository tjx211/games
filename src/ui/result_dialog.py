from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
import os

class ResultDialog(ModalView):
    def __init__(self, final_score, stars, on_restart_callback, on_exit_callback, **kwargs):
        super().__init__(**kwargs)
        
        self.size_hint = (0.85, 0.45) 
        self.auto_dismiss = False     
        self.background = '' 
        self.background_color = (0, 0, 0, 0.7) 
        self.opacity = 0 

        layout = BoxLayout(orientation='vertical', padding=25, spacing=15)

        with layout.canvas.before:
            Color(0.98, 0.96, 0.94, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
        layout.bind(pos=self.update_bg, size=self.update_bg)

        # 1. 标题
        layout.add_widget(Label(text="游 戏 结 算", font_size=40, bold=True, color=(0.8, 0.3, 0.3, 1), font_name='simhei', size_hint=(1, 0.25)))

        # 2. 星星展示 (根据您的要求修改路径为 assets/images/materials/start.png)
        star_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.25))
        star_layout.add_widget(Label(size_hint_x=0.2)) 
        
        for i in range(3):
            # 精确对齐您的最新路径
            star_img = Image(source='assets/images/materials/start.png', allow_stretch=True, keep_ratio=True)
            if i >= stars:
                star_img.color = (0.3, 0.3, 0.3, 1) # 没拿到的星变暗
            star_layout.add_widget(star_img)
            
        star_layout.add_widget(Label(size_hint_x=0.2))
        layout.add_widget(star_layout)

        # 3. 分数
        layout.add_widget(Label(text=f"最终得分: {final_score}", font_size=35, bold=True, color=(0.3, 0.3, 0.3, 1), font_name='simhei', size_hint=(1, 0.2)))

        # 4. 按钮
        btn_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.3))
        rb = Button(text="再来一局", background_color=(0.4, 0.8, 0.5, 1), font_size=28, bold=True, font_name='simhei')
        rb.bind(on_press=lambda x: self.handle_action(on_restart_callback))
        eb = Button(text="返回主页", background_color=(0.9, 0.6, 0.4, 1), font_size=28, bold=True, font_name='simhei')
        eb.bind(on_press=lambda x: self.handle_action(on_exit_callback))
        btn_layout.add_widget(rb); btn_layout.add_widget(eb)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
        self.bind(on_open=self.animate_popup)

    def update_bg(self, instance, value):
        self.bg.pos, self.bg.size = instance.pos, instance.size

    def animate_popup(self, *args):
        Animation(opacity=1, duration=0.4).start(self)

    def handle_action(self, callback):
        self.dismiss()
        if callback: callback()