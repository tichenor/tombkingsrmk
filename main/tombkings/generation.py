from __future__ import annotations

import random
from typing import Iterator, Tuple, List, TYPE_CHECKING

import tcod

import entity_factories
import tile_types

from entity_factories import EntityFactory
from entity import Entity
from game_map import GameMap

if TYPE_CHECKING:
    from engine import Engine


class Rectangle:

    def __init__(self, x: int, y: int, width: int, height: int):

        self._x1 = x
        self._y1 = y
        self._x2 = x + width
        self._y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        """Find the coordinates of the center of the room."""
        center_x = int((self._x1 + self._x2) / 2)
        center_y = int((self._y1 + self._y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self._x1 + 1, self._x2), slice(self._y1 + 1, self._y2)

    @property
    def y2(self):
        return self._y2

    @property
    def x2(self):
        return self._x2

    @property
    def x1(self):
        return self._x1

    @property
    def y1(self):
        return self._y1

    def intersects(self, other: Rectangle) -> bool:
        """Return True if this rectangle overlaps with another."""
        return (
            self._x1 <= other._x2
            and self._x2 >= other._x1
            and self._y1 <= other._y2
            and self._y2 >= other._y1
        )


def tunnel_between(start: Tuple[int, int], end: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for the tunnel using Bresenham's line algorithm.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y

    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        max_monsters_per_room: int,
        max_items_per_room: int,
        engine: Engine,
) -> GameMap:
    """Generate a new dungeon map."""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[Rectangle] = []

    for r in range(max_rooms):

        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        new_room = Rectangle(x, y, room_width, room_height)

        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # If there is an intersection, skip to next attempt.

        dungeon.tiles[new_room.inner] = tile_types.FLOOR

        if len(rooms) == 0:
            # The first room, where the player starts
            player.place(*new_room.center, dungeon)

        else:
            # Generate some entities.
            place_entities(new_room, dungeon, max_monsters_per_room, max_items_per_room)
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.FLOOR

        rooms.append(new_room)

    return dungeon


def place_entities(room: Rectangle, dungeon: GameMap, max_monsters: int, max_items: int) -> None:
    """Place entities randomly in a given room."""
    num_monsters = random.randint(0, max_monsters)
    num_items = random.randint(0, max_items)

    for i in range(num_monsters):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            if random.random() < 0.8:
                EntityFactory.orc.copy_to(dungeon, x, y)
            else:
                EntityFactory.troll.copy_to(dungeon, x, y)

    for i in range(num_items):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            item_chance = random.random()

            if item_chance < 0.4:
                EntityFactory.potion_health.copy_to(dungeon, x, y)
            elif item_chance < 0.6:
                EntityFactory.scroll_confuse.copy_to(dungeon, x, y)
            elif item_chance < 0.8:
                EntityFactory.scroll_lightning.copy_to(dungeon, x, y)
            else:
                EntityFactory.scroll_fireball.copy_to(dungeon, x, y)
