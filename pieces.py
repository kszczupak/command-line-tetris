"""
Collection of base pieces used in Tetris game.
"""
from enum import Enum
import random


def get_positions_from_rotation(rotation_block, orientation_enum):
    positions = list()

    for y_offset, x_offset in orientation_enum.value:
        new_position = (
            rotation_block[0] + y_offset,
            rotation_block[1] + x_offset
        )
        positions.append(new_position)

    return positions


class AbstractPiece:
    def __init__(self, initial_rotation_block_position=(1, 5)):
        # Only position of rotation block will be constantly maintained - positions of other blocks can be
        # calculated using rotation block and offsets relative to this block (encoded in orientation enum in this case)
        self.rotation_block = initial_rotation_block_position
        self.orientation = None

        self.requested_rotation_block = None
        self.requested_orientation = None

        # Only for drawing - needs to be maintained in order to erase previous positions of the piece from window
        self.previous_rotation_block = None
        self.previous_orientation = None

    def __hash__(self):
        return hash(self.__class__.__name__)

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return True

        return False

    def accept_move(self):
        self.previous_rotation_block = self.rotation_block
        if self.requested_rotation_block:
            self.rotation_block = self.requested_rotation_block

        self.previous_orientation = self.orientation
        if self.requested_orientation:
            self.orientation = self.requested_orientation

    def reject_move(self):
        self.requested_rotation_block = None
        self.requested_orientation = None

    @property
    def previous_positions(self):
        if self.previous_rotation_block:
            return get_positions_from_rotation(self.previous_rotation_block, self.previous_orientation)

        return None

    @property
    def current_positions(self):
        return get_positions_from_rotation(self.rotation_block, self.orientation)

    def move_right(self):
        self.requested_rotation_block = (
            self.rotation_block[0],
            self.rotation_block[1] + 1
        )

        return get_positions_from_rotation(self.requested_rotation_block, self.orientation)

    def move_left(self):
        self.requested_rotation_block = (
            self.rotation_block[0],
            self.rotation_block[1] - 1
        )

        return get_positions_from_rotation(self.requested_rotation_block, self.orientation)

    def advance(self):
        self.requested_rotation_block = (
            self.rotation_block[0] + 1,
            self.rotation_block[1]
        )

        return get_positions_from_rotation(self.requested_rotation_block, self.orientation)

    def rotate_clockwise(self):
        raise NotImplementedError()

    def rotate_anti_clockwise(self):
        raise NotImplementedError()


class Square(AbstractPiece):
    """
    0 1
    2 3

    Blocks numeration, rotation block = 1
    """
    class _Orientation(Enum):
        CONSTANT = ((0, -1), (0, 0), (1, -1), (1, 0))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = Square._Orientation.CONSTANT

    def rotate_clockwise(self):
        # Square doesn't rotate so return current positions
        return get_positions_from_rotation(self.rotation_block, self.orientation)

    def rotate_anti_clockwise(self):
        return self.rotate_clockwise()


class LongBar(AbstractPiece):
    """
    0 1 2 3

    Blocks numeration with orientation == _VERTICAL, rotation block = 2
    """
    class _Orientation(Enum):
        VERTICAL = ((0, -2), (0, -1), (0, 0), (0, 1))
        HORIZONTAL = ((2, 0), (1, 0), (0, 0), (-1, 0))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = LongBar._Orientation.VERTICAL

    def rotate_clockwise(self):
        if self.orientation == LongBar._Orientation.VERTICAL:
            self.requested_orientation = LongBar._Orientation.HORIZONTAL
        else:
            self.requested_orientation = LongBar._Orientation.VERTICAL

        return get_positions_from_rotation(self.rotation_block, self.requested_orientation)

    def rotate_anti_clockwise(self):
        return self.rotate_clockwise()


class L_Piece(AbstractPiece):
    """
    1 2 3
    0

    Blocks numeration when facing down (_Orientation.DOWN, rotation block = 2)
    """

    class _Orientation(Enum):
        # abstract direction -> y, x offsets relative to rotation block
        DOWN = ((1, -1), (0, -1), (0, 0), (0, 1))
        LEFT = ((-1, -1), (-1, 0), (0, 0), (1, 0))
        UP = ((-1, 1), (0, 1), (0, 0), (0, -1))
        RIGHT = ((1, 1), (1, 0), (0, 0), (-1, 0))

    _clockwise_rotation = {
        _Orientation.DOWN: _Orientation.LEFT,
        _Orientation.LEFT: _Orientation.UP,
        _Orientation.UP: _Orientation.RIGHT,
        _Orientation.RIGHT: _Orientation.DOWN,
    }

    _anti_clockwise_rotation = {v: k for k, v in _clockwise_rotation.items()}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = L_Piece._Orientation.DOWN

    def rotate_clockwise(self):
        self.requested_orientation = L_Piece._clockwise_rotation[self.orientation]

        return get_positions_from_rotation(self.rotation_block, self.requested_orientation)

    def rotate_anti_clockwise(self):
        self.requested_orientation = L_Piece._anti_clockwise_rotation[self.orientation]

        return get_positions_from_rotation(self.rotation_block, self.requested_orientation)


