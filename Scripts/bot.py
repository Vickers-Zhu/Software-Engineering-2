# import asyncio
# import multipledispatch as md
import threading
import random as rand
import time
import uuid
import datetime
import argparse
import signal
import sys

from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver

from threading import Thread
from enum import Enum

import common.settings as s
import common.messages as m
import common.delay as d
import common.logger as l

import board as b
import gm as g
import bot_server as bs


class Bot():

	def __init__(self, id:uuid.uuid4, teamPref:str, callback):
		self.id = id
		self.teamPref = teamPref
		self.sendMsg = callback

	def interpret_message(self, msg: m.Message):
		t = type(msg)
		if t is m.ConfirmJoiningGame:
			self.init_callback(msg)
		elif t is m.DestroyPieceData:
			self.destroyPieceCallback(msg)
		elif t is m.DiscoverData:
			self.discoverDataCallback(msg)
		elif t is m.GameMessage:
			self.game_start_callback(msg)
		elif t is m.MoveData:
			self.moveCallback(msg)
		elif t is m.PickUpData:
			self.pickUpCallback(msg)
		elif t is m.PlaceData:
			self.placePieceCallback(msg)
		elif t is m.TestData:
			self.testPieceCallback(msg)
		elif t is m.KnowledgeExchangeData:
			self.knowledgeExchangeCallback(msg)
		else:
			print(f"unrecognized message received: {msg}")

	def init_callback(self,msg):
		print(f'bot init ack: {self.id}')
		self.type = msg.type

	def game_start_callback(self,msg):
		print(f'game started ack: {self.id}')
		self.team = msg.team
		self.role = msg.role
		self.team_size = msg.team_size
		self.location = msg.location
		self.board = msg.board

		self.boardWrapper = BotHelper(BotBoard(msg.board["width"], msg.board["tasksHeight"], msg.board["goalsHeight"], msg.team), msg.location["x"], msg.location["y"])

		print(f'im starting to play : {self.id} : {self.team} : {self.location} : {self.board}')

		self.hasPiece = False
		self.lastMessage = None
		self.nextMove = self.move
		self.pieceAge = 0
		self.lastDistance = None
		self.currDistance = None

		self.nextMove()

	def move(self):
		if not self.hasPiece and self.lastDistance is not None and self.currDistance is not None and (self.lastDistance - 1) == self.currDistance and self.boardWrapper.checkValidityOfMove(self.lastMessage.dir):
			# last move was in the right direction. keep moving like that!
			d = self.boardWrapper.chancedMoveSkewer(self.lastMessage.dir)
		else:
			# delegate the choice to wrapper
			d = self.boardWrapper.getReturnMove() if self.hasPiece else self.boardWrapper.getReconMove()
		if d is None:
			# getReturnMove returns None if the target location is already under the bot (ie. it has arrived).
			if self.hasPiece:
				self.placePiece()
				return
			else:
				# Something went wrong. Make a random move.
				d = rand.choice(['N','S','E','W'])

		print(f'moving towards: {d}')
		ms = m.Move(id = self.id, direction = d)
		self.sendMsg(ms)
		# log last move message to help make next move choice
		self.lastMessage = ms

	def knowledgeExchangeCallback(self, msg):
		# for testing our gm's capability only
		print('knowledge exchange info received. How useless!')

	def takeNextMove(self):
		if self.nextMove is not None:
			self.nextMove()
		else:
			raise Exception("Failed to take action")

	# in each decision tree that the nextMove does not end assigned, call to takeNextMove raises exception. Since all cases are covered, the only case when that happens is if the gm is faulty.
	def moveCallback(self,msg):
		self.nextMove = None
		if msg.result == 'OK':
			self.updateLoc(self.lastMessage.dir)
			# reset failed move counter
			self.boardWrapper.headless_chicken_move_chance = 0
			if self.hasPiece:
				if msg.manhattanDistance is None and self.boardWrapper.canPlacePiece():
					# drop piece if holding it and over the goal area that is not flagged as blocking (not previously tested by bot)
					self.nextMove = self.placePiece
				elif self.pieceAge < 2 * self.boardWrapper.board.height:
					self.nextMove = self.move
					self.pieceAge += 1
				else:
					# something went wrong, despite numerous return moves the goal area has not been reached - so drop the piece.
					self.nextMove = self.placePiece
			elif msg.manhattanDistance == 0:
				# pick up piece since distance is 0
				self.nextMove = self.pickUp
			else:
				# continue looking for piece
				self.nextMove = self.move
			# stash last & curr manh. distance for better decisionmaking in self.move()
			self.lastDistance  = self.currDistance
			self.currDistance = msg.manhattanDistance
		elif msg.result == 'denied':
			# move has failed - a colision with a bot (since bots know not to run into walls). increase chance to make a random move and make a move action.
			self.boardWrapper.headless_chicken_move_chance += 0.2
			self.nextMove = self.move
			print(f'failed to move after msg: {self.lastMessage}')

		self.takeNextMove()

	def pickUp(self):
		print('picking up')
		ms = m.PickUp(id=self.id)
		self.sendMsg(ms)

	def pickUpCallback(self,msg):
		self.nextMove = None
		if msg.result == 'OK':
			self.pieceAge = 0
			self.hasPiece = True
			# always test piece right after picking up
			self.nextMove = self.testPiece
		elif msg.result == 'denied':
			# only case when bots pick up a piece is when dist is 0 => the gm is broken.
			print('I failed to pick up a piece that I swear was there (distance was 0)')
			self.nextMove = self.move

		self.takeNextMove()

	def placePiece(self):
		print('placing piece')
		ms = m.PlacePiece(id=self.id)
		self.sendMsg(ms)

	def placePieceCallback(self, msg):
		self.nextMove = None
		if msg.result == 'denied':
			self.nextMove = self.move
		elif msg.result == 'OK':
			self.hasPiece = False
			self.pieceAge = 0
			if msg.consequence == 'meaningless':
				# piece was dropped in goal area, but not on goal tile. pick it up at once!
				self.nextMove = self.pickUp
			elif msg.consequence == 'correct':
				# goal scored, search for next piece
				self.nextMove = self.move
		# failedPlace = nothing should be placed on this tile because either it is not a goal tile, or it is now a scored goal tile
		self.boardWrapper.flagFailedPlace()
		self.takeNextMove()

	def testPiece(self):
		print('testing')
		ms = m.TestPiece(id = self.id)
		self.sendMsg(ms)

	def testPieceCallback(self,msg):
		self.nextMove = None
		print('testPieceCallback')
		if msg.result == 'denied' or msg.test is None or msg.test == 'null':
			# something went wrong in logic (because pieces are only tested as result of holding them). try to recover.
			print('I thought I had a piece, but I didnt.')
			self.hasPiece = False
			self.nextMove = self.move
		elif msg.result == 'OK':
			if msg.test == 'true' or msg.test == True:
				self.nextMove = self.destroyPiece
			elif msg.test == "false" or msg.test == False:
				self.nextMove = self.move
		
		self.takeNextMove()

	def destroyPiece(self):
		print('destroying piece')
		ms = m.DestroyPiece(id = self.id)
		self.sendMsg(ms)

	def destroyPieceCallback(self,msg):
		self.nextMove = None

		if msg.result == 'denied':
			# something went wrong with gm. try to recover.
			print('I tried to destroy a piece I didnt have')
			self.hasPiece = False
			self.nextMove = self.move
		elif msg.result == 'OK':
			self.nextMove = self.move
			self.hasPiece = False

		self.takeNextMove()

	def discoverDataCallback(self,msg):
		pass

	# utilities

	def updateLoc(self, dir:str):
		self.boardWrapper.updatePosition(dir)


