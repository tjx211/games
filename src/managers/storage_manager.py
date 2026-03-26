import os
from kivy.app import App
from kivy.storage.jsonstore import JsonStore

class StorageManager:
    # ⭐ 1. 兼容 Android 沙盒权限的本地数据持久化管理器
    _store = None

    @classmethod
    def _get_store(cls):
        # ⭐ 2. 获取或初始化 JsonStore 实例
        if cls._store is None:
            app = App.get_running_app()
            if app:
                data_dir = app.user_data_dir
            else:
                data_dir = os.path.dirname(os.path.abspath(__file__))
                
            store_path = os.path.join(data_dir, 'game_save.json')
            cls._store = JsonStore(store_path)
            
            # 初始化默认数据结构
            if not cls._store.exists('global_data'):
                cls._store.put('global_data', high_score=0)
            if not cls._store.exists('session_data'):
                cls._store.put('session_data', is_active=False)
                
        return cls._store

    @classmethod
    def save_progress(cls, stage, score, turns_left, difficulty):
        # ⭐ 3. 保存当前战局进度
        store = cls._get_store()
        store.put('session_data', 
                  is_active=True,
                  stage=stage,
                  score=score,
                  turns_left=turns_left,
                  difficulty=difficulty)

    @classmethod
    def load_progress(cls):
        # ⭐ 4. 读取当前战局进度
        store = cls._get_store()
        if store.exists('session_data'):
            data = store.get('session_data')
            if data.get('is_active', False):
                return data
        return None

    @classmethod
    def clear_progress(cls):
        # ⭐ 5. 清除当前战局进度 (通关或失败时调用)
        store = cls._get_store()
        store.put('session_data', is_active=False)

    @classmethod
    def update_high_score(cls, current_score):
        # ⭐ 6. 更新历史最高分
        store = cls._get_store()
        global_data = store.get('global_data')
        if current_score > global_data.get('high_score', 0):
            store.put('global_data', high_score=current_score)
            return True
        return False

    @classmethod
    def get_high_score(cls):
        # ⭐ 7. 获取历史最高分
        store = cls._get_store()
        return store.get('global_data').get('high_score', 0)

    @classmethod
    def has_saved_game(cls):
        # ⭐ 8. 判断是否存在可继续的游戏存档
        progress = cls.load_progress()
        return progress is not None