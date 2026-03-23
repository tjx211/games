import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, Line
from kivy.core.window import Window
from kivy.animation import Animation
import os

from main_logic import GridManager # 导入之前的底层逻辑

Window.size = (450, 800)

# 素材映射字典：将底层颜色的名字映射到我们刚切好的图片路径
IMAGE_MAP = {
    '蓝鱼': 'assets/images/materials/fish.png',
    '橘盘': 'assets/images/materials/palette.png',
    '粉纸': 'assets/images/materials/paper.png',
    '紫结': 'assets/images/materials/bow.png',
    '粉花': 'assets/images/materials/flower.png',
    '蓝心': 'assets/images/materials/heart.png',
}

class CellWidget(Widget):
    """网格单元 UI，使用 Image 控件以支持图片和动画"""
    def __init__(self, grid_x, grid_y, **kwargs):
        super().__init__(**kwargs)
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.is_selected = False
        
        # 背景色块 (用于画棋盘底格)
        with self.canvas.before:
            Color(0.95, 0.95, 0.92, 1) # 暖色调底格
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        # 添加图片控件
        self.img = Image(allow_stretch=True, keep_ratio=True)
        self.add_widget(self.img)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        # 留出 2px 间隙作为网格线
        self.bg_rect.pos = (self.x + 2, self.y + 2)
        self.bg_rect.size = (self.width - 4, self.height - 4)
        
        # 如果没有被选中放大，图片尺寸跟随格子大小
        if not self.is_selected:
            self.img.size = (self.width - 10, self.height - 10)
            self.img.center = self.center

    def update_view(self, cell_data):
        self.is_selected = False # 重置状态
        if cell_data.content == '篮子':
            # 篮子暂时用一个占位色块代替，稍后您可以自己画一个 basket.png
            self.img.source = ''
            self.canvas.after.clear()
            with self.canvas.after:
                Color(0.8, 0.3, 0.3, 1)
                Rectangle(pos=(self.x+10, self.y+10), size=(self.width-20, self.height-20))
        elif cell_data.is_obstacle():
            self.img.source = ''
            self.canvas.after.clear()
            with self.canvas.after:
                Color(0.3, 0.3, 0.3, 1)
                Rectangle(pos=(self.x+10, self.y+10), size=(self.width-20, self.height-20))
        elif cell_data.content:
            color_name = cell_data.get_color()
            self.img.source = IMAGE_MAP.get(color_name, '')
            self.canvas.after.clear()
        else:
            self.img.source = ''
            self.canvas.after.clear()
            
        self.update_rect()

    def animate_select(self):
        """选中时的放大动画特效"""
        if not self.is_selected:
            self.is_selected = True
            # 创建动画：在 0.1 秒内放大到 1.2 倍
            target_size = (self.width * 1.2, self.height * 1.2)
            anim = Animation(size=target_size, center=self.center, duration=0.1)
            anim.start(self.img)

    def animate_deselect(self):
        """取消选中时的恢复动画"""
        if self.is_selected:
            self.is_selected = False
            target_size = (self.width - 10, self.height - 10)
            anim = Animation(size=target_size, center=self.center, duration=0.1)
            anim.start(self.img)

