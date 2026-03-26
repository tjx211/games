import os
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, Line
from kivy.animation import Animation
from src.managers.grid_manager import GridManager
from src.managers.config_manager import ConfigManager

from src.ui.particle_system import ParticleSystem

cfg_visuals = ConfigManager.get('visuals', 'colors')
cfg_assets = ConfigManager.get('assets')
IMAGE_MAP = cfg_assets.get('materials', {})
SPECIAL_IMAGE_MAP = cfg_assets.get('special', {})

class CellWidget(Widget):
    def __init__(self, grid_x, grid_y, **kwargs):
        super().__init__(**kwargs)
        self.grid_x, self.grid_y = grid_x, grid_y
        self.is_selected = False
        self.special_type = None 
        
        with self.canvas.before:
            self.bg_color_instr = Color(*cfg_visuals.get('cell_bg', [1,1,1,0.15])) 
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
            elif self.special_type in ['jelly', 'chest', 'clock', 'star_gem']:
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
        self.bg_color_instr.a = cfg_visuals.get('cell_bg')[3] 

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
        if sp_type == 'jelly': self.glow_color.rgba = cfg_visuals.get('glow_jelly')
        elif sp_type == 'chest': self.glow_color.rgba = cfg_visuals.get('glow_chest')
        elif sp_type == 'basket': 
            self.glow_color.rgba = cfg_visuals.get('glow_basket')
            self.glow_color.a = 0.1 
        elif sp_type == 'clock': self.glow_color.rgba = [0.5, 0.8, 0.9, 0.5] 
        elif sp_type == 'star_gem': self.glow_color.rgba = [1, 0.9, 0.2, 0.5] 
        
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
        # ⭐ 1. 初始化暂停标识
        self.is_paused = False 
        
        self.game_logic = GridManager(cols=7, rows=7)
        self.grid_layout = GridLayout(cols=7, rows=7, size_hint=(None, None))
        self.add_widget(self.grid_layout)
        
        with self.canvas.before:
            Color(*cfg_visuals.get('board_gap'))
            self.bg_board = Rectangle(pos=self.pos, size=self.size)

        self.floating_score = Label(text="0", font_size=50, bold=True, color=(1, 0.2, 0.2, 1), size_hint=(None, None), size=(50, 50), opacity=0)
        self.add_widget(self.floating_score)
        
        self.particle_system = ParticleSystem()
        self.add_widget(self.particle_system)

        self.cell_widgets = {}
        self.bind(pos=self.update_layout, size=self.update_layout)

    def update_layout(self, *args):
        self.grid_layout.pos, self.grid_layout.size = self.pos, self.size
        self.bg_board.pos, self.bg_board.size = self.pos, self.size
        self.particle_system.pos = self.pos
        self.particle_system.size = self.size
        self.update_visual_feedback()

    def rebuild_board(self, cols, rows):
        self.grid_layout.cols = cols
        self.grid_layout.rows = rows
        self.grid_layout.clear_widgets()
        self.cell_widgets.clear()
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
        # ⭐ 2. 游戏暂停时，直接拦截/吃掉所有的滑动连线事件
        if getattr(self, 'is_paused', False):
            return 
            
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
                if target_ui.img.opacity > 0:
                    target_ui.img.opacity = 0
                    self.particle_system.burst(target_ui.center_x, target_ui.center_y, count=8)

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

    def animate_shuffle(self):
        for (x, y), cell_ui in self.cell_widgets.items():
            if cell_ui.special_type not in ['basket', 'barrier']:
                original_size = cell_ui.img.size
                anim = Animation(size=(0, 0), duration=0.2, t='in_quad') + \
                       Animation(size=original_size, duration=0.3, t='out_bounce')
                anim.start(cell_ui.img)