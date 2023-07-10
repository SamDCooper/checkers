import abc
import json
import os
import pygame
import random
import sys

import checkersai.board
import checkersai.game


class ISquareClickedObserver(abc.ABC):
    @abc.abstractmethod
    def on_square_clicked(self, pos: tuple[int, int]) -> None:
        raise NotImplementedError


class ITimerObserver(abc.ABC):
    @abc.abstractmethod
    def on_frame(self, time: float) -> None:
        raise NotImplementedError


class Graphics(checkersai.game.IGraphics):
    def __init__(
        self,
        *,
        board_size: tuple[int, int] = (8, 8),
        screen_width: int = None,
        screen_height: int = None,
        board_width: int = None,
        board_height: int = None,
    ):
        pygame.init()
        if screen_height is None:
            screen_height = 720
        if screen_width is None:
            screen_width = (screen_height * 16) // 9
        if board_height is None:
            board_height = screen_height
        if board_width is None:
            board_width = board_height

        board_cols, board_rows = board_size
        self._board_cols = board_cols
        self._board_rows = board_rows
        self._cell_height = board_height // board_rows
        self._cell_width = board_width // board_cols
        self._board_height = board_height
        self._board_width = board_width

        self._screen = pygame.display.set_mode((screen_width, screen_height))

        with open("data/index.json", "r") as f:
            data = json.load(f)

        self._bg_surface = pygame.Surface((screen_width, screen_height))
        bg_img = pygame.image.load("data/" + data["background"])
        for y in range(0, screen_height, bg_img.get_height()):
            for x in range(0, screen_width, bg_img.get_width()):
                self._bg_surface.blit(bg_img, (x, y))

        square_fields = {0: "white_square", 1: "black_square"}
        board_left = screen_width // 2 - board_width // 2
        board_top = screen_height // 2 - board_height // 2
        for icol in range(board_cols):
            x = board_left + self._cell_width * icol
            for irow in range(board_rows):
                y = board_top + self._cell_height * irow
                source = random.choice(data[square_fields[(icol + irow) % 2]])
                square_img = pygame.transform.scale(
                    pygame.image.load("data/" + source),
                    (self._cell_width, self._cell_height),
                )
                self._bg_surface.blit(square_img, (x, y))

        self._img_pieces = {}
        piece_fields = {
            checkersai.board.Team.WHITE: "white_piece",
            checkersai.board.Team.BLACK: "black_piece",
        }
        for k, v in piece_fields.items():
            self._img_pieces[k] = self._load_image(data, v)
        self._img_selected_underlay = self._load_image(data, "selected_underlay")
        self._img_capturable_underlay = self._load_image(data, "capturable_underlay")
        self._img_king_overlay = self._load_image(data, "king_overlay")

        self._board_left = self._screen.get_width() // 2 - self._board_width // 2
        self._board_top = self._screen.get_height() // 2 - self._board_height // 2

        self._square_click_observers = set()
        self._time_observers = set()

    def _load_image(self, data, key) -> object:
        return pygame.transform.scale(
            pygame.image.load(os.path.join("data", data[key])),
            (self._cell_width, self._cell_height),
        )

    def update(
        self,
        data: checkersai.game.GameData,
        time: float,
    ) -> None:
        for observer in self._time_observers:
            observer.on_frame(time)

        self._screen.blit(self._bg_surface, (0, 0))

        capturable_squares = set()
        for pos, value in data.board.items():
            if value.team == data.current_team:
                for q in data.board.possible_captures(pos):
                    capturable_squares.add(q.jump_pos)

        for pos, value in data.board.items():
            icol, irow = pos
            x = self._board_left + self._cell_width * icol
            y = self._board_top + self._cell_height * irow

            img = self._img_pieces.get(value.team, None)
            if img is not None:
                if pos == data.current_player.selected_square:
                    self._screen.blit(self._img_selected_underlay, (x, y))
                elif pos in capturable_squares:
                    self._screen.blit(self._img_capturable_underlay, (x, y))
                self._screen.blit(img, (x, y))
                if value.king:
                    self._screen.blit(self._img_king_overlay, (x, y))

        pygame.display.flip()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.MOUSEBUTTONUP:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                x = (mouse_x - self._board_left) // self._cell_width
                y = (mouse_y - self._board_top) // self._cell_height
                for observer in self._square_click_observers:
                    observer.on_square_clicked((x, y))

    def add_square_click_observer(self, observer: ISquareClickedObserver) -> None:
        self._square_click_observers.add(observer)

    def add_time_observer(self, observer: ITimerObserver) -> None:
        self._time_observers.add(observer)
