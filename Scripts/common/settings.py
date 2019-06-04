import json
import os.path as path


class Settings:

    settings_file_path = 'settings.json'

    def __init__(self):
        current_dir = path.dirname(__file__)
        file_path = path.join(current_dir, f"{Settings.settings_file_path}")
        self.file_path = file_path
        
        with open(self.file_path, 'r') as settings_file:
            data = json.load(settings_file)

        self.piece_sham_chance = data["piece_sham_chance"]
        self.new_piece_freq = data["new_piece_freq"]
        self.initial_piece_count = data["initial_piece_count"]
        self.board_width = data["board_width"]
        self.task_area_length = data["task_area_length"]  # this means height
        self.goal_area_length = data["goal_area_length"]  # this means height
        self.player_count_per_team = data["player_count_per_team"]
        self.goal_definition = data["goal_definition"]
        self.game_name = data["game_name"]

    def print(self):
        for attr, value in self.__dict__.items():
            print(f'>    {attr}: {value}')