class J_Piece(AbstractPiece):
    """
    0 1 2
        3

    Blocks numeration when facing down (_Orientation.DOWN, rotation block = 1)
    """

    class _Orientation(Enum):
        # abstract direction -> y, x offsets relative to rotation block
        DOWN = ((0, -1), (0, 0), (0, 1), (1, 1))
        LEFT = ((-1, 0), (0, 0), (1, 0), (1, -1))
        UP = ((0, 1), (0, 0), (0, -1), (-1, -1))
        RIGHT = ((1, 0), (0, 0), (-1, 0), (-1, 1))

    _clockwise_rotation = {
        _Orientation.DOWN: _Orientation.LEFT,
        _Orientation.LEFT: _Orientation.UP,
        _Orientation.UP: _Orientation.RIGHT,
        _Orientation.RIGHT: _Orientation.DOWN,
    }

    _anti_clockwise_rotation = {v: k for k, v in _clockwise_rotation.items()}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = J_Piece._Orientation.DOWN

    def rotate_clockwise(self):
        self.requested_orientation = J_Piece._clockwise_rotation[self.orientation]

        return get_positions_from_rotation(self.rotation_block, self.requested_orientation)

    def rotate_anti_clockwise(self):
        self.requested_orientation = J_Piece._anti_clockwise_rotation[self.orientation]

        return get_positions_from_rotation(self.rotation_block, self.requested_orientation)


class Z_Piece(AbstractPiece):
    """
    0 1
      2 3

    Blocks numeration when facing left (_Orientation.LEFT, rotation block = 1)
    """

    class _Orientation(Enum):
        # abstract direction -> y, x offsets relative to rotation block
        LEFT = ((0, -1), (0, 0), (1, 0), (1, 1))
        UP = ((-1, 0), (0, 0), (0, -1), (1, -1))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = Z_Piece._Orientation.LEFT

    def rotate_clockwise(self):
        if self.orientation == Z_Piece._Orientation.UP:
            self.requested_orientation = Z_Piece._Orientation.LEFT
        else:
            self.requested_orientation = Z_Piece._Orientation.UP

        return get_positions_from_rotation(self.rotation_block, self.requested_orientation)

    def rotate_anti_clockwise(self):
        return self.rotate_clockwise()


class S_Piece(AbstractPiece):
    """
      0 1
    2 3

    Blocks numeration when facing right (_Orientation.RIGHT, rotation block = 0)
    """

    class _Orientation(Enum):
        # abstract direction -> y, x offsets relative to rotation block
        RIGHT = ((0, 0), (0, 1), (1, -1), (1, 0))
        UP = ((0, 0), (-1, 0), (0, 1), (1, 1))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = S_Piece._Orientation.RIGHT

    def rotate_clockwise(self):
        if self.orientation == S_Piece._Orientation.UP:
            self.requested_orientation = S_Piece._Orientation.RIGHT
        else:
            self.requested_orientation = S_Piece._Orientation.UP

        return get_positions_from_rotation(self.rotation_block, self.requested_orientation)

    def rotate_anti_clockwise(self):
        return self.rotate_clockwise()


class T_Piece(AbstractPiece):
    """
    0 1 2
      3

    Blocks numeration when facing down (_Orientation.DOWN, rotation block = 1)
    """

    class _Orientation(Enum):
        # abstract direction -> y, x offsets relative to rotation block
        DOWN = ((0, -1), (0, 0), (0, 1), (1, 0))
        LEFT = ((-1, 0), (0, 0), (1, 0), (0, -1))
        UP = ((0, 1), (0, 0), (0, -1), (-1, 0))
        RIGHT = ((1, 0), (0, 0), (-1, 0), (0, 1))

    _clockwise_rotation = {
        _Orientation.DOWN: _Orientation.LEFT,
        _Orientation.LEFT: _Orientation.UP,
        _Orientation.UP: _Orientation.RIGHT,
        _Orientation.RIGHT: _Orientation.DOWN,
    }

    _anti_clockwise_rotation = {v: k for k, v in _clockwise_rotation.items()}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = T_Piece._Orientation.DOWN

    def rotate_clockwise(self):
        self.requested_orientation = T_Piece._clockwise_rotation[self.orientation]

        return get_positions_from_rotation(self.rotation_block, self.requested_orientation)

    def rotate_anti_clockwise(self):
        self.requested_orientation = T_Piece._anti_clockwise_rotation[self.orientation]

        return get_positions_from_rotation(self.rotation_block, self.requested_orientation)


all_pieces = (Square, LongBar, L_Piece, J_Piece, Z_Piece, S_Piece, T_Piece)


def get_random_piece():
    return random.choice(all_pieces)
