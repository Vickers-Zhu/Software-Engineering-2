import env
import uuid
import time

import bot as bt
import common.messages as m
import unittest
import board as b
import common.settings as s

class BotTest(unittest.TestCase):
	def setUp(self):
		return

	def testMoveTowards(self):
		b = bt.BotHelper(bt.BotBoard(3, 1, 1, "red"), 1, 1)
		self.assertIsNotNone(b)

		self.assertIn(b.moveTowards((2, 2)), ["N", "E"])
		self.assertEqual(b.moveTowards((1, 2)), "N")
		self.assertIn(b.moveTowards((0, -5)), ["S", "W"])
		self.assertIsNone(b.moveTowards((1, 1)))

	def testSuspectCellSeeking(self):
		b = bt.BotHelper(bt.BotBoard(3, 1, 1, "blue"), 0, 0)
		self.assertIsNotNone(b)

		b.board.cells[0][1].tileType = bt.TileType.GOAL_FRIENDLY_BLOCKING
		self.assertEqual(len(b.board.getSuspectCellsInDist((1, 1), 1)), 3)
		self.assertEqual(len(b.board.getSuspectCellsInDist((1, 1), 0)), 1)
		self.assertEqual(len(b.board.getSuspectCellsInDist((1, 1), 2)), 4)
		self.assertEqual(len(b.board.getSuspectCellsInDist((1, 1), 3)), 0)

	def testCellSeeking(self):
		b = bt.BotHelper(bt.BotBoard(5, 3, 1, "blue"), 0, 0)
		self.assertIsNotNone(b)

		self.assertEqual(b.board.getClosestCellOfType((0, 1), bt.TileType.TASK_TILE), (0, 1))
		self.assertEqual(b.board.getClosestCellOfType((1, 0), bt.TileType.GOAL_ENEMY), (1, 4))

		b.board.cells[3][4].tileType = bt.TileType.GOAL_FRIENDLY_SCORED
		b.board.cells[4][2].tileType = bt.TileType.GOAL_FRIENDLY_SCORED
		self.assertEqual(b.board.getClosestCellOfType((3, 0), bt.TileType.GOAL_FRIENDLY_SCORED), (4, 2))

	def testBoardMoves(self):
		b = bt.BotHelper(bt.BotBoard(3, 1, 1,"red"), 0, 1)
		self.assertIsNotNone(b)

		self.assertEqual(b.getValidMovesMasked(), (["E", "N"], False))

		self.assertEqual(b.getValidMovesMasked([bt.TileType.GOAL_FRIENDLY_UNKNOWN]), (["E"], False))

		self.assertIn(b.getReconMove(), ["E", "N"])
		self.assertEqual(b.getReturnMove(), "N")

if __name__ == '__main__':
    unittest.main(exit=False)