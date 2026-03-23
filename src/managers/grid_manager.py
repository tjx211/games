import random

# ==========================================
# 🧩 实体类定义
# ==========================================
class Item:
    COLORS = ['蓝鱼', '橘盘', '粉纸', '紫结', '粉花', '蓝心']
    def __init__(self, color=None):
        self.color = color if color else random.choice(self.COLORS)
    def __str__(self): return f"[{self.color}]"

class Obstacle:
    def __init__(self): self.is_obstacle = True
    def __str__(self): return "[障碍]"

class SpecialItem:
    def __init__(self, sp_type):
        self.is_special = True
        self.type = sp_type # 'jelly' (果冻) / 'chest' (宝箱)
    def __str__(self): return f"[SP:{self.type}]"

class Cell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.content = None
    def is_empty(self): return self.content is None
    def is_obstacle(self): return getattr(self.content, 'is_obstacle', False)
    def is_special(self): return getattr(self.content, 'is_special', False)
    def get_color(self):
        if self.content and not self.is_obstacle() and not self.is_special() and self.content != '篮子':
            return getattr(self.content, 'color', None)
        return None

# ==========================================
# 🧠 核心逻辑管理器
# ==========================================
class GridManager:
    def __init__(self, cols=7, rows=7):
        self.cols, self.rows = cols, rows
        self.grid = []
        self.path = []
        # 记录篮子的实时坐标，初始位置为最下面中间 (3, 0)
        self.basket_pos = (3, 0)
        self.current_line_target_color = None
        
        self.init_board(difficulty=1)

    def init_board(self, difficulty=1):
        """根据难度初始化棋盘，重置篮子到初始点"""
        self.current_difficulty = difficulty
        self.basket_pos = (3, 0) # 初始轮次重置到 (3, 0)
        self.grid = [[Cell(x, y) for x in range(self.cols)] for y in range(self.rows)]
        
        # 安放篮子
        bx, by = self.basket_pos
        self.grid[by][bx].content = '篮子'
        
        self.path = []
        self.current_line_target_color = None

        obs_rate = 0.05
        # 启发式生成：根据难度“种植”黄金路径
        if difficulty == 1:
            self._plant_path(length=6, items=[]) 
            obs_rate = 0.02
        elif difficulty == 2:
            self._plant_path(length=15, items=['chest'])
            obs_rate = 0.08
        elif difficulty == 3:
            # 困难模式：保底生成 20 连的长路径，包含果冻换色
            self._plant_path(length=20, items=['jelly', 'chest'])
            obs_rate = 0.15

        # 填充剩余空格（跳过篮子）
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x].is_empty() and (x, y) != self.basket_pos:
                    if random.random() < obs_rate:
                        self.grid[y][x].content = Obstacle()
                    else:
                        self.grid[y][x].content = Item()

    # ==========================================
    # 🕹️ 连线校验 (多级状态机)
    # ==========================================
    def connect(self, x, y):
        target = self.grid[y][x]
        if target.is_obstacle(): return False

        # 核心逻辑：必须从“篮子当前坐标”开始连线
        if not self.path:
            if (x, y) == self.basket_pos:
                self.path.append(target)
                self.current_line_target_color = None
                return True
            return False

        # 撤销逻辑
        if len(self.path) >= 2 and target == self.path[-2]:
            self.path.pop()
            self._recalculate_line_color_state()
            return True

        if target in self.path: return False

        # 8方向相邻校验
        last = self.path[-1]
        if max(abs(last.x - target.x), abs(last.y - target.y)) == 1:
            # 处理特殊道具
            if target.is_special():
                sp_type = getattr(target.content, 'type', None)
                if sp_type == 'jelly':
                    self.current_line_target_color = None # 经过果冻，开启换色授权
                self.path.append(target)
                return True
            
            # 处理普通材料
            color = target.get_color()
            if self.current_line_target_color is None:
                self.current_line_target_color = color
                self.path.append(target)
                return True
            elif color == self.current_line_target_color:
                self.path.append(target)
                return True
                
        return False

    def _recalculate_line_color_state(self):
        """回退时重新计算路径颜色状态"""
        self.current_line_target_color = None
        if len(self.path) < 2: return
        for i in range(1, len(self.path)):
            cell = self.path[i]
            if cell.is_special():
                if getattr(cell.content, 'type', None) == 'jelly':
                    self.current_line_target_color = None
            else:
                self.current_line_target_color = cell.get_color()

    # ==========================================
    # 🚀 执行收集与补全逻辑
    # ==========================================
    def execute_collection(self):
        """消除路径，补全新材料，并将篮子固定到新起点"""
        if len(self.path) <= 1: return
        
        # 1. 记录本轮路径的最后一个格子的坐标
        last_cell = self.path[-1]
        new_basket_pos = (last_cell.x, last_cell.y)

        # 2. 将连线上的所有格子（包括旧篮子的初始位置）彻底置空
        for cell in self.path:
            cell.content = None
        
        # 3. 在新位置安放篮子，更新内部坐标记录
        self.basket_pos = new_basket_pos
        self.grid[new_basket_pos[1]][new_basket_pos[0]].content = '篮子'
        
        # 4. 遍历全局：只把为空的格子（即刚刚连线的轨迹起点和沿途）填上新材料，其余不变！
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x].is_empty() and (x, y) != self.basket_pos:
                    self.grid[y][x].content = Item()

        # 5. 重置本轮连线状态
        self.path = []
        self.current_line_target_color = None

    # ==========================================
    # 🎲 启发式路径生成辅助
    # ==========================================
    def _plant_path(self, length, items):
        """强行在棋盘生成一条可以连通的长路径"""
        path_coords = self._generate_golden_path(length)
        if not path_coords: return
        
        colors = random.sample(Item.COLORS, len(items) + 1 if 'jelly' in items else 1)
        current_color_idx = 0
        
        # 道具投放逻辑
        item_pos = {}
        if items:
            step = len(path_coords) // (len(items) + 1)
            for i, it in enumerate(items):
                pos = (i + 1) * step
                item_pos[pos] = it

        for i, (px, py) in enumerate(path_coords):
            # 跳过起点，起点已经是篮子了
            if (px, py) == self.basket_pos: continue
            
            if i in item_pos:
                it_type = item_pos[i]
                self.grid[py][px].content = SpecialItem(it_type)
                if it_type == 'jelly': current_color_idx += 1
            else:
                c = colors[min(current_color_idx, len(colors)-1)]
                self.grid[py][px].content = Item(color=c)

    def _generate_golden_path(self, length):
        """DFS 随机游走寻找黄金路径"""
        for _ in range(100):
            # 起点必须是当前的篮子位置
            sx, sy = self.basket_pos
            p = [(sx, sy)]; vis = {(sx, sy)}
            for _ in range(length - 1):
                lx, ly = p[-1]
                nb = []
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                    nx, ny = lx+dx, ly+dy
                    if 0<=nx<self.cols and 0<=ny<self.rows and (nx,ny) not in vis:
                        nb.append((nx,ny))
                if not nb: break
                nxt = random.choice(nb); p.append(nxt); vis.add(nxt)
            if len(p) >= length * 0.7: return p
        return []