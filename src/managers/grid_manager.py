import random

# ==========================================
#  实体类定义
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
        self.type = sp_type 
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
#  核心逻辑管理器 (支持动态尺寸与洗牌)
# ==========================================
class GridManager:
    def __init__(self, cols=7, rows=7):
        self.cols, self.rows = cols, rows
        self.grid = []
        self.path = []
        self.basket_pos = (3, 0)
        self.current_line_target_color = None
        self.current_difficulty = 1
        self.load_level(cols, rows, 1)

    # 支持动态行列，并在初始化时赋予特殊道具极小概率的自然生成
    def load_level(self, cols, rows, difficulty=1):
        self.cols = cols
        self.rows = rows
        self.current_difficulty = difficulty
        # 篮子始终在最底部的中间
        self.basket_pos = (self.cols // 2, 0)
        
        self.grid = [[Cell(x, y) for x in range(self.cols)] for y in range(self.rows)]
        self.grid[self.basket_pos[1]][self.basket_pos[0]].content = '篮子'
        
        self.path = []
        self.current_line_target_color = None

        obs_rate = 0.05
        base_len = max(5, int((cols * rows) * 0.15)) 
        
        # 即使是第一关(新手)，也保底给一个宝箱，让玩家体验机制
        if difficulty == 1:
            self._plant_path(length=base_len, items=['chest']) 
            obs_rate = 0.02

        elif difficulty == 2:
            self._plant_path(length=base_len + 5, items=['jelly'])
            obs_rate = 0.05

        elif difficulty == 3:
                self._plant_path(length=base_len + 5, items=['chest','jelly'])
                obs_rate = 0.05
                obs_rate = 0.08

        elif difficulty == 4:
                self._plant_path(length=base_len + 5, items=['chest', 'jelly'])
                obs_rate = 0.08
                obs_rate = 0.08       
        else: 
            self._plant_path(length=base_len + 10, items=['jelly', 'chest', 'jelly'])
            obs_rate = 0.12

        # 填充剩余空格
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x].is_empty() and (x, y) != self.basket_pos:
                    if random.random() < obs_rate:
                        self.grid[y][x].content = Obstacle()
                    else:
                        # 极小概率的自然生成机制
                        rand_val = random.random()
                        if rand_val < 0.02:    # 2% 概率生成宝箱
                            self.grid[y][x].content = SpecialItem('chest')
                        elif rand_val < 0.04:  # 2% 概率生成果冻
                            self.grid[y][x].content = SpecialItem('jelly')
                        else:
                            self.grid[y][x].content = Item()

        # 填充剩余空格
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x].is_empty() and (x, y) != self.basket_pos:
                    if random.random() < obs_rate:
                        self.grid[y][x].content = Obstacle()
                    else:
                        self.grid[y][x].content = Item()

    # 死局检测
    def check_deadlock(self):
        """检测篮子周围是否没有任何可以连接的格子"""
        bx, by = self.basket_pos
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            nx, ny = bx + dx, by + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                cell = self.grid[ny][nx]
                # 只要周围有不是障碍物、不是空位、且不是篮子本身的格子，就不是死局
                if not cell.is_empty() and not cell.is_obstacle() and cell.content != '篮子':
                    return False
        print("⚠️ 触发死局检测：无路可走！")
        return True


    def shuffle(self):
            """ 修改：死局洗牌时，除了保留原有的特殊道具，新生成的材料也享受掉落概率"""
            print("🔄 正在执行全局洗牌...")
            self.path = []
            self.current_line_target_color = None
            
            # 收集当前盘面上的特殊道具类型，以保证洗牌后不被吞掉
            special_items_to_keep = []
            for y in range(self.rows):
                for x in range(self.cols):
                    cell = self.grid[y][x]
                    if cell.is_special():
                        special_items_to_keep.append(getattr(cell.content, 'type'))
            
            # 强行种植一条能够连通的保底路径
            golden_len = max(5, int((self.cols * self.rows) * 0.1))
            golden_path = self._generate_golden_path(golden_len)
            
            # 清空除篮子和障碍物外的所有内容
            for y in range(self.rows):
                for x in range(self.cols):
                    cell = self.grid[y][x]
                    if not cell.is_obstacle() and (x, y) != self.basket_pos:
                        cell.content = None

            # 重新填充保底路径
            if golden_path:
                c = random.choice(Item.COLORS)
                for (px, py) in golden_path:
                    if (px, py) != self.basket_pos and not self.grid[py][px].is_obstacle():
                        self.grid[py][px].content = Item(color=c)

            # 填补其余空位
            for y in range(self.rows):
                for x in range(self.cols):
                    if self.grid[y][x].is_empty():
                        if special_items_to_keep and random.random() < 0.1:
                            self.grid[y][x].content = SpecialItem(special_items_to_keep.pop())
                        else:
                            #  洗牌重置时也保持 2%~4% 的特殊道具掉率
                            rand_val = random.random()
                            if rand_val < 0.02:
                                self.grid[y][x].content = SpecialItem('chest')
                            elif rand_val < 0.04:
                                self.grid[y][x].content = SpecialItem('jelly')
                            else:
                                self.grid[y][x].content = Item()
                            
            # 如果还有没放下的特殊道具，随便找个普通材料替换，保证不少
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
                self.path.append(target)
                return True
            
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
        self.current_line_target_color = None
        if len(self.path) < 2: return
        for i in range(1, len(self.path)):
            cell = self.path[i]
            if cell.is_special() and getattr(cell.content, 'type', None) == 'jelly':
                self.current_line_target_color = None
            else:
                self.current_line_target_color = cell.get_color()

    def execute_collection(self):
        """修改：消耗路径并移动篮子后，填补空位时也有极小概率掉落特殊道具"""
        if len(self.path) <= 1: return
        last_cell = self.path[-1]
        new_basket_pos = (last_cell.x, last_cell.y)

        # 清空轨迹
        for cell in self.path:
            cell.content = None
        
        self.basket_pos = new_basket_pos
        self.grid[new_basket_pos[1]][new_basket_pos[0]].content = '篮子'
        
        # 遍历全局，为刚才置空的位置长出新材料
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x].is_empty() and (x, y) != self.basket_pos:
                    #  每次消耗补全时，少量随机刷出宝箱和果冻
                    rand_val = random.random()
                    if rand_val < 0.02:   # 2%概率生成宝箱
                        self.grid[y][x].content = SpecialItem('chest')
                    elif rand_val < 0.04: # 2%概率生成果冻
                        self.grid[y][x].content = SpecialItem('jelly')
                    else:
                        self.grid[y][x].content = Item()

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