"""Handle the loading and initialization of game sessions."""
from __future__ import annotations

import copy
import lzma
import pickle
import traceback
from typing import Optional

import tcod
from overrides import overrides

from config import Config as cfg
from engine import Engine
from entity_factories import EntityFactory
import input_handlers
from game_map import GameWorld
from generation import generate_dungeon


# Load the background image and remove the alpha channel.
background_image = tcod.image.load("assets/menu_background1.png")[:, :, :3]


def new_game() -> Engine:
    """Return a brand new game session as an engine instance."""
    player = copy.deepcopy(EntityFactory.player)
    engine = Engine(player=player, fov_radius=cfg.Vision.DEFAULT_FOV_RADIUS)

    engine.game_world = GameWorld(
        engine=engine,
        max_rooms=cfg.Map.MAX_ROOMS,
        room_min_size=cfg.Map.ROOM_MIN_SIZE,
        room_max_size=cfg.Map.ROOM_MAX_SIZE,
        map_width=cfg.Map.WIDTH,
        map_height=cfg.Map.HEIGHT,
    )
    engine.game_world.generate_floor()
    engine.update_fov()

    engine.message_log.add_message(
        "Hello and welcome, adventurer, to yet another dungeon!", cfg.Color.WELCOME_TEXT
    )
    return engine


def save_game(handler: input_handlers.BaseEventHandler, file_name: str) -> None:
    """If the current event handler has an active Engine, then save it."""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(file_name)


def load_game(file_name: str) -> Engine:
    """Load an Engine instance from a file."""
    with open(file_name, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    return engine


class MainMenu(input_handlers.BaseEventHandler):
    """Handle the main menu rendering and input. This input handler is specific to the start of the game and
    is therefore not among the others in input_handlers.py. This handler will not be called during the normal
    course of the game."""

    @overrides
    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""
        console.draw_semigraphics(background_image, 0, 0)

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "TOMBS OF THE ANCIENT KINGS",
            fg=cfg.Color.MENU_TITLE,
            alignment=tcod.CENTER,
        )

        console.print(
            console.width // 2,
            console.height - 2,
            "By Arvid",
            fg=cfg.Color.MENU_TITLE,
            alignment=tcod.CENTER,
        )

        menu_width = cfg.MainMenu.WIDTH

        for i, text in enumerate(
            ["[N] Play a new game", "[C] Continue last game", "[Q] Quit"]
        ):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=cfg.Color.MENU_TEXT,
                bg=cfg.Color.BLACK,
                alignment=tcod.CENTER,
                bg_blend=tcod.BKGND_ALPHA(64),
            )

    @overrides
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[input_handlers.BaseEventHandler]:
        if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
            raise SystemExit()
        elif event.sym == tcod.event.K_c:
            try:
                return input_handlers.MainEventHandler(load_game("savegame.sav"))
            except FileNotFoundError:
                return input_handlers.PopupMessage(self, "No saved game to load.")
            except Exception as exc:
                traceback.print_exc()  # Print to stderr.
                return input_handlers.PopupMessage(self, f"Failed to load save:\n{exc}")
        elif event.sym == tcod.event.K_n:
            return input_handlers.MainEventHandler(new_game())

        return None
