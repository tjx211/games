import os
import sys
import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, FadeTransition

# 确保路径被正确识别
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入抽离出去的独立屏幕组件
from src.screens.main_menu import MainMenuScreen
from src.screens.game_screen import GameScreen

# 模拟手机竖屏
Window.size = (450, 800)

class ConnectApp(App):
    # App级别的数据总线
    selected_difficulty = 1 
    
    def build(self):
        # 挂载场景管理器与转场特效
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    ConnectApp().run()