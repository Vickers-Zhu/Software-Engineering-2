import time
import datetime
import csv
import os.path as path
import os

# Logs game messages from the gm (as descrived in the documentation)

class Logger:
    log_dir = 'logs'
    columns = ['Type', 'Timestamp', 'Game ID', 'Player GUID', 'Colour', 'Role']

    def __init__(self, game_id):
        self.game_id = game_id

        self._log = []
        self._log.append(Logger.columns)

        current_dir = path.dirname(__file__)
        file_path = path.join(
            current_dir, f"{Logger.log_dir}\\{game_id}_{time.time()}.csv")

        self.log_path = file_path

    @staticmethod
    def get_ts():
        return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

    def log(self, msg, player):

        if player is None:
            player_team = 'Unknown'
            player_role = 'Unknown'
        else:
            player_team = player.team
            player_role = 'member' if not player.is_leader else 'leader'

        msg_type = type(msg).__name__
        timestamp = Logger.get_ts()
        game_id = self.game_id
        # Don't know about player id vs guid difference, currently only using player guid
        player_id = msg.id if msg is not None else 'Unknown'
        color = player_team
        role = player_role

        self._log.append(
            [msg_type, timestamp, game_id, player_id, color, role])
        # print('logger: ', msg_type, timestamp, game_id, player_id, color, role)

    def save_log(self):
        print(f'> logger: Saving log to \"{self.log_path}\"')

        dir_path = path.join(path.dirname(__file__), Logger.log_dir)
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)

        with open(self.log_path, 'w+') as log_file:
            wr = csv.writer(log_file)
            wr.writerows(self._log)