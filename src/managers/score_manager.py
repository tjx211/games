class ScoreManager:
    def __init__(self):
        self.current_score = 0
        
        # 基础分配置
        self.base_points_per_item = 100
        
        # 3星级打分逻辑：分数阈值 (您可以根据后续关卡难度随意调整)
        self.star_thresholds = {
            1: 1500,  # 达到 1500 分：1星
            2: 3500,  # 达到 3500 分：2星
            3: 6000   # 达到 6000 分：3星
        }

    def calculate_line_score(self, path_length):
        """
        计算单次连线的得分。
        逻辑：连线越长，倍率越高 (Combo加成)
        """
        collected_count = path_length - 1 # 不包含篮子
        if collected_count <= 0:
            return 0
            
        # 连击倍率计算：每多连一个，倍率增加 0.2
        # 例如：连2个倍率1.0，连3个1.2，连5个1.6
        combo_multiplier = 1.0 + (collected_count - 1) * 0.2
        
        points = int(collected_count * self.base_points_per_item * combo_multiplier)
        return points

    def add_score(self, points):
        """累加分数"""
        self.current_score += points
        return self.current_score

    def get_star_rating(self):
        """根据当前总分结算星级 (返回 0, 1, 2, 3)"""
        if self.current_score >= self.star_thresholds[3]:
            return 3
        elif self.current_score >= self.star_thresholds[2]:
            return 2
        elif self.current_score >= self.star_thresholds[1]:
            return 1
        return 0

    def reset(self):
        """重置分数（用于重新开始游戏）"""
        self.current_score = 0