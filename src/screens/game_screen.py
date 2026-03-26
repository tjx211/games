from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle

from src.ui.game_board import GameBoard
from src.managers.score_manager import ScoreManager
from src.ui.result_dialog import ResultDialog
from src.managers.config_manager import ConfigManager
from src.managers.storage_manager import StorageManager

cfg_assets = ConfigManager.get('assets')
cfg_visuals = ConfigManager.get('visuals', 'colors')

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.score_manager = ScoreManager()
        self.current_stage = 1 
        
        self.main_layout = BoxLayout(orientation='vertical')
        
        with self.canvas.before:
            Color(1, 1, 1, 1) 
            self.bg_rect = Rectangle(pos=self.pos, size=self.size, source=cfg_assets.get('global_background'))
        self.bind(pos=self.update_global_bg, size=self.update_global_bg)

        self.header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), padding=[20, 0], spacing=5)
        with self.header.canvas.before:
            Color(*cfg_visuals.get('hud_bg', [1,1,1,0.1])) 
            self.header_bg = Rectangle(pos=self.header.pos, size=self.header.size)
        self.header.bind(pos=self.update_header_bg, size=self.update_header_bg)

        self.turn_label = Label(text="步数: --", font_size=18, bold=True, color=(0.8, 0, 0, 1), font_name='simhei')
        self.score_label = Label(text="得分: 0 / 目标: 0", font_size=18, bold=True, color=(0, 0, 0, 1), font_name='simhei')
        self.header.add_widget(self.turn_label)
        self.header.add_widget(self.score_label)
        self.main_layout.add_widget(self.header)
        
        self.board = GameBoard(size_hint=(1, 0.75))
        self.main_layout.add_widget(self.board)

        bottom = BoxLayout(orientation='horizontal', size_hint=(1, 0.15), padding=20, spacing=20)
        self.exit_btn = Button(text="结算", font_name='simhei', size_hint=(0.3, 1), background_color=(0.5, 0.5, 0.5, 0.6))
        self.exit_btn.bind(on_release=lambda x: self.trigger_settlement(False))
        self.go_btn = Button(text="出  发", font_size=35, bold=True, font_name='simhei', background_color=(0.9, 0.4, 0.5, 0.8), size_hint=(0.7, 1))
        self.go_btn.bind(on_release=self.on_go_pressed)
        bottom.add_widget(self.exit_btn)
        bottom.add_widget(self.go_btn)
        self.main_layout.add_widget(bottom)
        
        self.add_widget(self.main_layout)

        self.overlay = FloatLayout()
        self.is_paused = False

        with self.overlay.canvas.before:
            self.pause_overlay_color = Color(0, 0, 0, 0) 
            self.pause_overlay_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_pause_overlay, size=self.update_pause_overlay)

        # ⭐ 1. 初始化暂停按钮，应用颜色 #185A56 (RGB: 24, 90, 86)
        self.pause_btn = Button(
            text="▌▌", 
            font_name='simhei',
            font_size=26,
            size_hint=(None, None), size=(60, 60),
            pos_hint={'x': 0.01, 'top': 0.99}, 
            background_color=(0,0,0,0),
            color=(24/255.0, 90/255.0, 86/255.0, 0.5), # ⭐ 高级墨绿色
            border=(0,0,0,0)
        )
        self.pause_btn.bind(on_release=self.toggle_pause)
        self.overlay.add_widget(self.pause_btn)
        
        self.add_widget(self.overlay)

    def update_global_bg(self, *args): self.bg_rect.pos, self.bg_rect.size = self.pos, self.size
    def update_header_bg(self, *args): self.header_bg.pos, self.header_bg.size = self.header.pos, self.header.size
    def update_pause_overlay(self, *args): self.pause_overlay_rect.pos, self.pause_overlay_rect.size = self.pos, self.size

    def toggle_pause(self, *args):
        self.is_paused = not getattr(self, 'is_paused', False)
        self.board.is_paused = self.is_paused
        
        if self.is_paused:
            # ⭐ 2. 暂停状态下，图标改为兼容性极好的 ◀，颜色保持 #185A56
            self.pause_btn.text = "◀"  
            self.pause_btn.color = (24/255.0, 90/255.0, 86/255.0, 1) 
            self.pause_overlay_color.a = 0.5  
            self.go_btn.disabled = True
            self.exit_btn.disabled = True
        else:
            # ⭐ 3. 恢复游戏状态下，改回 ▌▌，颜色保持 #185A56
            self.pause_btn.text = "▌▌" 
            self.pause_btn.color = (24/255.0, 90/255.0, 86/255.0, 0.5)
            self.pause_overlay_color.a = 0    
            self.go_btn.disabled = len(self.board.game_logic.path) <= 1
            self.exit_btn.disabled = False

    def on_enter(self):
        self.is_paused = False
        if hasattr(self, 'board'): self.board.is_paused = False
        if hasattr(self, 'pause_btn'):
            self.pause_btn.text = "▌▌"
            # ⭐ 4. 重置页面时，颜色也要应用 #185A56
            self.pause_btn.color = (24/255.0, 90/255.0, 86/255.0, 0.5)
            self.pause_overlay_color.a = 0

        app = App.get_running_app()
        is_continue = getattr(app, 'is_continue', False)

        if is_continue:
            save_data = StorageManager.load_progress()
            if save_data:
                self.current_stage = save_data.get('stage', 1)
                self.score_manager.current_score = save_data.get('score', 0)
                self.base_difficulty = save_data.get('difficulty', 1)
                self.turns_left = save_data.get('turns_left', 10)
                self.load_stage_config(is_restore=True)
        else:
            self.base_difficulty = getattr(app, 'selected_difficulty', 1)
            self.current_stage = 1
            self.score_manager.reset()
            self.load_stage_config(is_restore=False)

    def load_stage_config(self, is_restore=False):
        stage = self.current_stage
        size = min(10, 7 + (stage - 1) // 3)
        cols, rows = size, size
        
        target = 300 + (stage - 1) * 350
        turns = 10 + (stage - 1) * 2
        
        if not is_restore:
            self.turns_left = 999 if self.base_difficulty == 1 else turns
            
        self.target_score = target * self.base_difficulty 
        self.board.game_logic.load_level(cols, rows, stage)
        self.board.rebuild_board(cols, rows)
        self.update_ui_text()

    def update_ui_text(self):
        self.score_label.text = f"得分: {self.score_manager.current_score} / 目标: {self.target_score}"
        self.turn_label.text = f"第{self.current_stage}关 | 步数: {'∞' if self.turns_left > 100 else self.turns_left}"

    def on_go_pressed(self, instance):
        path = self.board.game_logic.path
        if len(path) > 1:
            self.go_btn.disabled = True
            
            clock_count = 0
            star_count = 0
            for cell in path:
                if cell.is_special():
                    sp_type = getattr(cell.content, 'type', None)
                    if sp_type == 'clock': clock_count += 1
                    elif sp_type == 'star_gem': star_count += 1
            
            def after_animation():
                if self.turns_left < 900: 
                    self.turns_left -= 1
                    if clock_count > 0:
                        self.turns_left += 3 * clock_count
                
                points = self.score_manager.calculate_line_score(len(path), star_count)
                self.score_manager.add_score(points)
                self.update_ui_text()
                
                self.board.game_logic.execute_collection()
                
                if self.board.game_logic.check_deadlock():
                    self.board.game_logic.shuffle()
                    self.board.animate_shuffle()

                self.board.refresh_all_cells()
                self.board.floating_score.opacity = 0 
                
                if not getattr(self, 'is_paused', False):
                    self.go_btn.disabled = False
                
                StorageManager.update_high_score(self.score_manager.current_score)
                
                if self.score_manager.current_score >= self.target_score:
                    self.current_stage += 1
                    self.load_stage_config(is_restore=False)
                    StorageManager.save_progress(self.current_stage, self.score_manager.current_score, self.turns_left, self.base_difficulty)
                elif self.turns_left <= 0: 
                    StorageManager.clear_progress()
                    self.trigger_settlement(True)
                else:
                    StorageManager.save_progress(self.current_stage, self.score_manager.current_score, self.turns_left, self.base_difficulty)

            self.board.animate_basket_move(after_animation)

    def trigger_settlement(self, is_game_over):
        ResultDialog(final_score=self.score_manager.current_score, stars=self.score_manager.get_star_rating(),
                     on_restart_callback=self.on_enter, on_exit_callback=self.return_to_menu).open()

    def return_to_menu(self): 
        self.score_manager.reset()
        self.manager.current = 'main_menu'