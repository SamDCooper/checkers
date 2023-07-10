import argparse
import datetime
import json
import logging
import random

import checkersai
import checkersai.board
import checkersai.humanplayer
import checkersai.game
import checkersai.graphics
import checkersai.computeropponent

logger = logging.getLogger("checkersai")

available_players = {
    "human": checkersai.humanplayer.HumanPlayer,
    "random": checkersai.computeropponent.RandomOpponent,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="checkersai", description="Play checkers vs the computer"
    )
    parser.add_argument("--version", action="version", version=checkersai.__version__)
    parser.add_argument("--board-size", action="store", nargs=2, type=int, default=(8, 8), help="Size of the board. 2 args.")
    parser.add_argument(
        "--white",
        choices=available_players,
        default="human",
        help="Sets which player is white. White always goes first.",
    )
    parser.add_argument(
        "--black",
        choices=available_players,
        default="random",
        help="Sets which player is black. Black always goes second.",
    )
    parser.add_argument(
        "--seed",
        action="store",
        type=int,
        help="Set the seed for random number generation.",
    )
    parser.add_argument(
        "--logfile", action="store", type=str, help="Log the run to file. Disabled for multiprocessing."
    )
    parser.add_argument(
        "--logformat",
        action="store",
        type=str,
        default="%(asctime)s [%(levelname)s]: %(message)s",
        help="Format for log entries.",
    )
    parser.add_argument(
        "--loglevel",
        choices=["INFO", "WARNING", "ERROR"],
        default="WARNING",
        help="Minimum level to log.",
    )
    return parser.parse_args()


def main() -> None:
    start_time = datetime.datetime.now()

    args = parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if args.logfile is not None:
        handler = logging.FileHandler(args.logfile)
        handler.setFormatter(logging.Formatter(args.logformat))
        logger.addHandler(handler)
        logger.setLevel(logging.getLevelName(args.loglevel))
    logger.info("----------------------------------------------------------------")
    logger.info("New session start. Cmd line params given:")
    for arg, val in vars(args).items():
        if val is not None:
            logger.info("%s = %s", arg, str(val))

    play_mode(**vars(args))
    logger.info(
        "Finished execution. Total run time: %s", datetime.datetime.now() - start_time
    )
    logger.info("----------------------------------------------------------------")


def play_mode(*, white, black, board_size, **kwargs) -> None:
    gui = checkersai.graphics.Graphics(
        screen_height=800, board_height=720, screen_width=800, board_size=board_size
    )
    white_player = available_players[white](checkersai.board.Team.WHITE, gui)
    black_player = available_players[black](checkersai.board.Team.BLACK, gui)
    start_team = checkersai.board.Team.WHITE

    game = checkersai.game.Game(gui, datetime.timedelta(milliseconds=16.67), board_size)
    game.start_game(white_player, black_player, start_team)


main()