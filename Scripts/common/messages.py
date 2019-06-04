import uuid
import json
import collections

# Contains all types of messages and their conversions to and from json format

class Message:
    def __init__(self):
        pass

    def __str__(self):
        ret = ""
        for attr, value in self.__dict__.items():
            ret += f'>    {attr}: {value}\n'
        return ret

    # For debugging
    def print(self):
        for attr, value in self.__dict__.items():
            print(f'>    {attr}: {value}')

    def to_json(self):
        """ Converts message to json """

        def serialize(obj):
            if isinstance(obj, uuid.UUID):
                serial = str(obj.hex)
                return serial

            return obj.__dict__

        j = json.dumps(self, default=serialize)
        j = j.replace('\"id\"', '\"userGuid\"')

        return j

    @staticmethod
    def from_json_gm(json_data):
        """ Converts messages sent to gm from json to corresponding message class """
        return Message._json_to_msg(json_data, Message._conv_dict_gm)
    
    @staticmethod
    def from_json_player(json_data):
        """ Converts messages sent to player from json to corresponding message class """
        return Message._json_to_msg(json_data, Message._conv_dict_player)
    
    @staticmethod
    def from_json_server(json_data):
        """ Converts messages sent to server from json to corresponding message class """
        return Message._json_to_msg(json_data, Message._conv_dict_server)


    # ======== Internals ========
    
    
    # Holds the action to Message conversion, given j is loaded json data
    _conv_dict_gm = {
        'start':   lambda j: ConfirmSetUpGame(j['result']),
        'connect': lambda j: JoinGame(j['userGuid'], j['preferredTeam'], j['type']),
        'move':    lambda j: Move(j['userGuid'], j['direction']),
        'pickup':  lambda j: PickUp(j['userGuid']),
        'test':    lambda j: TestPiece(j['userGuid']),
        'state':   lambda j: Discover(j['location'], j['userGuid']),
        'place':   lambda j: PlacePiece(j['userGuid']),
        'destroy': lambda j: DestroyPiece(j['userGuid']),
        'exchange': lambda j: Message._handleExchange(j),
        'error-translation': lambda j: MessageTranslationError(j['error']),
        'error-guid': lambda j: UnkownGuidError(j['error'])
    }

    _conv_dict_server = {
        'start':   lambda j: SetUpGame(),
        'error-translation': lambda j: MessageTranslationError(j['error']),
        'error-guid': lambda j: UnkownGuidError(j['error']),
        'gui': lambda j: GuiMessage(j['board'])
    }

    _conv_dict_player = {
        'start':   lambda j: GameMessage(j['userGuid'], j['team'], j['role'], j['teamSize'], j['teamGuids'], j['location'], j['board']),
        'connect': lambda j: ConfirmJoiningGame(j['userGuid'], j['result'], j['type']),
        'move':    lambda j: MoveData(j['userGuid'], j['result'], j['manhattanDistance']),
        'pickup':  lambda j: PickUpData(j['userGuid'], j['result']),
        'test':    lambda j: TestData(j['userGuid'], j['result'], j['test']),
        'state':   lambda j: DiscoverData(j['userGuid'], j['result'], j['location'], j['fields']),
        'place':   lambda j: PlaceData(j['userGuid'], j['result'], j['consequence']),
        'destroy': lambda j: DestroyPieceData(j['userGuid'], j['result']),
        'end':     lambda j: GameOver(j['result']),
        'exchange':lambda j: Message._handleExchange(j),
        'error-translation': lambda j: MessageTranslationError(j['error']),
        'error-guid': lambda j: UnkownGuidError(j['error'])
    }

    @staticmethod
    def _json_to_msg(json_data, conv_dict):
        """ Converts given json into a Message class if possible, returns (msg, error) """
        j = json.loads(json_data)
        try:
            msg = conv_dict[j['action']](j)
            return msg, None
        except Exception as err:
            return None, f'Could not parse json msg: {json_data}\nError: {err}'

    @staticmethod
    def _handleExchange(j):
        """ Handles json to message conversion for Knowledge exchange classes """
        if 'receiverGuid' in j:
            return AuthorizeKnowledgeExchange(j['userGuid'], j['receiverGuid'])
        elif 'rejectDuration' in j:
            return RejectKnowledgeExchange(j['userGuid'], j['rejectDuration'])
        elif 'fields' in j:
            return KnowledgeExchangeData(j['userGuid'], j['receiverGuid'], j['fields'])
        else:
            return AcceptKnowledgeExchange(j['userGuid'])


