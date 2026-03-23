class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.content = None  # 内部装载的内容：Item, Obstacle, 或者特殊标识(如'篮子')

    def is_empty(self):
        return self.content is None

    def is_obstacle(self):
        # 【解耦修复】：不需要 import Obstacle 类
        # 直接检查 content 对象自身是否带有一个为 True 的 is_obstacle 属性
        return getattr(self.content, 'is_obstacle', False)

    def get_color(self):
        # 【解耦修复】：不需要 import Item 类
        # 直接尝试获取 content 对象的 color 属性
        if self.content and not self.is_obstacle() and self.content != '篮子':
            return getattr(self.content, 'color', None)
        return None

    def __str__(self):
        if self.content == '篮子':
            return "[篮子]"
        if self.content is None:
            return "[ 空 ]"
        return str(self.content)