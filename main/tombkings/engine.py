from __future__ import annotations

import lzma
import pickle
from typing import TYPE_CHECKING, Tuple

from tcod.console import Console
import tcod.map

import exceptions
from config import Config as cfg
from message_log import MessageLog
from render_functions import render_bar, render_names_at_mouse_location

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap


class Engine:

    game_map: GameMap

    def __init__(self, player: Actor, fov_radius: int):

        self._message_log = MessageLog()
        self._mouse_location = (0, 0)
        self._player = player
        self._fov_radius = fov_radius

    def handle_ai(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass  # Ignore impossible action exceptions from AI.

    def update_fov(self) -> None:
        """Recompute the field of vision (visible area) based on the player's point of view."""
        self.game_map.visible_tiles[:] = tcod.map.compute_fov(
            self.game_map.tiles["transparent"],
            (self._player.x, self._player.y),
            radius=self._fov_radius,
        )
        # If a tile is 'visible' it should be set to 'explored'.
        self.game_map.explored_tiles |= self.game_map.visible_tiles

    def save_as(self, file_name: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(file_name, "wb") as f:
            f.write(save_data)

    def render(self, console: Console) -> None:

        # Draw the map
        self.game_map.render(console)

        # Render gui, hud, etc.

        self._message_log.render(
            console=console,
            x=cfg.Log.POS_X,
            y=cfg.Log.POS_Y,
            width=cfg.Log.WIDTH,
            height=cfg.Log.HEIGHT
        )

        render_bar(
            console=console,
            current_value=self._player.fighter.hp,
            max_value=self._player.fighter.max_hp,
            total_width=20,
        )

        render_names_at_mouse_location(console=console, x=cfg.Tooltip.POS_X, y=cfg.Tooltip.POS_Y, engine=self)

    @property
    def player(self):
        return self._player

    @property
    def message_log(self) -> MessageLog:
        return self._message_log

    @property
    def mouse_location(self) -> Tuple[int, int]:
        return self._mouse_location

    @mouse_location.setter
    def mouse_location(self, val: Tuple[int, int]) -> None:
        self._mouse_location = val

