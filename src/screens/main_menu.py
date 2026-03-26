from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.app import App

from src.managers.config_manager import ConfigManager
from src.managers.storage_manager import StorageManager
from src.ui.manual_dialog import ManualDialog

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        bg_source = ConfigManager.get('assets').get('global_background', 'assets/images/background/1.jpg')
        
        with self.canvas.before:
            Color(1, 1, 1, 1) 
            self.bg_rect = Rectangle(
                pos=self.pos, 
                size=self.size, 
                source=bg_source
            )
        self.bind(pos=self.update_bg, size=self.update_bg)

        self.main_layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        self.add_widget(self.main_layout)

        self.top_float = FloatLayout()
        ui_assets = ConfigManager.get('assets').get('ui', {})
        
        # 【退出】键 (❌)
        self.quit_btn = Button(
            background_normal=ui_assets.get('btn_quit', ''),
            size_hint=(None, None), size=(50, 50),
            pos_hint={'x': 0.01, 'top': 0.99}, 
            border=(0,0,0,0)
        )
        if not ui_assets.get('btn_quit'):
            self.quit_btn.text = "×"
            self.quit_btn.font_name = 'simhei'
            self.quit_btn.font_size = 40
            self.quit_btn.background_color = (0, 0, 0, 0) 
            self.quit_btn.color = (1, 0.4, 0.4, 1)    
            
        self.quit_btn.bind(on_release=lambda x: App.get_running_app().stop())
        self.top_float.add_widget(self.quit_btn)

        # 【说明书】键 (❓)
        self.help_btn = Button(
            background_normal=ui_assets.get('btn_help', ''),
            size_hint=(None, None), size=(50, 50),
            pos_hint={'x': 0.02, 'top': 0.93}, 
            border=(0,0,0,0)
        )
        if not ui_assets.get('btn_help'):
            self.help_btn.text = "？"
            self.help_btn.font_name = 'simhei'
            self.help_btn.font_size = 40
            self.help_btn.background_color = (0, 0, 0, 0) 
            self.help_btn.color = (0.5, 0.8, 0.9, 1) 
              
            
        self.help_btn.bind(on_release=lambda x: ManualDialog().open())
        self.top_float.add_widget(self.help_btn)

        self.add_widget(self.top_float)

    def on_pre_enter(self, *args):
        self.main_layout.clear_widgets()
        
        self.main_layout.add_widget(Label(
            text=" 拾祝巡礼 ", font_size=70, bold=True, 
            color=(80/255.0, 140/255.0, 146/255.0, 1), font_name='simhei', size_hint=(1, 0.1)
        ))

        high_score = StorageManager.get_high_score()
        self.main_layout.add_widget(Label(
            text=f"历史最高分: {high_score}", font_size=24, bold=True, 
            color=(0.3, 0.3, 0.3, 1), font_name='simhei', size_hint=(1, 0.05)
        ))

        btn_box = BoxLayout(orientation='vertical', spacing=15, size_hint=(0.8, 0.6), pos_hint={'center_x': 0.5})
        
        if StorageManager.has_saved_game():
            continue_btn = Button(
                text="继续游戏", font_size=28, bold=True, font_name='simhei',
                background_color=(0.9, 0.6, 0.2, 0.8), background_normal=''
            )
            continue_btn.bind(on_release=self.continue_game)
            btn_box.add_widget(continue_btn)
        
        difficulties = [
            ("简单模式", 1, (0.4, 0.8, 0.4, 0.8)),
            ("中等模式", 2, (0.9, 0.7, 0.3, 0.8)),
            ("困难模式", 3, (0.8, 0.3, 0.3, 0.8))
        ]

        for text, level, color in difficulties:
            btn = Button(
                text=text, font_size=28, bold=True, font_name='simhei',
                background_color=color, background_normal=''
            )
            btn.bind(on_release=lambda instance, lv=level: self.select_difficulty(lv))
            btn_box.add_widget(btn)

        self.main_layout.add_widget(btn_box)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def select_difficulty(self, level):
        app = App.get_running_app()
        app.selected_difficulty = level
        app.is_continue = False 
        self.manager.current = 'game'

    def continue_game(self, instance):
        app = App.get_running_app()
        app.is_continue = True 
        self.manager.current = 'game'