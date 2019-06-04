import random
import uuid

import common.settings as s
import common.square as sqr
import common.piece as pc

class Board:

    def __init__(self, settings: s.Settings):
        self.id = uuid.uuid4()
        self.board_width = settings.board_width
        self.goal_area_height = settings.goal_area_length
        self.piece_sham_chance = settings.piece_sham_chance
        self.goal_definition = settings.goal_definition
        self.piece_count = settings.initial_piece_count

        self.board_height = settings.goal_area_length * 2 + settings.task_area_length
        self.task_area_height = settings.task_area_length

        self.goal_area_blue = [sqr.Square(x, y, sqr.SquareType.BlueGoalArea) for y in range(self.goal_area_height)
                                for x in range(self.board_width)]

        self.task_area = [sqr.Square(x, y, sqr.SquareType.TaskArea) 
                          for y in range(self.goal_area_height, self.board_height - self.goal_area_height)
                          for x in range(self.board_width)]

        self.goal_area_red = [sqr.Square(x, y, sqr.SquareType.RedGoalArea) 
             for y in range(self.board_height - self.goal_area_height, self.board_height)
             for x in range(self.board_width)]

        # For convenience
        self.content = self.goal_area_blue + self.task_area + self.goal_area_red 

    # Returns square at x,y position, None if not found
    def get_square(self, x, y):
        if x >= self.board_width or x < 0:
            return None
        if y >= self.board_height or y < 0:
            return None
        return self.content[y * self.board_width + x]

    # Randomly selects goal areas to be fields on red side and mirrors them on blue side
    def random_select_fields(self):
        rem = self.goal_definition

        while True:
            sq = random.choice(self.goal_area_blue)
            if sq.type == sqr.SquareType.BlueGoalArea:
                sq.type = sqr.SquareType.BlueGoalField
                self.get_square(sq.x,self.board_height - sq.y - 1).type = sqr.SquareType.RedGoalField
                rem = rem - 1
            if rem == 0:
                break

    # Randomly adds new pieces to the board
    def random_select_pieces(self):
        rem = self.piece_count

        while True:
            sq = random.choice(self.task_area)
            if sq.piece is None:
                sq.piece = pc.Piece(
                    is_sham=True if random.random() < self.piece_sham_chance else False)
                rem = rem - 1
                if rem == 0:
                    break

    # Picks random square in task area and adds a new piece, will destroy old piece if present
    def new_piece(self):
        sq = random.choice(self.task_area)
        sq.piece = pc.Piece(is_sham=True if random.random()
                            < self.piece_sham_chance else False)

    def __str__(self):
        b = ""
        for x in range(self.board_height):
            s = ""
            for y in range(self.board_width):
                s += f'|{self.get_square(x, y)}| '
            b = b + s + "\n"
        return b
