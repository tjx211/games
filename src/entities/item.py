import random

class Item:
    # 预设6种基础颜色/类型
    COLORS = ['蓝鱼', '橘盘', '粉纸', '紫结', '粉花', '蓝心']

    def __init__(self, color_name=None):
        # 如果未指定颜色，则随机生成一种
        self.color = color_name if color_name else random.choice(self.COLORS)
    
    def __str__(self):
        # 控制台打印时使用简写格式
        return f"[{self.color}]"