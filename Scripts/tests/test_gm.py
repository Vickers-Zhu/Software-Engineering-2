import unittest
import pubsub as ps
import uuid

import env

import common.settings as settings
import gm
import common.messages as m
import common.player as player
import common.piece as piece
import common.square as square

# Pretend server callback function
current_msg = None

def server(arg1):
    global current_msg
    current_msg = arg1


class GMTest(unittest.TestCase):

    def setUp(self):
        global current_msg
        self.settings = settings.Settings()
        self.gm = gm.GM(self.settings)
        self.current_msg = current_msg
        ps.pub.subscribe(server, 'server')

    def fill_game(self):
        # Fill game with players
        for _ in range(self.settings.player_count_per_team * 2):
            self.gm.join_game(m.JoinGame(
                id=uuid.uuid4(), preferred_team='blue', type='player'))

    def test_sending(self):
        msg = m.Message()

        self.gm.send(msg)

        self.assertEqual(m.Message, type(current_msg))

    def test_join_game(self):
        pl = player.GmPlayer(id=uuid.uuid4(), team='blue')
        msg = m.JoinGame(id=pl.id, preferred_team='red', type='player')

        self.gm.join_game(msg)

        self.assertIn(pl.id, self.gm.players)

    def test_deny_join_game(self):
        self.fill_game()
        msg = m.JoinGame(id=uuid.uuid4, preferred_team='red', type='player')

        self.gm.join_game(msg)

        res = current_msg.result
        self.assertEqual(res, 'denied')

    def test_teams_equal(self):
        self.fill_game()

        red = len(self.gm.red_team)
        blue = len(self.gm.blue_team)

        self.assertEqual(red, blue)

    def test_sending_game_data_on_start(self):
        self.fill_game()

        self.assertEqual(type(current_msg), m.GameMessage)

    def move_to_dir(self, dir, fr, to, step):
        self.setUp()

        # Add and move player to middle of board
        msg = m.JoinGame(id=uuid.uuid4(), preferred_team='red', type='player')
        self.gm.join_game(msg)

        pl = self.gm.red_team[0]

        mid_x = int(self.gm.board.board_width/2)
        mid_y = int(self.gm.board.board_height/2)

        sq = self.gm.board.get_square(pl.x, pl.y)
        mid_sq = self.gm.board.get_square(mid_x, mid_y)

        pl.move(sq, mid_sq)

        # Moving in dir to the end
        for _ in range(fr, to, step):
            msg = m.Move(id=pl.id, direction=dir)
            self.gm.move_player(msg)

            res = current_msg.result
            self.assertEqual(res, 'OK')

        # Now should not be able to go more in the given direction
        msg = m.Move(id=pl.id, direction=dir)
        self.gm.move_player(msg)

        res = current_msg.result
        self.assertNotEqual(res, dir)

    def test_moving_player(self):
        max_y = self.gm.board.board_height - 1
        max_x = self.gm.board.board_width - 1
        min_y = 0
        min_x = 0
        mid_x = int(self.gm.board.board_width/2)
        mid_y = int(self.gm.board.board_height/2)

        self.move_to_dir('E', mid_x, max_x,  1)
        self.move_to_dir('S', mid_y, max_y - 1,  1)
        self.move_to_dir('W', mid_x, min_x, -1)
        self.move_to_dir('N', mid_y, min_y, -1)

    def test_move_over_player(self):
        self.setUp()

        # Add and move player to middle of board
        msg = m.JoinGame(id=uuid.uuid4(), preferred_team='red', type='player')
        self.gm.join_game(msg)

        pl1 = self.gm.red_team[0]

        mid_x = int(self.gm.board.board_width/2)
        mid_y = int(self.gm.board.board_height / 2)

        sq = self.gm.board.get_square(pl1.x, pl1.y)
        mid_sq = self.gm.board.get_square(mid_x, mid_y)

        pl1.move(sq, mid_sq)

        # Add and move player to middle of board
        msg = m.JoinGame(id=uuid.uuid4(), preferred_team='blue', type='player')
        self.gm.join_game(msg)

        pl2 = self.gm.blue_team[0]

        pl2_x = int(self.gm.board.board_height/2)
        pl2_y = int(self.gm.board.board_width / 2) + 1

        sq = self.gm.board.get_square(pl2.x, pl2.y)
        next_sq = self.gm.board.get_square(pl2_x, pl2_y)

        pl2.move(sq, next_sq)

        msg = m.Move(id=pl1.id, direction='E')
        self.gm.move_player(msg)

        res = current_msg.result
        self.assertEqual(res, 'denied')

    def test_discover(self):
        self.fill_game()

        pl_id = self.gm.red_team[0].id
        msg = m.Discover(id=pl_id, location={"x": 0, "y": 0})

        self.gm.discover(msg)

        self.assertEqual(len(current_msg.fields), 4)

        fields = list(current_msg.fields[0].keys())
        true_fields = ['x', 'y', 'value']

        types = [type(x) for x in current_msg.fields[0].values()]
        true_types = [int, int, dict]

        self.assertEqual(type(current_msg), m.DiscoverData)
        self.assertEqual(fields, true_fields)
        self.assertEqual(types, true_types)

    def test_place_piece(self):
        self.fill_game()
        pl = self.gm.red_team[0]

        # Put down without having a piece
        msg = m.PlacePiece(id=pl.id)
        self.gm.place_piece(msg)

        self.assertEqual(current_msg.result, 'denied')

        # Can't put down due to piece
        sq = self.gm.board.get_square(pl.x, pl.y)
        sq.piece = piece.Piece(is_sham=False)

        msg = m.PlacePiece(id=pl.id)
        self.gm.place_piece(msg)

        self.assertEqual(current_msg.result, 'denied')

        # Can put down, meaningless
        sq.piece = None
        pl.piece = piece.Piece(is_sham=False)

        msg = m.PlacePiece(id=pl.id)
        self.gm.place_piece(msg)

        self.assertEqual(current_msg.result, 'OK')
        self.assertEqual(current_msg.consequence, 'meaningless')
        self.assertNotEqual(sq.piece, None)

        # Can't due to discovered field
        sq.piece = None
        sq.type = square.SquareType.RedGoalField
        sq.discovered = True
        pl.piece = piece.Piece(is_sham=False)

        msg = m.PlacePiece(id=pl.id)
        self.gm.place_piece(msg)

        self.assertEqual(current_msg.result, 'denied')
        self.assertEqual(current_msg.consequence, 'null')

        # Placed piece correctly
        sq.piece = None
        sq.type = square.SquareType.RedGoalField
        sq.discovered = False
        pl.piece = piece.Piece(is_sham=False)

        msg = m.PlacePiece(id=pl.id)
        self.gm.place_piece(msg)

        self.assertEqual(current_msg.result, 'OK')
        self.assertEqual(current_msg.consequence, 'correct')

        # Piece should disappear after being correclty placed
        self.assertEqual(sq.piece, None)
        self.assertEqual(sq.discovered, True)

    def test_destroy(self):
        self.fill_game()

        pl = self.gm.red_team[0]

        # Not allowed
        pl.piece = None
        msg = m.DestroyPiece(id=pl.id)
        self.gm.destroy_piece(msg)

        self.assertEqual(current_msg.result, 'denied')

        # Allowed
        pl.piece = piece.Piece(is_sham=False)
        msg = m.DestroyPiece(id=pl.id)
        self.gm.destroy_piece(msg)

        self.assertEqual(current_msg.result, 'OK')
        self.assertEqual(pl.piece, None)


if __name__ == '__main__':
    unittest.main(exit=False)