# ===== Messages from GM =====

#       Game setup

class SetUpGame(Message):
    """ Sent by gm to server on game start """

    def __init__(self):
        super().__init__()
        self.action = 'start'


class ConfirmSetUpGame(Message):
    """ Sent by server to gm on game start """

    def __init__(self, result: str):
        super().__init__()
        self.action = 'start'
        self.result = result


class ConfirmJoiningGame(Message):
    """ Sent by gm to player to confirm whether the player joined the game """

    def __init__(self, id: uuid.uuid4, response: str, type: str):
        super().__init__()
        self.action = 'connect'
        self.result = response
        self.type = type
        self.id = id
    
    def to_json(self):
        j = super(ConfirmJoiningGame, self).to_json()
        j = j.replace('\"preferred_team\"', '\"preferredTeam\"')
        return j


class GameMessage(Message):
    """ Sent by gm to player on game start, contains starting game info """

    def __init__(self, id: uuid.uuid4, team: str, role: str, team_size: int, team_guids: list, location: dict, board: dict):
        super().__init__()
        self.action = 'start'
        self.team = team
        self.role = role
        self.id = id
        self.team_size = team_size
        self.team_guids = team_guids
        self.location = location
        self.board = board
    
    def to_json(self):
        j = super(GameMessage, self).to_json()
        j = j.replace('\"team_size\"', '\"teamSize\"')
        j = j.replace('\"team_guids\"', '\"teamGuids\"')
        return j


#       Player action responses

class MoveData(Message):
    """ Sent by gm to player on as response to move message """

    def __init__(self, id: uuid.uuid4, result: str, manhattanDistance: int = None):
        super().__init__()
        self.action = 'move'
        self.result = result
        self.id = id
        self.manhattanDistance = manhattanDistance


class PickUpData(Message):
    """ Sent by gm to player as response to pick up message """

    def __init__(self, id: uuid.uuid4, result: str):
        super().__init__()
        self.action = 'pickup'
        self.result = result
        self.id = id


class TestData(Message):
    """ Sent by gm to player as response to test message """

    def __init__(self, id: uuid.uuid4, result: str, test: str):
        super().__init__()
        self.action = 'test'
        self.id = id
        self.result = result
        self.test = test


class DiscoverData(Message):
    """ Sent by gm to player as response to discover up message """

    def __init__(self, id: uuid.uuid4, result: str, location: dict = None, fields=None):
        super().__init__()
        self.action = 'state'
        self.result = result
        self.id = id
        self.location = location
        self.fields = fields


class PlaceData(Message):
    """ Sent by gm to player as response to place message """

    def __init__(self, id: uuid.uuid4, result: str, consequence: str):
        super().__init__()
        self.action = 'place'
        self.id = id
        self.result = result
        self.consequence = consequence


class DestroyPieceData(Message):
    """ Sent by gm to player as response to destroy message """

    def __init__(self, id: uuid.uuid4, result: str):
        super().__init__()
        self.action = 'destroy'
        self.id = id
        self.result = result


#       Game end
class GameOver(Message):
    """ Sent by gm to all players when the game has ended """

    def __init__(self, result: str):
        super().__init__()
        self.action = 'end'
        self.result = result


# ===== Messages to GM =====


#       Game setup