class GameBoard(FloatLayout):
    """主游戏区，使用 FloatLayout 以支持悬浮数字和画线"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_logic = GridManager(cols=7, rows=7)
        
        # 底部网格
        self.grid_layout = GridLayout(cols=7, rows=7, size_hint=(1, 1))
        self.add_widget(self.grid_layout)
        
        # 悬浮数字 Label (初始化为不可见)
        self.floating_score = Label(
            text="0", font_size=40, bold=True, 
            color=(1, 0.2, 0.2, 1), size_hint=(None, None), size=(50, 50), opacity=0
        )
        self.add_widget(self.floating_score)

        self.cell_widgets = {}
        self.init_board_ui()

    def init_board_ui(self):
        self.grid_layout.clear_widgets()
        self.cell_widgets.clear()
        for y in range(6, -1, -1):
            for x in range(7):
                cell_ui = CellWidget(grid_x=x, grid_y=y)
                self.grid_layout.add_widget(cell_ui)
                self.cell_widgets[(x, y)] = cell_ui
        self.refresh_all_cells()

    def refresh_all_cells(self):
        for y in range(7):
            for x in range(7):
                cell_data = self.game_logic.grid[y][x]
                self.cell_widgets[(x, y)].update_view(cell_data)
        self.draw_connection_lines()

    def on_touch_down(self, touch):
        self.process_touch(touch)

    def on_touch_move(self, touch):
        self.process_touch(touch)

    def process_touch(self, touch):
        for (x, y), cell_ui in self.cell_widgets.items():
            if cell_ui.collide_point(*touch.pos):
                old_path_len = len(self.game_logic.path)
                success = self.game_logic.connect(x, y)
                
                # 如果连接成功或者是发生了撤销
                if success or len(self.game_logic.path) != old_path_len:
                    self.update_visual_feedback()
                break

    def update_visual_feedback(self):
        """更新所有视觉反馈：连线、放大特效、悬浮数字"""
        path = self.game_logic.path
        
        # 1. 更新放大特效：判断谁在路径里
        for (x, y), cell_ui in self.cell_widgets.items():
            # 判断对应底层的 cell 对象是否在 path 中
            cell_in_path = any(c.x == x and c.y == y for c in path)
            if cell_in_path:
                cell_ui.animate_select()
            else:
                cell_ui.animate_deselect()

        # 2. 画连接线
        self.canvas.after.clear()
        if len(path) < 2:
            self.floating_score.opacity = 0 # 隐藏悬浮数字
            return

        with self.canvas.after:
            Color(1, 1, 1, 0.6) # 半透明白色粗线
            points = []
            for cell in path:
                ui_widget = self.cell_widgets[(cell.x, cell.y)]
                points.extend([ui_widget.center_x, ui_widget.center_y])
            Line(points=points, width=12, cap='round', joint='round')

        # 3. 更新悬浮数字的位置和数值
        last_cell = path[-1]
        last_widget = self.cell_widgets[(last_cell.x, last_cell.y)]
        
        # 分数 = 连线长度 - 1 (不包括篮子)
        score = len(path) - 1 
        self.floating_score.text = str(score)
        self.floating_score.opacity = 1
        # 将数字悬浮在当前手指所在格子的上方偏右
        self.floating_score.center_x = last_widget.center_x + 30
        self.floating_score.center_y = last_widget.center_y + 40

class GameScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.top_bar = Label(text="Score: 0", size_hint=(1, 0.1), font_size=30, color=(0,0,0,1))
        with self.top_bar.canvas.before:
            Color(0.9, 0.8, 0.7, 1)
            self.bg = Rectangle(pos=self.top_bar.pos, size=self.top_bar.size)
        self.top_bar.bind(pos=self.update_bg, size=self.update_bg)
        self.add_widget(self.top_bar)
        
        self.board = GameBoard(size_hint=(1, 0.7))
        self.add_widget(self.board)

        bottom_area = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), padding=30)
        self.go_button = Button(
            text="出 发 !", font_size=40, bold=True,
            background_color=(1, 0.5, 0.5, 1)
        )
        self.go_button.bind(on_press=self.on_go_pressed)
        bottom_area.add_widget(self.go_button)
        self.add_widget(bottom_area)
        
    def update_bg(self, *args):
        self.bg.pos = self.top_bar.pos
        self.bg.size = self.top_bar.size

    def on_go_pressed(self, instance):
        if len(self.board.game_logic.path) > 1:
            self.board.game_logic.execute_collection()
            self.board.refresh_all_cells()
            self.board.floating_score.opacity = 0 # 收集后隐藏数字

class ConnectApp(App):
    def build(self):
        return GameScreen()

if __name__ == '__main__':
    ConnectApp().run()