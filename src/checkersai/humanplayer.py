import checkersai.board
import checkersai.game
import checkersai.graphics


class HumanPlayer(checkersai.game.IPlayer, checkersai.graphics.ISquareClickedObserver):
    def __init__(self, team: checkersai.board.Team, gui: checkersai.graphics.Graphics):
        self._team = team
        self._start_pos = None
        self._end_pos = None
        self._board = None
        gui.add_square_click_observer(self)

    def on_square_clicked(self, pos: tuple[int, int]) -> None:
        if self._board is not None:
            if self._board.is_legal_position(pos):
                if self._start_pos is None:
                    if self._board[pos].team == self._team:
                        self._start_pos = pos
                else:
                    if self._board.is_legal_move(
                        checkersai.board.Move(
                            team=self._team, start_pos=self._start_pos, end_pos=pos
                        )
                    ):
                        self._end_pos = pos
                    else:
                        self._start_pos = None

    @property
    def selected_square(self) -> tuple[int, int] | None:
        return self._start_pos

    @property
    def destination_square(self) -> tuple[int, int] | None:
        return self._end_pos

    def on_turn_started(self, board: checkersai.game.PlayerBoard) -> None:
        self._board = board

    def on_move_started(self, board: checkersai.game.PlayerBoard) -> None:
        self._start_pos = None
        self._end_pos = None

    def on_move_rejected(self) -> None:
        self._start_pos = None
        self._end_pos = None

    def on_move_completed(self) -> None:
        self._start_pos = None
        self._end_pos = None

    def on_turn_completed(self) -> None:
        self._board = None

    def on_win(self) -> None:
        pass

    def on_loss(self) -> None:
        pass