class JoinGame(Message):
    """ Sent by player to gm in order to join a game """

    def __init__(self, id: uuid.uuid4, preferred_team: str, type: str):
        super().__init__()
        self.action = 'connect'
        self.id = id
        self.preferred_team = preferred_team
        self.type = type

    def to_json(self):
        j = super(JoinGame, self).to_json()
        j = j.replace('\"preferred_team\"', '\"preferredTeam\"')
        return j



#       Player actions


class Move(Message):
    """ Sent by player to gm to move in a direction """

    def __init__(self, id: uuid.uuid4, direction: str):
        super().__init__()
        self.action = 'move'
        self.dir = direction
        self.id = id
    
    def to_json(self):
        j = super(Move, self).to_json()
        j = j.replace('\"dir\"', '\"direction\"')
        return j


class PickUp(Message):
    """ Sent by player to gm to pick up a piece """

    def __init__(self, id: uuid.uuid4):
        super().__init__()
        self.action = 'pickup'
        self.id = id


class TestPiece(Message):
    """ Sent by player to gm to test whether a piece is a sham """

    def __init__(self, id: uuid.uuid4):
        super().__init__()
        self.action = 'test'
        self.id = id


class Discover(Message):
    """ Sent by player to gm to discover the contents of a section of the board """

    def __init__(self, location: dict, id: uuid.uuid4):
        super().__init__()
        self.action = 'state'
        self.location = location
        self.id = id


class PlacePiece(Message):
    """ Sent by player to gm  to place a piece on the board """

    def __init__(self, id: uuid.uuid4):
        super().__init__()
        self.action = 'place'
        self.id = id


class DestroyPiece(Message):
    """ Sent by player to gm to destroy the piece the player is holding """

    def __init__(self, id: uuid.uuid4):
        super().__init__()
        self.action = 'destroy'
        self.id = id

#       Knowledge Exchange

# There are slightly too complicated to explain in single line descriptions, please lookup the documentation,
#   I did my best to mimic what is written there


class AuthorizeKnowledgeExchange(Message):

    def __init__(self, userGuid: uuid.uuid4, receiverGuid: uuid.uuid4):
        super().__init__()
        self.action = 'exchange'
        self.userGuid = userGuid
        self.receiverGuid = receiverGuid


class RejectKnowledgeExchange(Message):

    def __init__(self, id: uuid.uuid4, rejectDuration: str):
        super().__init__()
        self.action = 'exchange'
        self.result = 'denied'
        self.id = id
        self.rejectDuration = rejectDuration


class AcceptKnowledgeExchange(Message):

    def __init__(self, id: uuid.uuid4):
        super().__init__()
        self.action = 'exchange'
        self.result = 'OK'
        self.id = id


class KnowledgeExchangeData(Message):

    def __init__(self, id: uuid.uuid4, to: uuid.uuid4, fields: dict):
        super().__init__()
        self.action = 'send'
        self.id = id
        self.to = to
        self.fields = fields

    def to_json(self):
        j = super(KnowledgeExchangeData, self).to_json()
        j = j.replace('\"to\"', '\"receiverGuid\"')
        return j



# ===== Errors =====

class MessageTranslationError(Message):
    """ Send this in case a received message could not be parsed from json """
    def __init__(self, error: str):
        super().__init__()
        self.action = 'error-translation'
        self.error = error

class UnkownGuidError(Message):
    """ Send this in case a received message has an unknown guid """
    def __init__(self, error: str):
        super().__init__()
        self.action = 'error-guid'
        self.error = error


# ===== GUI =====


class GuiMessage(Message):
    """ Sent by gm to server to be passed on to gui, contains current board """

    def __init__(self, board):
        super().__init__()
        self.action = 'gui'
        self.board = self.serialize_board(board)

    def serialize_board(self, board):
        rows = board.board_height
        cols = board.board_width
        cells = []
        for y in range(rows):
            row = []
            for x in range(cols):
                sq = board.get_square(x, y)
                content = str(sq)
                cell = content
                row.append(cell)
            cells.append(row)
        return cells