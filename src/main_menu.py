from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.app import App

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 1. 顶层设计：设置全屏背景图 (与游戏页面同步)
        with self.canvas.before:
            Color(1, 1, 1, 1) 
            self.bg_rect = Rectangle(
                pos=self.pos, 
                size=self.size, 
                source='assets/images/background/1.jpg'
            )
        self.bind(pos=self.update_bg, size=self.update_bg)

        # 🚀 修复核心：明确定义 layout 容器
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        
        # 2. 游戏标题
        layout.add_widget(Label(
            text=" 拾祝漫游 ", font_size=75, bold=True, 
            color=(80, 140, 146, 1), font_name='simhei', size_hint=(1, 0.1)
        ))

        # 3. 难度选择区域
        btn_box = BoxLayout(orientation='vertical', spacing=15, size_hint=(0.8, 0.6), pos_hint={'center_x': 0.5})
        
        difficulties = [
            ("简单模式 ", 1, (0.4, 0.8, 0.4, 0.8)),
            ("中等模式 ", 2, (0.9, 0.7, 0.3, 0.8)),
            ("困难模式 ", 3, (0.8, 0.3, 0.3, 0.8))
        ]

        for text, level, color in difficulties:
            btn = Button(
                text=text, font_size=28, bold=True, font_name='simhei',
                background_color=color, background_normal=''
            )
            # 闭包抓手：传递选中的难度等级
            btn.bind(on_release=lambda instance, lv=level: self.select_difficulty(lv))
            btn_box.add_widget(btn)

        layout.add_widget(btn_box)
        self.add_widget(layout)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def select_difficulty(self, level):
        """将难度等级存入 App 全局变量并切换"""
        app = App.get_running_app()
        app.selected_difficulty = level
        self.manager.current = 'game'