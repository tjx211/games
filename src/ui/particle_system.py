import random
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

class Particle:
    # ⭐ 独立的粒子物理实体
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # ⭐ 赋予极坐标系下的随机初速度 (向四周飞溅)
        self.vx = random.uniform(-180, 180)
        self.vy = random.uniform(50, 300)
        
        self.life = 0.5  # 存活时间 0.5 秒
        self.max_life = 0.5
        self.size = random.uniform(5, 10)
        
        # ⭐ 使用金黄色系的光效配色
        r = random.uniform(0.8, 1.0)
        g = random.uniform(0.8, 1.0)
        b = random.uniform(0.2, 0.6)
        self.color_instr = Color(r, g, b, 1) 
        self.rect_instr = Rectangle(pos=(self.x, self.y), size=(self.size, self.size))

    def update(self, dt):
        # ⭐ 物理公式：Y轴重力下坠
        self.vy -= 800 * dt 
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        
        # ⭐ Alpha 透明度随寿命线性衰减
        alpha = max(0, self.life / self.max_life)
        self.color_instr.a = alpha
        
        self.rect_instr.pos = (self.x, self.y)
        return self.life > 0

class ParticleSystem(Widget):
    # ⭐ 粒子系统发射器与生命周期管理器
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.particles = []
        # 开启 60FPS 的高频刷新帧循环
        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def burst(self, x, y, count=8):
        # ⭐ 触发一次爆裂，在指定坐标生成多个粒子
        with self.canvas:
            for _ in range(count):
                p = Particle(x, y)
                self.particles.append(p)

    def update(self, dt):
        # 遍历更新，清理已死亡粒子的渲染内存
        alive_particles = []
        for p in self.particles:
            if p.update(dt):
                alive_particles.append(p)
            else:
                self.canvas.remove(p.color_instr)
                self.canvas.remove(p.rect_instr)
        self.particles = alive_particles