class Team(Enum):
	RED = "red"
	BLUE = "blue"


class BotHelper:

	"""Intermediate between the bot and board: updates the board and has a selection of decisions based on input directive, but does not make the initial call it"""
	def __init__(self, board:"BotBoard", x, y):
		self.headless_chicken_move_chance = 0
		self.board = board
		self.x = x
		self.y = y
		self.dirToCoord = {
			"N": (0, 1),
			"S": (0, -1),
			"E": (1, 0),
			"W": (-1, 0)
		}

	def canPlacePiece(self):
		return self.board.getCellIfExists((self.x, self.y)).tileType == TileType.GOAL_FRIENDLY_UNKNOWN

	def flagFailedPlace(self):
		"""Set the tile you are currently on as one a piece cannot be placed upon"""
		self.board.setCell((self.x, self.y), TileType.GOAL_FRIENDLY_BLOCKING)

	def chancedMoveSkewer(self, move:"Moves"):
		"""Return move as per logic unless the random roll is lower than random move chance - incremented on failed moves by bot, zeroed on successfull move"""
		# each time you move there is a chance to move in a random direction, starting at 0, reseting to 0 on each successful move, and incrementing each time a move is failed - to avoid deadlocks
		print(f'current rm chance: {self.headless_chicken_move_chance}')
		if self.headless_chicken_move_chance > 0:
			return move if (rand.random() > self.headless_chicken_move_chance) else rand.choice(self.getValidMovesMasked()[0])
		else:
			return move

	def moveTowards(self, to:"[x,y]"):
		"""Returns move that needs to be taken to get to tile 'to', or None if already on it."""
		x1, y1 = self.x, self.y
		x2, y2 = to

		if x1 == x2 and y1 == y2:
			return None

		# compute the next move towards x, y
		dx = x2 - x1
		dy = y2 - y1

		# move should have some randomness, to avoid deadlocks; regardless it will always move closer to it after this
		if rand.random() < abs(dx) / (abs(dx) + abs(dy)):
			return "E" if dx > 0 else "W"
		else:
			return "N" if dy > 0 else "S"

	def updatePosition(self, move:"Moves"):
		"""Given NSEW move, update current location on board"""
		postmove = [self.dirToCoord[move][0] + self.x, self.dirToCoord[move][1] + self.y]

		if self.board.getCellIfExists(postmove) is None:
			# this never happens. but flag if it does, because it means there is a flaw in code.
			print("Bot tried to update position of self into a wall!")
		self.x = postmove[0]
		self.y = postmove[1]
		print(f'I: {self.board.team}\n Am at: {self.x}/{self.y}')

	def getValidMovesMasked(self, mask:"list of TileType's"=[]):
		"""return valid moves that will not put you into a tile of type from mask with flag false; if no such move is possible, return valid moves that will not crash you into a wall with flag set to true"""
		base = []
		priority = []
		right = self.board.getCellIfExists((self.x + 1, self.y))
		left = self.board.getCellIfExists((self.x - 1, self.y))
		up = self.board.getCellIfExists((self.x, self.y + 1))
		down = self.board.getCellIfExists((self.x, self.y - 1))

		if right is not None and right.tileType != TileType.GOAL_ENEMY:
			base.append("E")
			if right.tileType not in mask:
				priority.append("E")
		if left is not None and left.tileType != TileType.GOAL_ENEMY:
			base.append("W")
			if left not in mask:
				priority.append("W")
		if up is not None and up.tileType != TileType.GOAL_ENEMY:
			base.append("N")
			if up.tileType not in mask:
				priority.append("N")
		if down is not None and down.tileType != TileType.GOAL_ENEMY:
			base.append("S")
			if down.tileType not in mask:
				priority.append("S")
		return (priority, False) if len(priority) > 0 else (base, True)

	def getReconMove(self):
		"""Get a move whose result maximizes chance to find a new piece, unless the bot knows better (bot knows distances to pieces and boardWrapper does not)"""
		return self.chancedMoveSkewer(rand.choice(self.getValidMovesMasked()[0]))

	def checkValidityOfMove(self, move):
		"""Check if a move is possible (essentially, if it doesnt move you into a walll)"""
		return move in self.getValidMovesMasked([])[0]

	def getReturnMove(self):
		"""Return a move that will move you closer to the closest unknown friendly goal area tile"""
		ret = self.board.getClosestCellOfType((self.x, self.y), TileType.GOAL_FRIENDLY_UNKNOWN)
		
		if ret is None:
			# this should never happen. but if the gm is broken and it does, revert to old logic.
			print("No unscored friendly goals exist? How? Something went wrong with gm.")
		else:
			x, y = ret
			move = self.moveTowards((x,y))
			if move is None:
				#already on an unknown friendly goal tile
				return None
			else:
				return self.chancedMoveSkewer(move)

		# revert back to the old return-move way because the new failed. Only happens when the gm is broken.
		# move towards your goal area if outside of it
		if self.board.getCellIfExists((self.x,self.y)).tileType in [TileType.TASK_TILE]:
			return self.chancedMoveSkewer("N" if self.board.team == "red" else "S")

		# if within the goal, move to another non-filled non-task field if possible
		moves, flag = self.getValidMovesMasked([TileType.GOAL_FRIENDLY_BLOCKING, TileType.TASK_TILE])
		# if not possible, at least try not moving into task tiles
		if flag:
			moves, flag = self.getValidMovesMasked([TileType.TASK_TILE])
		return self.chancedMoveSkewer(rand.choice(moves))

