import uuid as u
import enum

class SquareType(enum.Enum):
    RedGoalArea = enum.auto()
    RedGoalField = enum.auto()

    BlueGoalArea = enum.auto()
    BlueGoalField = enum.auto()

    TaskArea = enum.auto()


class Square:

    def __init__(self, x: int, y: int, type: SquareType, piece = None, player = None):
        self.id = u.uuid4()
        self.x = x
        self.y = y
        self.piece = piece
        self.player = player
        self.type = type
        self.discovered = False

    def get_type_msg(self):
        if self.player is not None:
            return "player"
        elif self.piece is not None:
            if self.piece.is_sham:
                return "sham"
            else:
                return "piece"
        else:
            return "empty"

    def discover(self):
        self.discovered = True

    # Used for debugging, present square as text (as in the documentation example)
    def __str__(self):
        t = ''
        if self.player is not None:
            t = 'R' if self.player.team == 'red' else 'B'
            if self.player.piece is not None:
                t = t + str(self.player.piece)
            elif self.piece is not None:
                t = t + '|' + str(self.piece)
        elif self.piece is not None:
            t = str(self.piece)
        elif self.discovered and (self.type == SquareType.BlueGoalArea or self.type == SquareType.RedGoalArea):
            t = 'N'
        elif self.discovered and (self.type == SquareType.BlueGoalField or self.type == SquareType.RedGoalField):
            t = 'YG'
        elif not self.discovered and (self.type == SquareType.BlueGoalField or self.type == SquareType.RedGoalField):
            t = 'G'
        return t
