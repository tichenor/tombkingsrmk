from __future__ import annotations

import lzma
import pickle
import random
from typing import TYPE_CHECKING, Tuple, List, Optional, Set

from tcod.console import Console
import tcod.map

from entity_factories import EntityFactory
import exceptions
from config import Config as cfg
from message_logs import MessageLog
import render_functions
from ticker import Ticker

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap, GameWorld


class Engine:

    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor, fov_radius: int):

        self._message_log = MessageLog()
        self._mouse_location = (0, 0)
        self._player = player
        self._fov_radius = fov_radius
        self._ticker = Ticker()

        self._debug_log = None
        if cfg.DEBUG:
            self._debug_log = MessageLog()

    def handle_ai(self) -> None:
        """Go through the turn schedule and let actors do their turns until it is the player's turn.
        If there are other actors scheduled for the same tick as the player, they will currently get to
        act first."""
        players_turn = False

        #TODO: Might cause bugs to have an arbitrarily long while-loop here
        while not players_turn:

            actors = self.ticker.next_turn()  # Get a list of any actors who are scheduled for this tick

            for actor in actors:
                if actor.is_alive:
                    if actor == self.player:
                        # Schedule the player's next turn.
                        self.ticker.schedule_turn(actor.energy.speed, actor)
                        players_turn = True
                    else:
                        if actor.parent != self.game_map:
                            # Scheduled turns for actors not on the current map are ignored.
                            continue
                        try:
                            actor.ai.perform()
                        except exceptions.Impossible:
                            pass
                        # Need to break out of this loop if the player died as the result of an action.
                        if not self.player.is_alive:
                            players_turn = True
                            break
                        self.ticker.schedule_turn(actor.energy.speed, actor)

            self.ticker.ticks += 1  # Increment the time

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

        render_functions.render_bar(
            console=console,
            current_value=self._player.fighter.hp,
            max_value=self._player.fighter.max_hp,
            total_width=20,
        )

        render_functions.render_dungeon_floor_text(
            console=console,
            level=self.game_world.current_floor,
            location=(cfg.Gui.DUNGEON_FLOOR_TEXT_POS_X, cfg.Gui.DUNGEON_FLOOR_TEXT_POS_Y),
        )

        render_functions.render_names_at_mouse_location(
            console=console, x=cfg.Tooltip.POS_X, y=cfg.Tooltip.POS_Y, engine=self
        )

    def parse_user_command(self, cmd: str) -> None:
        if not cmd:
            return
        response = f"Unknown command: {cmd}"
        col = cfg.Color.INVALID
        player = self._player

        if cmd == "heal":
            amt = player.fighter.add_hp(player.fighter.max_hp)
            response = f"Restored {amt} health."
            col = cfg.Color.GREEN

        elif cmd == "lvlup":
            to_next = player.level.experience_to_next_level - player.level.current_experience
            player.level.add_experience(to_next)
            response = f"Gained {to_next} experience."
            col = cfg.Color.GREEN

        elif cmd.startswith("spawnenemy "):
            enemy = cmd[len("spawnenemy "):]
            if enemy in EntityFactory.__monster_dict__.keys():
                tries = 9
                while tries > 0:
                    x, y = player.x + random.randint(-2, 2), player.y + random.randint(-2, 2)
                    if (x, y) == (player.x, player.y):
                        tries -= 1
                        continue
                    if self.game_map.in_bounds(x, y)\
                            and not any(e.x == x and e.y == y for e in self.game_map.entities)\
                            and self.game_map.tiles["walkable"][x, y]:
                        EntityFactory.__monster_dict__[enemy].copy_to(self.game_map, x, y)
                        response = f"Enemy spawned: {enemy}."
                        col = cfg.Color.GREEN
                        break
                    tries -= 1
                else:
                    response = f"Could not generate spawn location for enemy: {enemy}."
                    col = cfg.Color.INVALID
            else:
                response = f"Unknown enemy: {enemy}."
                col = cfg.Color.INVALID

        elif cmd.startswith("spawnitem "):
            item = cmd[len("spawnitem "):]
            if item in EntityFactory.__items_dict__.keys():
                tries = 9
                while tries > 0:
                    x, y = player.x + random.randint(-2, 2), player.y + random.randint(-2, 2)
                    if (x, y) == (player.x, player.y):
                        tries -= 1
                        continue
                    if self.game_map.in_bounds(x, y)\
                            and not any(e.x == x and e.y == y for e in self.game_map.entities)\
                            and self.game_map.tiles["walkable"][x, y]:
                        EntityFactory.__items_dict__[item].copy_to(self.game_map, x, y)
                        response = f"Item spawned: {item}."
                        col = cfg.Color.GREEN
                        break
                    tries -= 1
                else:
                    response = f"Could not generate spawn location for item: {item}."
                    col = cfg.Color.INVALID
            else:
                response = f"Unknown item: {item}."
                col = cfg.Color.INVALID

        elif cmd == "list enemies":
            response = ", ".join(EntityFactory.__monster_dict__.keys())
            col = cfg.Color.WHITE

        elif cmd == "list items":
            response = ", ".join(EntityFactory.__items_dict__.keys())
            col = cfg.Color.WHITE

        self._debug_log.add_message(response, fg=col)

    @property
    def ticker(self):
        return self._ticker

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

    @property
    def debug_log(self):
        return self._debug_log


