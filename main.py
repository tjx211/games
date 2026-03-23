import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, Line
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.managers.grid_manager import GridManager
except ImportError:
    print("找不到棋盘底层逻辑文件！")

from src.managers.score_manager import ScoreManager
from src.ui.result_dialog import ResultDialog
from src.main_menu import MainMenuScreen

Window.size = (450, 800)

CONFIG = {
    'BOARD_GAP_COLOR': (0, 0, 0, 0.2),  
    'CELL_BG_COLOR': (1, 1, 1, 0.15), 
    'GLOW_COLOR_JELLY': (0.2, 0.9, 0.2, 0.5), 
    'GLOW_COLOR_CHEST': (0.9, 0.7, 0.2, 0.5), 
    'GLOW_COLOR_BASKET': (1, 1, 1, 0.8),     
    'BLOCK_BG_COLOR': (0, 0, 0, 0.7),   
    'GLOBAL_BACKGROUND': 'assets/images/background/1.jpg',
}

IMAGE_MAP = {
    '蓝鱼': 'assets/images/materials/fish.png',
    '橘盘': 'assets/images/materials/palette.png',
    '粉纸': 'assets/images/materials/paper.png',
    '紫结': 'assets/images/materials/bow.png',
    '粉花': 'assets/images/materials/flower.png',
    '蓝心': 'assets/images/materials/heart.png',
}

SPECIAL_IMAGE_MAP = {
    'jelly': 'assets/images/special/jelly.png',
    'chest': 'assets/images/special/chest.png',
    'basket': 'assets/images/special/basket.png', 
    'barrier': 'assets/images/special/barrier.png', 
}

class CellWidget(Widget):
    def __init__(self, grid_x, grid_y, **kwargs):
        super().__init__(**kwargs)
        self.grid_x, self.grid_y = grid_x, grid_y
        self.is_selected = False
        self.special_type = None 
        
        with self.canvas.before:
            self.bg_color_instr = Color(*CONFIG['CELL_BG_COLOR']) 
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.glow_color = Color(1, 1, 1, 0) 
            self.glow_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.img = Image(allow_stretch=True, keep_ratio=True)
        self.add_widget(self.img)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.bg_rect.pos = (self.x + 1, self.y + 1)
        self.bg_rect.size = (self.width - 2, self.height - 2)
        
        self.glow_rect.pos = (self.x + 3, self.y + 3)
        self.glow_rect.size = (self.width - 6, self.height - 6)

        if not self.is_selected:
            if self.special_type == 'basket':
                self.img.size = (self.width * 1.3, self.height * 1.3)
            elif self.special_type == 'barrier':
                self.img.size = (self.width, self.height)
            elif self.special_type in ['jelly', 'chest']:
                self.img.size = (self.width - 4, self.height - 4)
            else:
                self.img.size = (self.width - 12, self.height - 12)
            self.img.center = self.center

    def update_view(self, cell_data):
        self.is_selected = False 
        self.img.source = ''
        self.img.opacity = 1 
        self.canvas.after.clear()
        
        self.special_type = None 
        Animation.cancel_all(self.glow_color)
        self.glow_color.a = 0
        self.bg_color_instr.a = 0.15 

        if cell_data.content == '篮子':
            img_path = SPECIAL_IMAGE_MAP.get('basket', '')
            if os.path.exists(img_path):
                self.img.source = img_path
                self.special_type = 'basket' 
                self.bg_color_instr.a = 0.6 
                self._trigger_glow_animation('basket')

        elif cell_data.is_obstacle():
            img_path = SPECIAL_IMAGE_MAP.get('barrier', '')
            if os.path.exists(img_path):
                self.img.source = img_path
                self.special_type = 'barrier'
                self.bg_color_instr.a = 0.0 

        elif cell_data.is_special():
            self.special_type = getattr(cell_data.content, 'type', None)
            img_path = SPECIAL_IMAGE_MAP.get(self.special_type, '')
            if os.path.exists(img_path):
                self.img.source = img_path
                self.bg_color_instr.a = 0.0 
                self._trigger_glow_animation(self.special_type)

        elif cell_data.content:
            color_name = cell_data.get_color()
            img_path = IMAGE_MAP.get(color_name, '')
            if os.path.exists(img_path):
                self.img.source = img_path
        self.update_rect()

    def _trigger_glow_animation(self, sp_type):
        if sp_type == 'jelly': self.glow_color.rgba = CONFIG['GLOW_COLOR_JELLY']
        elif sp_type == 'chest': self.glow_color.rgba = CONFIG['GLOW_COLOR_CHEST']
        elif sp_type == 'basket': 
            self.glow_color.rgba = CONFIG['GLOW_COLOR_BASKET']
            self.glow_color.a = 0.1 
        
        anim = Animation(a=0.5, duration=1.2, t='in_out_quad') + Animation(a=0.1, duration=1.2, t='in_out_quad')
        anim.repeat = True 
        anim.start(self.glow_color)

    def animate_select(self):
        if not self.is_selected and self.img.source:
            self.is_selected = True
            Animation(size=(self.width + 10, self.height + 10), center=self.center, duration=0.1).start(self.img)

    def animate_deselect(self):
        if self.is_selected and self.img.source:
            self.is_selected = False
            self.update_rect()

