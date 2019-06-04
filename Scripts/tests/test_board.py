import unittest

import env

import board as board
import common.settings as settings
import common.square as square
import common.player as player

class BoardTest(unittest.TestCase):

    def setUp(self):
        self.settings = settings.Settings()
        self.board = board.Board(self.settings)
        self.board.random_select_fields()
        self.board.random_select_pieces()

    def test_board_proportions(self):
        board_height = self.settings.goal_area_length*2 + self.settings.task_area_length
        self.assertEqual(len(self.board.content),
                         board_height * self.settings.board_width)

    def test_goal_fields(self):
        goal_field_count = len([1 for sq in self.board.content if sq.type ==
                                square.SquareType.BlueGoalField or sq.type == square.SquareType.RedGoalField])

        self.assertEqual(goal_field_count,
                         self.settings.goal_definition * 2)

    def test_pieces(self):
        piece_count = len(
            [1 for sq in self.board.content if sq.piece is not None])
        self.assertEqual(piece_count,
                         self.settings.initial_piece_count)


if __name__ == '__main__':
    unittest.main(exit=False)
