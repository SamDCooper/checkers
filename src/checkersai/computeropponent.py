import abc

import checkersai.board
import checkersai.game
import checkersai.graphics

import random

from checkersai.game import PlayerBoard


class ComputerOpponent(checkersai.game.IPlayer, checkersai.graphics.ITimerObserver):
    def __init__(
        self,
        team: checkersai.board.Team,
        gui: checkersai.graphics.Graphics,
        time_between_moves: float = 1.0,
        time_between_clicks: float = 0.5,
    ):
        self._team = team
        gui.add_time_observer(self)
        self._time_between_moves = time_between_moves
        self._time_between_clicks = time_between_clicks
        self._next_move = None
        self._current_time = 0.0
        self._move_time = 0.0
        self._my_turn = False

    @property
    def team(self):
        return self._team

    def on_frame(self, time: float) -> None:
        self._current_time = time

    @property
    def selected_square(self) -> tuple[int, int] | None:
        if self._my_turn and self._current_time > self._move_time:
            return self._next_move.start_pos
        else:
            return None

    @property
    def destination_square(self) -> tuple[int, int] | None:
        if (
            self._my_turn
            and self._current_time > self._move_time + self._time_between_clicks
        ):
            return self._next_move.end_pos
        else:
            return None

    def on_turn_started(self, board: checkersai.game.PlayerBoard) -> None:
        self._my_turn = True

    def on_move_started(self, board: checkersai.game.PlayerBoard) -> None:
        self._next_move = self.next_move(board)
        self._move_time = self._current_time + self._time_between_moves

    def on_move_rejected(self) -> None:
        pass

    def on_move_completed(self) -> None:
        pass

    def on_turn_completed(self) -> None:
        self._my_turn = False

    def on_win(self) -> None:
        pass

    def on_loss(self) -> None:
        pass

    @abc.abstractmethod
    def next_move(self, board: checkersai.game.PlayerBoard) -> checkersai.board.Move:
        raise NotImplementedError


class RandomOpponent(ComputerOpponent):
    def __init__(self, team: checkersai.board.Team, gui: checkersai.graphics.Graphics):
        super().__init__(team, gui)

    def next_move(self, board: checkersai.game.PlayerBoard) -> checkersai.board.Move:
        return random.choice([move for move in board.possible_moves(self.team)])