class GameBoard(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化默认7x7，稍后会被 GameScreen 接管重构
        self.game_logic = GridManager(cols=7, rows=7)
        self.grid_layout = GridLayout(cols=7, rows=7, size_hint=(None, None))
        self.add_widget(self.grid_layout)
        
        with self.canvas.before:
            Color(0, 0, 0, 0.2)
            self.bg_board = Rectangle(pos=self.pos, size=self.size)

        self.floating_score = Label(text="0", font_size=50, bold=True, color=(1, 0.2, 0.2, 1), size_hint=(None, None), size=(50, 50), opacity=0)
        self.add_widget(self.floating_score)
        self.cell_widgets = {}
        self.bind(pos=self.update_layout, size=self.update_layout)

    def update_layout(self, *args):
        self.grid_layout.pos, self.grid_layout.size = self.pos, self.size
        self.bg_board.pos, self.bg_board.size = self.pos, self.size
        self.update_visual_feedback()

    # 新增：动态重构网格（用于连续关卡扩容）
    def rebuild_board(self, cols, rows):
        self.grid_layout.cols = cols
        self.grid_layout.rows = rows
        self.grid_layout.clear_widgets()
        self.cell_widgets.clear()
        # 注意 y 的遍历方向，保证 [0][0] 在最下
        for y in range(rows - 1, -1, -1):
            for x in range(cols):
                cell_ui = CellWidget(grid_x=x, grid_y=y)
                self.grid_layout.add_widget(cell_ui)
                self.cell_widgets[(x, y)] = cell_ui
        self.refresh_all_cells()

    def refresh_all_cells(self):
        for y in range(self.game_logic.rows):
            for x in range(self.game_logic.cols):
                self.cell_widgets[(x, y)].update_view(self.game_logic.grid[y][x])
        self.update_visual_feedback()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos): self.process_touch(touch); return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos): self.process_touch(touch); return True
        return super().on_touch_move(touch)

    def process_touch(self, touch):
        for (x, y), cell_ui in self.cell_widgets.items():
            if cell_ui.collide_point(*touch.pos):
                old_len = len(self.game_logic.path)
                if self.game_logic.connect(x, y) or len(self.game_logic.path) != old_len:
                    self.update_visual_feedback()
                break

    def update_visual_feedback(self):
        path = self.game_logic.path
        for (x, y), cell_ui in self.cell_widgets.items():
            if any(c.x == x and c.y == y for c in path): cell_ui.animate_select()
            else: cell_ui.animate_deselect()
            
        self.canvas.after.clear()
        if len(path) < 2: self.floating_score.opacity = 0; return
        
        with self.canvas.after:
            Color(1, 1, 1, 0.6)
            points = []
            for cell in path:
                ui = self.cell_widgets[(cell.x, cell.y)]
                points.extend([ui.center_x, ui.center_y])
            Line(points=points, width=10, cap='round', joint='round')
            
        last_ui = self.cell_widgets[(path[-1].x, path[-1].y)]
        self.floating_score.text = str(len(path) - 1)
        self.floating_score.opacity = 1
        self.floating_score.center = (last_ui.center_x + 35, last_ui.center_y + 45)

    def animate_basket_move(self, on_complete_callback):
        path = self.game_logic.path
        if len(path) < 2:
            on_complete_callback()
            return

        start_ui = self.cell_widgets[(path[0].x, path[0].y)]
        base_w, base_h = start_ui.width * 1.3, start_ui.height * 1.3
        
        temp_basket = Image(
            source=SPECIAL_IMAGE_MAP['basket'],
            size=(base_w, base_h), center=start_ui.center,
            allow_stretch=True, keep_ratio=True
        )
        self.add_widget(temp_basket)
        start_ui.img.opacity = 0
        
        step_idx = 1
        
        def animate_next_step(*args):
            nonlocal step_idx
            if step_idx >= len(path):
                self.remove_widget(temp_basket)
                on_complete_callback()
                return

            target_cell = path[step_idx]
            target_ui = self.cell_widgets[(target_cell.x, target_cell.y)]
            
            move_anim = Animation(center=target_ui.center, duration=0.15, t='out_quad')
            
            def on_move_complete(*args):
                target_ui.img.opacity = 0
                breathe_anim = Animation(size=(base_w * 1.15, base_h * 1.15), duration=0.08, t='out_quad') + \
                               Animation(size=(base_w, base_h), duration=0.08, t='in_quad')
                def on_breathe_complete(*args):
                    nonlocal step_idx
                    step_idx += 1
                    animate_next_step()
                
                breathe_anim.bind(on_complete=on_breathe_complete)
                breathe_anim.start(temp_basket)

            move_anim.bind(on_complete=on_move_complete)
            move_anim.start(temp_basket)

        animate_next_step()

    #  新增：华丽洗牌动画
    def animate_shuffle(self):
        """让所有非篮子、非障碍物的材料缩小再放大，制造洗牌视觉"""
        for (x, y), cell_ui in self.cell_widgets.items():
            if cell_ui.special_type not in ['basket', 'barrier']:
                original_size = cell_ui.img.size
                anim = Animation(size=(0, 0), duration=0.2, t='in_quad') + \
                       Animation(size=original_size, duration=0.3, t='out_bounce')
                anim.start(cell_ui.img)


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.score_manager = ScoreManager()
        self.current_stage = 1 # 连续闯关记录
        
        self.main_layout = BoxLayout(orientation='vertical')
        
        with self.canvas.before:
            Color(1, 1, 1, 1) 
            self.bg_rect = Rectangle(pos=self.pos, size=self.size, source=CONFIG['GLOBAL_BACKGROUND'])
        self.bind(pos=self.update_global_bg, size=self.update_global_bg)

        # HUD 加入了目标分数显示
        self.header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), padding=[20, 0])
        with self.header.canvas.before:
            Color(1, 1, 1, 0.1) 
            self.header_bg = Rectangle(pos=self.header.pos, size=self.header.size)
        self.header.bind(pos=self.update_header_bg, size=self.update_header_bg)

        self.turn_label = Label(text="步数: --", font_size=20, bold=True, color=(0.8, 0, 0, 1), font_name='simhei')
        self.score_label = Label(text="得分: 0 / 目标: 0", font_size=20, bold=True, color=(0, 0, 0, 1), font_name='simhei')
        self.header.add_widget(self.turn_label); self.header.add_widget(self.score_label)
        self.main_layout.add_widget(self.header)
        
        self.board = GameBoard(size_hint=(1, 0.75))
        self.main_layout.add_widget(self.board)

        bottom = BoxLayout(orientation='horizontal', size_hint=(1, 0.15), padding=20, spacing=20)
        self.exit_btn = Button(text="结算", font_name='simhei', size_hint=(0.3, 1), background_color=(0.5, 0.5, 0.5, 0.6))
        self.exit_btn.bind(on_release=lambda x: self.trigger_settlement(False))
        self.go_btn = Button(text="出  发", font_size=35, bold=True, font_name='simhei', background_color=(0.9, 0.4, 0.5, 0.8), size_hint=(0.7, 1))
        self.go_btn.bind(on_release=self.on_go_pressed)
        bottom.add_widget(self.exit_btn); bottom.add_widget(self.go_btn)
        self.main_layout.add_widget(bottom); self.add_widget(self.main_layout)

    def update_global_bg(self, *args): self.bg_rect.pos, self.bg_rect.size = self.pos, self.size
    def update_header_bg(self, *args): self.header_bg.pos, self.header_bg.size = self.header.pos, self.header.size

    def on_enter(self):
        """进入游戏，开始第一关"""
        base_diff = getattr(App.get_running_app(), 'selected_difficulty', 1)
        # 根据大难度基调，决定起始关卡的参数
        self.current_stage = 1
        self.base_difficulty = base_diff
        self.score_manager.reset()
        self.load_stage_config()

    def load_stage_config(self):
        """ 连续关卡核心机制：动态配置每一关的网格和目标"""
        stage = self.current_stage
        # ⭐修改难度步数及临界分值
        # 网格扩容逻辑：第一关 7x7, 第二关 8x8, 第三关 10x10...
        if stage == 1: cols, rows, turns, target = 7, 7, 10, 8000
        elif stage == 2: cols, rows, turns, target = 7, 8, 15, 12000
        elif stage == 3: cols, rows, turns, target = 8, 8, 20, 15000
        elif stage == 4: cols, rows, turns, target = 8, 9, 25, 20000
        elif stage == 5: cols, rows, turns, target = 9, 9, 35, 30000
        else: cols, rows, turns, target = 10, 10, 25, 60 + (stage-3)*3000
        
        self.turns_left = 999 if self.base_difficulty == 1 else turns
        self.target_score = target
        
        # 难度递增：根据关卡决定特殊道具和障碍物刷新率
        logic_diff = 1 if stage == 1 else (2 if stage == 2 else 3)
        
        # 让大脑和UI同时重建！
        self.board.game_logic.load_level(cols, rows, logic_diff)
        self.board.rebuild_board(cols, rows)
        self.update_ui_text()

    def update_ui_text(self):
        self.score_label.text = f"得分: {self.score_manager.current_score} / 目标: {self.target_score}"
        self.turn_label.text = f"第{self.current_stage}关 | 步数: {'∞' if self.turns_left > 100 else self.turns_left}"

    def on_go_pressed(self, instance):
        if len(self.board.game_logic.path) > 1:
            self.go_btn.disabled = True
            
            def after_animation():
                if self.turns_left < 900: self.turns_left -= 1
                self.score_manager.add_score(self.score_manager.calculate_line_score(len(self.board.game_logic.path)))
                self.update_ui_text()
                
                # 消除并长出新材料
                self.board.game_logic.execute_collection()
                
                # 死局检测与洗牌接入！
                if self.board.game_logic.check_deadlock():
                    self.board.game_logic.shuffle()
                    self.board.animate_shuffle()

                self.board.refresh_all_cells()
                self.board.floating_score.opacity = 0 
                self.go_btn.disabled = False
                
                # 胜负判定：分够了进入下一关，步数没了游戏结束
                if self.score_manager.current_score >= self.target_score:
                    self.current_stage += 1
                    self.load_stage_config()
                elif self.turns_left <= 0: 
                    self.trigger_settlement(True)

            self.board.animate_basket_move(after_animation)

    def trigger_settlement(self, is_game_over):
        ResultDialog(final_score=self.score_manager.current_score, stars=self.score_manager.get_star_rating(),
                     on_restart_callback=self.on_enter, on_exit_callback=self.return_to_menu).open()

    def return_to_menu(self): self.score_manager.reset(); self.manager.current = 'main_menu'

class ConnectApp(App):
    selected_difficulty = 1 
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    ConnectApp().run()