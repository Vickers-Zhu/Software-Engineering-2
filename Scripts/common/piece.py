import uuid

# Holds info on a piece

class Piece:
    def __init__(self, is_sham):
        self.id = uuid.uuid4()
        self.is_sham = is_sham

    def __str__(self):
        return "S" if self.is_sham else "P"