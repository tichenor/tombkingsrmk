from __future__ import annotations

import random
from typing import Iterator, Tuple, List, TYPE_CHECKING, Dict

import tcod

import entity_factories
import tile_types

from config import Config as cfg
from entity_factories import EntityFactory
from game_map import GameMap

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

"""The following dictionaries contain weights along with a minimum floor value for each enemy and item that can 
spawn. Each key in the dictionaries represents the minimum floor that a certain entity can spawn, and its value
consists of a pair of the entity and its associated weight."""

ITEM_CHANCES: Dict[int, List[Tuple[Entity, int]]] = {
    0: [
        (EntityFactory.potion_health, 35),
        (EntityFactory.scroll_confuse, 10),
        (EntityFactory.scroll_lightning, 25),
        (EntityFactory.weapon_dagger, 25),
        (EntityFactory.armor_leather, 20),
    ],
    1: [(EntityFactory.scroll_fireball, 25)],
}

MONSTER_CHANCES: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(EntityFactory.enemy_orc, 80)],
    3: [(EntityFactory.enemy_troll, 15)],
    5: [(EntityFactory.enemy_troll, 30)],
    7: [(EntityFactory.enemy_troll, 60)],
}


class Rectangle:
    """Simple class to represent a rectangular room in a dungeon."""
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


def get_max_by_floor(weighted_chances: List[Tuple[int, int]], floor: int) -> int:
    """Get the maximum number of items or monsters that can spawn per room for a given dungeon `floor`.
    The first number in each element of `weighted_chances` represents the minimum dungeon floor, and the
    second value represents the max number of items/monsters that can spawn from that floor onwards."""
    current = 0

    for floor_level, value in weighted_chances:
        if floor_level > floor:
            break
        else:
            current = value
    return current


def pick_entities_randomly(
        weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
        num_choices: int,
        floor: int,
) -> List[Entity]:
    """Select `num_choices` entities randomly using weights that depend on the dungeon floor."""
    # Store the entities that can spawn on the current floor and their weights in a dictionary.
    entity_weights: Dict[Entity, int] = {}
    for key, values in weighted_chances_by_floor.items():
        if key > floor:  # The minimum floor that something can spawn is higher than the current `floor`.
            break
        else:
            for value in values:
                entity, weight = value  # Each value is an (entity, weight)-pair.
                entity_weights[entity] = weight  # Populate our list of possible things that can spawn.

    possible_entities = list(entity_weights.keys())
    chances = list(entity_weights.values())
    chosen_entities = random.choices(
        possible_entities, weights=chances, k=num_choices
    )
    return chosen_entities


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
        engine: Engine,
) -> GameMap:
    """Generate a new dungeon map."""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[Rectangle] = []
    center_of_last_room: Tuple[int, int] = (0, 0)

    for r in range(max_rooms):

        # Make a new room with random dimensions.
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        new_room = Rectangle(x, y, room_width, room_height)

        # If room intersects an earlier room, skip it and try again.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue

        dungeon.tiles[new_room.inner] = tile_types.FLOOR

        if len(rooms) == 0:
            # The first room, where the player starts
            player.place(*new_room.center, dungeon)

        else:
            # Generate some entities.
            place_entities(new_room, dungeon, engine.game_world.current_floor)
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.FLOOR

            center_of_last_room = new_room.center

        # Add the stair down to the last room created.
        dungeon.tiles[center_of_last_room] = tile_types.DOWN_STAIRS
        dungeon.downstairs_location = center_of_last_room

        rooms.append(new_room)

    return dungeon


def place_entities(room: Rectangle, dungeon: GameMap, floor_number: int) -> None:
    """Place entities randomly in a given room."""
    num_monsters = random.randint(
        0, get_max_by_floor(cfg.Map.MAX_MONSTERS_BY_FLOOR, floor_number)
    )
    num_items = random.randint(
        0, get_max_by_floor(cfg.Map.MAX_ITEMS_BY_FLOOR, floor_number)
    )

    monsters: List[Entity] = pick_entities_randomly(
        MONSTER_CHANCES, num_monsters, floor_number
    )
    items: List[Entity] = pick_entities_randomly(
        ITEM_CHANCES, num_items, floor_number
    )

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.copy_to(dungeon, x, y)
