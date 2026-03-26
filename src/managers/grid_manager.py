import random

class Item:
    COLORS = ['蓝鱼', '橘盘', '粉纸', '紫结', '粉花', '蓝心']
    def __init__(self, color=None):
        self.color = color if color else random.choice(self.COLORS)

class Obstacle:
    def __init__(self): self.is_obstacle = True

class SpecialItem:
    def __init__(self, sp_type):
        self.is_special = True
        self.type = sp_type 

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

class GridManager:
    def __init__(self, cols=7, rows=7):
        self.cols, self.rows = cols, rows
        self.grid = []
        self.path = []
        self.basket_pos = (3, 0)
        self.current_line_target_color = None
        self.allowed_special_items = [] # 当前关卡允许生成的特殊道具池
        
        self.load_level(cols, rows, 1)

    def load_level(self, cols, rows, stage):
        # ⭐ 1. 算法递进：初始化盘面参数
        self.cols, self.rows = cols, rows
        self.stage = stage
        self.basket_pos = (self.cols // 2, 0)
        self.grid = [[Cell(x, y) for x in range(self.cols)] for y in range(self.rows)]
        self.grid[self.basket_pos[1]][self.basket_pos[0]].content = '篮子'
        self.path = []
        self.current_line_target_color = None

        # ⭐ 2. 算法递进：障碍物生成率
        # 第1关没有，第2关起步 5%，之后每关增加 1.5%，上限 20%
        obs_rate = 0.0 if stage == 1 else min(0.20, 0.05 + (stage - 2) * 0.015)

        # ⭐ 3. 算法递进：道具池管理逻辑
        pool = ['jelly', 'chest', 'clock', 'star_gem']
        if stage == 1 or stage == 2:
            # 前两关强制无特殊道具
            self.allowed_special_items = []
        elif stage == 3:
            # 第三关首次出现，随机给两个
            self.allowed_special_items = random.sample(pool, 2)
        else:
            # 第四关起：继承上一关的 1 个道具，再随机补 2 个新道具（总共3个）
            prev_items = getattr(self, 'last_level_special_items', [])
            if not prev_items:
                prev_items = random.sample(pool, 2)
                
            keep_item = random.choice(prev_items)
            others = [item for item in pool if item != keep_item]
            new_items = random.sample(others, 2)
            self.allowed_special_items = [keep_item] + new_items
            
        self.last_level_special_items = self.allowed_special_items

        # ⭐ 4. 黄金路径种植
        base_len = max(5, int((cols * rows) * 0.15))
        if not self.allowed_special_items:
            self._plant_path(length=base_len, items=[])
        else:
            # 从允许的道具池中随机挑1~3个种在必经之路上
            num_plant = min(3, stage - 2)
            items_to_plant = [random.choice(self.allowed_special_items) for _ in range(num_plant)]
            self._plant_path(length=base_len + min(5, stage), items=items_to_plant)

        self._fill_empty_cells(obs_rate)

    def _fill_empty_cells(self, obs_rate=0):
        # ⭐ 5. 核心：封装统一的填充逻辑，只使用当前关卡合法的道具池
        sp_total_rate = 0.06 if self.allowed_special_items else 0.0
        
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x].is_empty() and (x, y) != self.basket_pos:
                    if random.random() < obs_rate:
                        self.grid[y][x].content = Obstacle()
                    else:
                        if sp_total_rate > 0 and random.random() < sp_total_rate:
                            chosen_sp = random.choice(self.allowed_special_items)
                            self.grid[y][x].content = SpecialItem(chosen_sp)
                        else:
                            self.grid[y][x].content = Item()

    def check_deadlock(self):
        bx, by = self.basket_pos
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            nx, ny = bx + dx, by + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                cell = self.grid[ny][nx]
                if not cell.is_empty() and not cell.is_obstacle() and cell.content != '篮子':
                    return False
        return True

    def shuffle(self):
        self.path = []
        self.current_line_target_color = None
        
        special_items_to_keep = []
        for y in range(self.rows):
            for x in range(self.cols):
                cell = self.grid[y][x]
                if cell.is_special():
                    special_items_to_keep.append(getattr(cell.content, 'type'))
        
        golden_len = max(5, int((self.cols * self.rows) * 0.1))
        golden_path = self._generate_golden_path(golden_len)
        
        for y in range(self.rows):
            for x in range(self.cols):
                cell = self.grid[y][x]
                if not cell.is_obstacle() and (x, y) != self.basket_pos:
                    cell.content = None

        if golden_path:
            c = random.choice(Item.COLORS)
            for (px, py) in golden_path:
                if (px, py) != self.basket_pos and not self.grid[py][px].is_obstacle():
                    self.grid[py][px].content = Item(color=c)

        # 洗牌时同样调用严谨的生成方法
        self._fill_empty_cells(obs_rate=0.0)
                        
        for sp_type in special_items_to_keep:
            rx, ry = random.randint(0, self.cols-1), random.randint(0, self.rows-1)
            if not self.grid[ry][rx].is_obstacle() and (rx, ry) != self.basket_pos:
                 self.grid[ry][rx].content = SpecialItem(sp_type)

    def connect(self, x, y):
        target = self.grid[y][x]
        if target.is_obstacle(): return False

        if not self.path:
            if (x, y) == self.basket_pos:
                self.path.append(target)
                self.current_line_target_color = None
                return True
            return False

        if len(self.path) >= 2 and target == self.path[-2]:
            self.path.pop()
            self._recalculate_line_color_state()
            return True

        if target in self.path: return False

        last = self.path[-1]
        if max(abs(last.x - target.x), abs(last.y - target.y)) == 1:
            if target.is_special():
                sp_type = getattr(target.content, 'type', None)
                if sp_type == 'jelly':
                    self.current_line_target_color = None 
                # ⭐ 6. 宝箱、果冻、时钟、翻倍星 均可以作为桥接穿过
                self.path.append(target)
                return True
            
            color = target.get_color()
            if self.current_line_target_color is None or color == self.current_line_target_color:
                self.current_line_target_color = color
                self.path.append(target)
                return True
        return False

    def _recalculate_line_color_state(self):
        self.current_line_target_color = None
        if len(self.path) < 2: return
        for i in range(1, len(self.path)):
            cell = self.path[i]
            if cell.is_special() and getattr(cell.content, 'type', None) == 'jelly':
                self.current_line_target_color = None
            elif not cell.is_special():
                self.current_line_target_color = cell.get_color()

    def execute_collection(self):
        if len(self.path) <= 1: return
        last_cell = self.path[-1]
        new_basket_pos = (last_cell.x, last_cell.y)

        for cell in self.path:
            cell.content = None
        
        self.basket_pos = new_basket_pos
        self.grid[new_basket_pos[1]][new_basket_pos[0]].content = '篮子'
        
        # 消除后补空，复用严谨的统一生成函数 (暂不增加新的障碍物)
        self._fill_empty_cells(obs_rate=0.0)
        
        self.path = []
        self.current_line_target_color = None

    def _plant_path(self, length, items):
        path_coords = self._generate_golden_path(length)
        if not path_coords: return
        
        colors = random.sample(Item.COLORS, len(items) + 1 if 'jelly' in items else 1)
        current_color_idx = 0
        item_pos = {}
        if items:
            step = len(path_coords) // (len(items) + 1)
            for i, it in enumerate(items):
                pos = (i + 1) * step
                item_pos[pos] = it

        for i, (px, py) in enumerate(path_coords):
            if (px, py) == self.basket_pos: continue
            if i in item_pos:
                it_type = item_pos[i]
                self.grid[py][px].content = SpecialItem(it_type)
                if it_type == 'jelly': current_color_idx += 1
            else:
                c = colors[min(current_color_idx, len(colors)-1)]
                self.grid[py][px].content = Item(color=c)

    def _generate_golden_path(self, length):
        for _ in range(100):
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