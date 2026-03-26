from src.managers.config_manager import ConfigManager

class ScoreManager:
    def __init__(self):
        self.current_score = 0
        # ⭐ 1. 单个材料的基础得分从 100 骤降为 10，防止分数虚高
        self.base_points_per_item = 10 
        
        self.star_thresholds = {
            1: 500,  
            2: 1200,  
            3: 2500   
        }

    def calculate_line_score(self, path_length, multiplier_count=0):
        collected_count = path_length - 1 
        if collected_count <= 0:
            return 0
            
        # ⭐ 2. 削弱连击加成：每多连一个仅多 10% 的加成 (原来是 20%)
        combo_multiplier = 1.0 + (collected_count - 1) * 0.1
        points = int(collected_count * self.base_points_per_item * combo_multiplier)
        
        if multiplier_count > 0:
            points *= (2 ** multiplier_count)
            
        return points

    def add_score(self, points):
        self.current_score += points
        return self.current_score

    def get_star_rating(self):
        if self.current_score >= self.star_thresholds[3]: return 3
        elif self.current_score >= self.star_thresholds[2]: return 2
        elif self.current_score >= self.star_thresholds[1]: return 1
        return 0

    def reset(self):
        self.current_score = 0