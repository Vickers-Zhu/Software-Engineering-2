import random as rand
import pubsub.pub as pub
import uuid
import math
import copy
import time

import common.settings as s
import board as b
import common.player as p
import common.messages as m
import common.square as sqr

# This class holds the state of the game - the board and the players. It is in charge of applying game logic to the board.
# Generally this code should be considered internal,
#   to interact with the gm it is better to use the GmExternal class


class GM:

    def __init__(self, settings: s.Settings):
        self.id = uuid.uuid4()
        self.board = b.Board(settings)

        # Select random goal areas to be goal fields
        self.board.random_select_fields()
        # Add pieces randomly to board
        self.board.random_select_pieces()

        self.settings = settings
        self.game_over = False

        self.red_team = []
        self.blue_team = []
        self.players = {}

    # shorthand of the full pub sending function
    # server refers to the external class communicating with gm (does not need to be an actual server)
    def send(self, msg: m.Message):
        # Send message to server
        pub.sendMessage(topicName='server', arg1=msg)

        # Send current board for visualization
        pub.sendMessage('gui', arg1=copy.deepcopy(self.board) )

    # Pick up action
    def player_pick_up(self, msg):
        player = self.get_player(msg.id)
        if player is None:
            self.send(m.UnkownGuidError(f'Unknown guid: {msg.id}'))
            return

        square = self.board.get_square(player.x, player.y)
       
        # If square has a piece and player does not
        if square.piece is not None and player.piece is None:
            player.pick_up(square)
            msg = m.PickUpData(result='OK', id=player.id)
        else:
            msg = m.PickUpData(result='denied', id=player.id)
        self.send(msg)

    # Tells the board to add a new piece
    def add_new_piece(self):
        self.board.new_piece()

    # Test piece action
    def test_piece(self, msg):
        player = self.get_player(msg.id)
        if player is None:
            self.send(m.UnkownGuidError(f'Unknown guid: {msg.id}'))
            return

        if player.piece is None:
            msg = m.TestData(id=player.id, result='denied', test='null')
            self.send(msg)
            return

        if player.piece.is_sham:
            msg = m.TestData(id=player.id, result='OK', test='true')
        else:
            msg = m.TestData(id=player.id, result='OK', test='false')

        self.send(msg)

    # Join game action
    def join_game(self, msg):
        # Get preferred team
        preferred_team = msg.preferred_team
        id = msg.id

        team_count = self.settings.player_count_per_team

        # Check if any spots are available
        if len(self.players) == team_count * 2:
            msg = m.ConfirmJoiningGame(response='denied', type='player', id=id)
            self.send(msg)
            return

        red_count = len(self.red_team)
        blue_count = len(self.blue_team)

        # Place in preferred team if possible
        if (preferred_team == 'red' and red_count < team_count) or (preferred_team == 'blue' and blue_count < team_count):
            team = preferred_team
        else:
            team = 'blue' if blue_count < team_count else 'red'

        player = p.GmPlayer(id=msg.id, team=team)

        # Add to corresponding team
        if team == 'red':
            self.red_team.append(player)
        else:
            self.blue_team.append(player)

        # Add to player dictionary
        self.players[player.id] = player

        # Locate spot for player on task area
        sq = rand.choice(self.board.task_area)
        available = len(self.board.task_area) - len(self.players)
        while available > 0:
            if sq.player is None:
                break
            sq = rand.choice(self.board.task_area)
            available -= 1

        # Place player on square
        player.x = sq.x
        player.y = sq.y
        sq.player = player

        # Send confirmation message
        msg = m.ConfirmJoiningGame(response='OK', type='player', id=player.id)
        self.send(msg)

        # Check if game is full
        if len(self.red_team) == len(self.blue_team) and len(self.red_team) == team_count:
            # First to join are set as leaders
            self.red_team[0].is_leader = True
            self.blue_team[0].is_leader = True

            # Send game start messages
            self.send_game_messages()

    # Sends game start msg and info to each player
    def send_game_messages(self):

        for plr in self.red_team + self.blue_team:
            role = 'member' if not plr.is_leader else 'leader'
            location = {"x": plr.x, "y": plr.y}
            board = {
                "width": self.board.board_width,
                "tasksHeight": self.board.task_area_height,
                "goalsHeight": self.board.goal_area_height
            }
            team = self.red_team if plr.team == 'red' else self.blue_team
            team_guids = [p.id for p in team]
            msg = m.GameMessage(
                id = plr.id, team = plr.team, role = role, team_size = self.settings.player_count_per_team, team_guids = team_guids, location = location, board = board)
            self.send(msg)

        # Start adding pieces
        pub.sendMessage(topicName='start-pieces')

    # Return player based on given id, None if not found
    def get_player(self, player_id: uuid.uuid4()):
        return self.players.get(player_id)

    def move_player(self, msg):
        player_id = msg.id
        direction = msg.dir

        player = self.get_player(player_id)
        if player is None:
            self.send(m.UnkownGuidError(f'Unknown guid: {msg.id}'))
            return

        x = player.x
        y = player.y
        old_square = self.board.get_square(x, y)

        if direction == 'N':
            y = y + 1
        elif direction == 'W':
            x = x - 1
        elif direction == 'S':
            y = y - 1
        elif direction == 'E':
            x = x + 1
        else:
            self.send(m.MessageTranslationError("Unkown direction:" + direction))
            return

        # Check if movement is allowed
        if not self.can_move(x, y, player.team):
            msg = m.MoveData(result='denied', id=player_id)
        else:
            sq = self.board.get_square(x, y)
            player.move(old_square, sq)

            msg = m.MoveData(result='OK', id=player_id,
                             manhattanDistance=self.find_man_dist(sq))

        self.send(msg)

    # Finds the closest piece, in terms of Manhattan distance
    def find_man_dist(self, square: sqr.Square) -> int:
        if square.piece is not None:
            return 0

        # If in the goal area send null (None in python)
        if self._in_goal_area(square.type):
            return None

        closest = math.inf
        x1 = square.x
        y1 = square.y
        for sq in self.board.content:
            if sq.piece is not None:
                d = self._dist(x1, sq.x, y1, sq.y)
                closest = d if d < closest else closest

        # Can happen if the board has no pieces
        if closest == math.inf:
            return None
        return closest

    # Helper function, hides away a long if statement
    def _in_goal_area(self, sq_type: sqr.SquareType):
        a = sq_type == sqr.SquareType.RedGoalArea
        b = sq_type == sqr.SquareType.RedGoalField
        c = sq_type == sqr.SquareType.BlueGoalArea
        d = sq_type == sqr.SquareType.BlueGoalField
        return a or b or c or d

    # Calculates Manhattan distance between two points
    def _dist(self, x1, x2, y1, y2):
        return abs(x1 - x2) + abs(y1 - y2)

    # Checks if a move is allowed
    def can_move(self, x: int, y: int, team: str) -> bool:
        sq = self.board.get_square(x, y)

        if sq is None:
            return False
        elif sq.player is not None:
            return False
        elif (sq.type == sqr.SquareType.BlueGoalField or sq.type == sqr.SquareType.BlueGoalArea) and team == 'red':
            return False
        elif (sq.type == sqr.SquareType.RedGoalArea or sq.type == sqr.SquareType.RedGoalField) and team == 'blue':
            return False
        else:
            return True

    def discover(self, msg):
        player = self.get_player(msg.id)
        if player is None:
            self.send(m.UnkownGuidError(f'Unknown guid: {msg.id}'))
            return

        scope_x = msg.location["x"]
        scope_y = msg.location["y"]

        square = self.board.get_square(scope_x, scope_y)

        if square is None:
            msg = m.DiscoverData(player.id, 'denied')
            self.send(msg)
            return

        fields = []
        # Locate all fields around player and gather their info
        for x in range(square.x - 1, square.x + 2):  # not including
            for y in range(square.y - 1, square.y + 2):
                sq = self.board.get_square(x, y)
                if sq is not None:
                    value = {
                        "manhattanDistance": self.find_man_dist(sq),
                        "contains": sq.get_type_msg(),
                        "userGuid": None if sq.player is None else sq.player.id
                    }
                    fields.append({
                        "x": sq.x,
                        "y": sq.y,
                        "value": value,
                    })

        msg = m.DiscoverData(player.id, 'OK', location=msg.location, fields=fields)
        self.send(msg)

    # Checks if given team has won
    def has_team_won(self, team) -> bool:
        if team == 'red':
            count = 0
            for sq in self.board.goal_area_red:
                if sq.discovered and sq.type == sqr.SquareType.RedGoalField:
                    count += 1
        elif team == 'blue':
            count = 0
            for sq in self.board.goal_area_blue:
                if sq.discovered and sq.type == sqr.SquareType.BlueGoalField:
                    count += 1

        has_won = count == self.settings.goal_definition

        if has_won:
            self.game_over = True

        return has_won

    def place_piece(self, msg):

        player = self.get_player(msg.id)
        if player is None:
            self.send(m.UnkownGuidError(f'Unknown guid: {msg.id}'))
            return

        square = self.board.get_square(player.x, player.y)
        assert square is not None

        # Player has no piece
        if player.piece is None:
            msg = m.PlaceData(player.id, 'denied', 'null')
            self.send(msg)
            return

        # Can't put down
        if square.piece is not None:
            msg = m.PlaceData(player.id, 'denied', 'null')
            self.send(msg)
            return

        # Simple put down
        if square.type == sqr.SquareType.TaskArea and square.piece is None:
            player.put_down_on(square)
            msg = m.PlaceData(player.id, 'OK', 'meaningless')
            self.send(msg)
            return

        # Meaningless, but can
        if square.type == sqr.SquareType.RedGoalArea or square.type == sqr.SquareType.BlueGoalArea:
            msg = m.PlaceData(player.id, 'OK', 'meaningless')
            player.put_down_on(square)
            self.send(msg)
            return

        # Placed on discovered field
        if (square.type == sqr.SquareType.RedGoalField or square.type == sqr.SquareType.BlueGoalField) and square.discovered:
            # square.discover()
            # player.put_down(square)
            msg = m.PlaceData(player.id, 'denied', 'null')
            self.send(msg)
            return

        # Undiscovered goal field
        if (square.type == sqr.SquareType.RedGoalField or square.type == sqr.SquareType.BlueGoalField) and not square.discovered:
            
            # Correct placement
            if not player.piece.is_sham:
                # Set square as discovered
                square.discovered = True

                # Destroy piece
                player.piece = None
                square.piece = None

                msg = m.PlaceData(player.id, 'OK', 'correct')
                self.send(msg)
            
            # Can't place sham on goal field
            elif player.piece.is_sham:
                msg = m.PlaceData(player.id, 'denied', 'null')
                self.send(msg)
                return 

            # Check if game is won
            if self.has_team_won(player.team):
                self.send_game_over(player.team)
            return

    def destroy_piece(self, msg: m.DestroyPiece):
        pl = self.get_player(msg.id)
        if pl is None:
            self.send(m.UnkownGuidError(f'Unknown guid: {msg.id}'))
            return

        # Not holding a piece
        if pl.piece is None:
            msg = m.DestroyPieceData(id=pl.id, result="denied")
            self.send(msg)
            return

        # Holding a piecce
        else:
            pl.piece = None
            msg = m.DestroyPieceData(id=pl.id, result="OK")
            self.send(msg)
            return

    def send_game_over(self, winning_team):
        # Send game over messages with winning team as result
        
        msg = m.GameOver(result=winning_team)
        self.send(msg)

        print(f' ***** {winning_team} won *****')
        for pl in self.blue_team + self.red_team:
            res = 'won' if pl.team == winning_team else 'lost'
            print(f'      player ({pl.id}), {pl.team} has {res}')

        # Stop game
        self.game_over = True
        pub.sendMessage('end_internal', msg=winning_team)
