import uuid

# Called GmPlayer to avoid confusion with bot's internal player class

class GmPlayer:

    def __init__(self, id: uuid.uuid4, team: str, x: int = None, y: int = None, is_leader: bool = False):
        self.id = id
        self.x = x
        self.y = y
        self.team = team
        self.is_leader = is_leader
        self.piece = None

    def move(self, from_square, to_square):
        from_square.player = None

        to_square.player = self
        self.x = to_square.x
        self.y = to_square.y

    def pick_up(self, square):
        self.piece = square.piece
        square.piece = None

    def put_down_on(self, square):
        square.piece = self.piece
        self.piece = None