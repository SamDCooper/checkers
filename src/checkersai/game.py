import abc
import datetime
import dataclasses
import logging

import checkersai.board

logger = logging.getLogger(__name__)


class PlayerBoard:
    def __init__(self, underlying: checkersai.board.Board):
        self._underlying = underlying

    def __getitem__(self, item) -> checkersai.board.BoardValue:
        return self._underlying[item]

    def __str__(self) -> str:
        return str(self._underlying)

    @property
    def rows(self) -> int:
        return self._underlying.rows

    @property
    def cols(self) -> int:
        return self._underlying.cols

    def is_legal_position(self, pos: tuple[int, int]) -> bool:
        return self._underlying.is_legal_position(pos)

    def is_legal_move(self, move: checkersai.board.Move) -> bool:
        return self._underlying.is_legal_move(move)

    def items(self):
        for item in self._underlying.items():
            yield item

    def possible_moves(self, team: checkersai.board.Team):
        for move in self._underlying.possible_moves(team):
            yield move


class IPlayer(abc.ABC):
    @property
    @abc.abstractmethod
    def selected_square(self) -> tuple[int, int] | None:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def destination_square(self) -> tuple[int, int] | None:
        raise NotImplementedError

    @abc.abstractmethod
    def on_turn_started(self, board: PlayerBoard) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def on_move_started(self, board: PlayerBoard) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def on_move_rejected(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def on_move_completed(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def on_turn_completed(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def on_win(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def on_loss(self) -> None:
        raise NotImplementedError


@dataclasses.dataclass
class GameData:
    players: dict[checkersai.board.Team, IPlayer]
    current_team: checkersai.board.Team
    board: checkersai.board.Board
    current_time: float = 0
    last_move: checkersai.board.Move = None

    @property
    def current_player(self) -> IPlayer:
        return self.players[self.current_team]

    @property
    def other_player(self) -> IPlayer:
        return self.players[self.current_team.other]

    def change_player(self) -> None:
        self.current_player.on_turn_completed()
        self.current_team = self.current_team.other
        if self.board.can_move(self.current_team):
            logger.info("%s's turn.\n%s", self.current_team.name, self.board)
            self.current_player.on_turn_started(PlayerBoard(self.board))
            self.current_player.on_move_started(PlayerBoard(self.board))


class IGraphics(abc.ABC):
    @abc.abstractmethod
    def handle_events(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def update(
        self,
        data: GameData,
        time: float,
    ) -> None:
        raise NotImplementedError


class Game:
    def __init__(
        self,
        graphics: IGraphics,
        t_ms_per_update: datetime.timedelta,
        board_size: tuple[int, int],
    ):
        self._graphics = graphics
        self._t_ms_per_update = t_ms_per_update
        self._board_size = board_size

    def start_game(
        self,
        white_player: IPlayer,
        black_player: IPlayer,
        first_team: checkersai.board.Team,
    ) -> None:
        data = GameData(
            players={
                checkersai.board.Team.WHITE: white_player,
                checkersai.board.Team.BLACK: black_player,
            },
            current_team=first_team,
            board=checkersai.board.Board(size=self._board_size),
        )
        logger.info("%s's turn.\n%s", data.current_team.name, data.board)
        data.current_player.on_turn_started(PlayerBoard(data.board))
        data.current_player.on_move_started(PlayerBoard(data.board))

        t_prev = datetime.datetime.now()
        t_lag = datetime.timedelta(0)
        t_game = datetime.timedelta(0)

        state = self._state_wait_player_move

        while data.board.can_move(data.current_team):
            t_current = datetime.datetime.now()
            t_elapsed = t_current - t_prev
            t_prev = t_current
            t_lag += t_elapsed

            if self._graphics is not None:
                self._graphics.handle_events()

            while t_lag >= self._t_ms_per_update:
                t_lag -= self._t_ms_per_update
                t_game += self._t_ms_per_update
                data.current_time = t_game.total_seconds()
                next_state = state(data)
                if next_state is not None:
                    state = next_state

            if self._graphics is not None:
                self._graphics.update(data, (t_game + t_lag).total_seconds())
        logger.info("%s won.", data.current_team.other.name)
        data.other_player.on_win()
        data.current_player.on_loss()

    def _state_wait_player_move(self, data: GameData) -> None:
        start_pos = data.current_player.selected_square
        end_pos = data.current_player.destination_square

        if start_pos is not None and end_pos is not None:
            move, kinged = self._perform_move(data, start_pos, end_pos)
            if move is not None:
                if (
                    not kinged
                    and move.is_capture
                    and data.board.is_capture_possible(move.end_pos)
                ):
                    data.current_player.on_move_started(PlayerBoard(data.board))
                    return self._state_wait_player_jump
                else:
                    data.change_player()
            else:
                data.current_player.on_move_rejected()

    def _state_wait_player_jump(self, data: GameData) -> None:
        start_pos = data.last_move.end_pos
        if data.current_player.selected_square == data.last_move.end_pos:
            end_pos = data.current_player.destination_square
            if end_pos is not None:
                move, kinged = self._perform_move(data, start_pos, end_pos)
                if move is not None:
                    if kinged or not data.board.is_capture_possible(end_pos):
                        data.change_player()
                        return self._state_wait_player_move
                    else:
                        data.current_player.on_move_completed()
                        data.current_player.on_move_started(PlayerBoard(data.board))
                else:
                    data.current_player.on_move_rejected()

    def _perform_move(
        self, data: GameData, start_pos: tuple[int, int], end_pos: tuple[int, int]
    ) -> tuple[checkersai.board.Move, bool]:
        was_king = data.board[start_pos].king
        move = checkersai.board.Move(
            team=data.current_team, start_pos=start_pos, end_pos=end_pos
        )
        if data.board.is_legal_move(move):
            data.board.perform_move(move)
            logger.info(
                "%s moves (%d, %d) -> (%d, %d).",
                data.current_team.name,
                *start_pos,
                *end_pos,
            )
            data.last_move = move
            data.current_player.on_move_completed()
            return move, not was_king and data.board[end_pos].king
        return None, None
