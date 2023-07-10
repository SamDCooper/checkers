import dataclasses
import enum


class InvalidBoardPosition(Exception):
    pass


class IllegalMove(Exception):
    pass


class Team(enum.Enum):
    WHITE = 0
    BLACK = 1

    @property
    def direction(self):
        return 1 if self == Team.WHITE else -1

    @property
    def other(self):
        return Team.WHITE if self == Team.BLACK else Team.BLACK


class BoardValue(enum.Enum):
    EMPTY = 0
    WHITE_NORMAL = 1
    BLACK_NORMAL = 2
    WHITE_KING = 3
    BLACK_KING = 4

    @property
    def team(self) -> Team:
        if self == BoardValue.EMPTY:
            return None
        elif self == BoardValue.WHITE_NORMAL or self == BoardValue.WHITE_KING:
            return Team.WHITE
        else:
            return Team.BLACK

    @property
    def king(self) -> bool:
        return self == BoardValue.WHITE_KING or self == BoardValue.BLACK_KING

    @property
    def kinged(self) -> "BoardValue":
        if self == BoardValue.WHITE_NORMAL:
            return BoardValue.WHITE_KING
        elif self == BoardValue.BLACK_NORMAL:
            return BoardValue.BLACK_KING
        else:
            raise ValueError


@dataclasses.dataclass
class Move:
    team: Team
    start_pos: tuple[int, int]
    end_pos: tuple[int, int]

    @property
    def jump_pos(self) -> tuple[int, int] | None:
        dy = self.end_pos[1] - self.start_pos[1]

        jump = abs(dy) == 2
        if jump:
            return tuple((self.end_pos[i] + self.start_pos[i]) // 2 for i in range(2))
        return None

    @property
    def is_capture(self):
        return self.jump_pos is not None


class Board:
    def __init__(self, *, size: tuple[int, int] = (8, 8)):
        cols, rows = size
        if cols < 3:
            raise ValueError("Cols must be at least 3.")
        if rows < 5:
            raise ValueError("Rows must be at least 5.")

        self._cols = cols
        self._rows = rows
        self._board = [
            [
                (
                    (
                        BoardValue.WHITE_NORMAL
                        if irow < 2
                        else (
                            BoardValue.BLACK_NORMAL
                            if irow > rows - 2 - 1
                            else BoardValue.EMPTY
                        )
                    )
                    if (icol + irow) % 2 == 1
                    else None
                )
                for icol in range(cols)
            ]
            for irow in range(rows)
        ]
        self._last_move = None

    def __getitem__(self, item: tuple[int, int]) -> BoardValue:
        icol, irow = item
        if self.is_legal_position(item):
            return self._board[irow][icol]
        else:
            raise InvalidBoardPosition

    def __setitem__(self, key: tuple[int, int], value: BoardValue) -> None:
        icol, irow = key
        if self.is_legal_position(key):
            self._board[irow][icol] = value
        else:
            raise InvalidBoardPosition

    def __str__(self) -> str:
        symb = {
            BoardValue.WHITE_NORMAL: "[w]",
            BoardValue.WHITE_KING: "[W]",
            BoardValue.BLACK_NORMAL: "[b]",
            BoardValue.BLACK_KING: "[B]",
            BoardValue.EMPTY: "[ ]",
        }
        return "\n".join(
            "".join(
                "   " if not self.is_legal_position((x, y)) else symb[self[x, y]]
                for x in range(self.cols)
            )
            for y in range(self.rows)
        )

    def items(self):
        for irow in range(self.rows):
            for icol in range(self.cols):
                pos = (icol, irow)
                if self.is_legal_position(pos):
                    yield pos, self[pos]

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    def can_move(self, team: Team) -> bool:
        for move in self.possible_moves(team):
            return True
        return False

    def possible_moves(self, team: Team):
        move_differences = (
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
            (-2, -2),
            (-2, 2),
            (2, -2),
            (2, 2),
        )
        for (start_x, start_y), value in self.items():
            if value.team == team:
                for dx, dy in move_differences:
                    end_x, end_y = start_x + dx, start_y + dy
                    move = Move(
                        start_pos=(start_x, start_y), end_pos=(end_x, end_y), team=team
                    )
                    if self.is_legal_move(move):
                        yield move

    def is_legal_position(self, pos: tuple[int, int]) -> bool:
        x, y = pos
        if (x + y) % 2 == 0:
            return False
        if x < 0:
            return False
        if y < 0:
            return False
        if x >= self.cols:
            return False
        if y >= self.rows:
            return False
        return True

    def is_legal_move(self, move: Move) -> bool:
        if not self.is_legal_position(move.start_pos):
            return False
        if not self.is_legal_position(move.end_pos):
            return False

        start_value = self[move.start_pos]
        end_value = self[move.end_pos]

        if end_value != BoardValue.EMPTY:
            return False

        if move.jump_pos is not None and self[move.jump_pos].team != move.team.other:
            return False

        if self._last_move is not None and move.team == self._last_move.team:
            if move.start_pos != self._last_move.end_pos:
                return False

        if not move.is_capture:
            for pos, value in self.items():
                if value.team == move.team and self.is_capture_possible(pos):
                    return False

        dx = move.end_pos[0] - move.start_pos[0]
        dy = move.end_pos[1] - move.start_pos[1]

        if abs(dx) not in (1, 2):
            return False

        if abs(dx) != abs(dy):
            return False

        if not start_value.king and dy // abs(dy) != move.team.direction:
            return False

        if start_value.team != move.team:
            return False

        return True

    def possible_captures(self, start_pos: tuple[int, int]):
        start_value = self[start_pos]
        if start_value == BoardValue.EMPTY:
            return False
        team = start_value.team

        x, y = start_pos
        configurations = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        candidate_enemy_places = [(x + dx, y + dy) for dx, dy in configurations]
        spaces_must_be_free = [(x + 2 * dx, y + 2 * dy) for dx, dy in configurations]

        for i in range(len(configurations)):
            enemy_space = candidate_enemy_places[i]
            free_space = spaces_must_be_free[i]
            try:
                if (
                    self[enemy_space].team == team.other
                    and self[free_space] == BoardValue.EMPTY
                ):
                    move = Move(start_pos=start_pos, end_pos=free_space, team=team)
                    if self.is_legal_move(move):
                        yield move
            except InvalidBoardPosition:
                pass

    def is_capture_possible(self, start_pos: tuple[int, int]) -> bool:
        for move in self.possible_captures(start_pos):
            return True
        return False

    def perform_move(self, move: Move) -> None:
        if not self.is_legal_move(move):
            raise IllegalMove

        if move.jump_pos is not None:
            self[move.jump_pos] = BoardValue.EMPTY

        if not self[move.start_pos].king and move.end_pos[1] == (
            0 if move.team.direction == -1 else self.rows - 1
        ):
            self[move.end_pos] = self[move.start_pos].kinged
        else:
            self[move.end_pos] = self[move.start_pos]

        self[move.start_pos] = BoardValue.EMPTY
        self._last_move = move
