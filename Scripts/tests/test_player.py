import unittest
import uuid

import env

import common.player as player
import common.settings as settings
import board
import common.piece as piece

class PlayerTest(unittest.TestCase):

    # Initialize settings, board, player and add player to middle of board
    def setUp(self):
        self.settings = settings.Settings()
        self.board = board.Board(self.settings)
        self.pl = player.GmPlayer(id=uuid.uuid4(), team='blue')
        
        mid_x = int(self.settings.board_width / 2)
        mid_y = int(self.board.board_height / 2)
        
        self.sq = self.board.get_square(mid_x, mid_y)
        self.pl.x = self.sq.x
        self.pl.y = self.sq.y
        self.sq.player = self.pl 

    def test_moving(self):
        
        x = self.pl.x
        y = self.pl.y
        new_square = self.board.get_square(x+1,y)
        
        self.pl.move(self.sq, new_square)
        
        self.assertEqual((x + 1, y), (self.pl.x, self.pl.y))
        
    def test_pick_up(self):
        
        pc = piece.Piece(is_sham=False)
        self.sq.piece = pc
        
        self.pl.pick_up(self.sq)
        
        self.assertEqual(self.sq.piece, None)
        self.assertEqual(type(self.pl.piece), piece.Piece)

    def test_put_down(self):
        
        pc = piece.Piece(is_sham=False)
        self.pl.piece = pc
        
        self.pl.put_down_on(self.sq)

        self.assertEqual(self.pl.piece, None)
        self.assertEqual(type(self.sq.piece), piece.Piece)


if __name__ == '__main__':
    unittest.main(exit=False)