class BotBoard:
	class Cell:
		def __init__(self, x, y, tileType:"TileType"):
			# even though updatedAt is never used (because we couldnt find a use for it), it was required, so here it is.
			self.updatedAt = datetime.datetime.now()
			self.x = x
			self.y = y
			self.tileType = tileType
			self.odds = 0

		def __repr__(self):
			return self.__str__()

		def __str__(self):
			return f"{self.x}/{self.y}, tile: {self.tileType}, lastUpdated: {self.updatedAt}"

		def getDistTo(self, arr:"[x,y]"):
			x, y = arr
			return (abs(self.x - x) + abs(self.y - y))

	def __init__(self, width:int, tasksHeight:int, goalsHeight:int, team:"Team"):
		self.width = width
		self.height = tasksHeight + 2 * goalsHeight
		self.tasksHeight = tasksHeight
		self.goalsHeight = goalsHeight
		self.team = team
		self.cells = []

		# create board with (x=0,y=0) in bottom-left
		for i in range(0, width):
			self.cells.append([])
			for j in range(0, goalsHeight):
				typ = TileType.GOAL_FRIENDLY_UNKNOWN if self.team == "blue" else TileType.GOAL_ENEMY
				self.cells[i].append(self.Cell(x = i, y = j, tileType = typ))
			for j in range(goalsHeight, goalsHeight + tasksHeight):
				self.cells[i].append(self.Cell(x = i, y = j, tileType = TileType.TASK_TILE))
			for j in range(goalsHeight + tasksHeight, self.height):
				typ = TileType.GOAL_FRIENDLY_UNKNOWN if self.team == "red" else TileType.GOAL_ENEMY
				self.cells[i].append(self.Cell(x = i, y = j, tileType = typ))

	def getClosestCellOfType(self, arr:"(x,y)", tt:"TileType"):
		"""Returns the closest cell of given type, or None if no such exists"""
		x, y = arr
		eligibles = [y for x in self.cells for y in x if y.tileType == tt]

		if len(eligibles) < 1:
			return None
		else:
			eligibles.sort(key = lambda c : c.getDistTo((x,y)), reverse = False)
			ret = eligibles[0]
			return (ret.x, ret.y)

	def setCell(self, arr:"(x,y)", tileType:"TileType"):
		x,y = arr
		self.cells[x][y] = self.Cell(x,y,tileType)

	def getCellIfExists(self, arr:"(x,y)"):
		(x,y) = arr
		if x >= 0 and x < self.width and y >= 0 and y < self.height:
			return self.cells[x][y]
		else:
			return None

class TileType(Enum):
	# while there are more states that are interesting to gm, the bot doesnt have to care about more than these 3 - so it doesnt
	GOAL_ENEMY = 1
	TASK_TILE = 2
	GOAL_FRIENDLY_UNKNOWN = 5
	GOAL_FRIENDLY_BLOCKING = 6
	# while these 3 were eventually never used, they are present in unit tests, so they stay.
	GOAL_FRIENDLY_EMPTY = 0
	GOAL_FRIENDLY_SCORED = 3
	GOAL_FRIENDLY_SCORING = 4