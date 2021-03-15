from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Iterator, Tuple, List, TYPE_CHECKING, Dict, Optional

import tcod
import numpy as np
from collections import deque

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


class MapGenerator:

    @staticmethod
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


class BasicRectangular(MapGenerator):

    def __init__(self,
                 room_min_size: int,
                 room_max_size: int,
                 map_width: int,
                 map_height: int,
                 max_rooms: int,
                 engine: Engine):
        self.room_min_size = room_min_size
        self.room_max_size = room_max_size
        self.map_width = map_width
        self.map_height = map_height
        self.max_rooms = max_rooms
        self.engine = engine

    def generate_map(self) -> GameMap:
        """Generate a new dungeon map."""
        player = self.engine.player
        dungeon = GameMap(self.engine, self.map_width, self.map_height, entities=[player])

        rooms: List[Rectangle] = []
        center_of_last_room: Tuple[int, int] = (0, 0)

        for r in range(self.max_rooms):

            # Make a new room with random dimensions.
            room_width = random.randint(self.room_min_size, self.room_max_size)
            room_height = random.randint(self.room_min_size, self.room_max_size)

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
                BasicRectangular.__place_entities(new_room, dungeon, self.engine.game_world.current_floor)
                # Dig out a tunnel between this room and the previous one.
                for x, y in BasicRectangular.__tunnel_between(rooms[-1].center, new_room.center):
                    dungeon.tiles[x, y] = tile_types.FLOOR

                center_of_last_room = new_room.center

            # Add the stair down to the last room created.
            dungeon.tiles[center_of_last_room] = tile_types.DOWN_STAIRS
            dungeon.downstairs_location = center_of_last_room

            rooms.append(new_room)

        return dungeon

    @staticmethod
    def __place_entities(room: Rectangle, dungeon: GameMap, floor_number: int) -> None:
        """Place entities randomly in a given room."""
        num_monsters = random.randint(
            0, BasicRectangular.__get_max_by_floor(cfg.Map.MAX_MONSTERS_BY_FLOOR, floor_number)
        )
        num_items = random.randint(
            0, BasicRectangular.__get_max_by_floor(cfg.Map.MAX_ITEMS_BY_FLOOR, floor_number)
        )

        monsters: List[Entity] = BasicRectangular.pick_entities_randomly(
            MONSTER_CHANCES, num_monsters, floor_number
        )
        items: List[Entity] = BasicRectangular.pick_entities_randomly(
            ITEM_CHANCES, num_items, floor_number
        )

        for entity in monsters + items:
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
                entity.copy_to(dungeon, x, y)

    @staticmethod
    def __get_max_by_floor(weighted_chances: List[Tuple[int, int]], floor: int) -> int:
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

    @staticmethod
    def __tunnel_between(start: Tuple[int, int], end: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
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


class CellularAutomata(MapGenerator):
    """WORK IN PROGRESS"""

    # Floor (walkable) tile represented by a 0
    # Wall (blocking) tile represented by a 1
    # Visited Floor tile (flood fill algorithm) represented by a 2

    def __init__(self, map_width: int, map_height: int, engine: Engine, percent_walls: int = 40):
        self.map_width: int = map_width
        self.map_height: int = map_height
        self.engine: Engine = engine
        self.percent_walls: int = percent_walls

        # Initialize map filled with floor/walkable tiles
        self.internal_map: np.ndarray = np.zeros(
            (self.map_width, self.map_height),
            dtype=np.int8,
            order="F"
        )

    def generate_map(self) -> GameMap:
        self.__random_fill()
        for _ in range(4):
            self.internal_map = self.__next_gen(0)
        for _ in range(3):
            self.internal_map = self.__next_gen(1)

        self.__flood_fill_test()

        # Create external map from representation
        dungeon = GameMap(self.engine, self.map_width, self.map_height, [self.engine.player])
        for x in range(self.map_width):
            for y in range(self.map_height):
                if self.internal_map[x, y] == 2:
                    dungeon.tiles[x, y] = tile_types.FLOOR

        dungeon = self.__place_entities(dungeon, self.engine.game_world.current_floor)
        return dungeon

    def __place_entities(self, dungeon: GameMap, floor_number: int) -> GameMap:
        max_monsters = cfg.Map.MAX_MONSTERS_PER_FLOOR
        max_items = cfg.Map.MAX_ITEMS_PER_FLOOR

        monsters: List[Entity] = MapGenerator.pick_entities_randomly(
            MONSTER_CHANCES, max_monsters, floor_number
        )
        items: List[Entity] = MapGenerator.pick_entities_randomly(
            ITEM_CHANCES, max_items, floor_number
        )

        spawn_tries = 3
        for entity in monsters + items:
            for _ in range(spawn_tries):
                x = random.randint(1, self.map_width - 1)
                y = random.randint(1, self.map_height - 1)
                if dungeon.tiles[x, y] == tile_types.FLOOR \
                        and not any(e.x == x and e.y == y for e in dungeon.entities):
                    entity.copy_to(dungeon, x, y)

        player_place_tries = 99
        for _ in range(player_place_tries):
            x = random.randint(1, self.map_width - 1)
            y = random.randint(1, self.map_height - 1)
            if dungeon.tiles[x, y] == tile_types.FLOOR \
                    and not any(e.x == x and e.y == y for e in dungeon.entities):
                self.engine.player.place(x, y, dungeon)

        return dungeon

    def __flood_fill_test(self):
        max_tries = 99
        # Find a random open tile
        for _ in range(max_tries):
            start_x, start_y = (random.randint(0, self.map_width - 1), random.randint(0, self.map_height - 1))
            if self.internal_map[start_x, start_y] == 0:
                break
        else:
            raise OverflowError("Could not find open tile to start flood fill (max tries reached)")
        adjacencies = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        num_filled_tiles = 0
        q = deque()
        q.append((start_x, start_y))
        while q: # While queue is not empty
            next_x, next_y = q.pop()
            if not self.__out_of_bounds(next_x, next_y):
                if self.internal_map[next_x, next_y] == 0:
                    self.internal_map[next_x, next_y] = 2
                    num_filled_tiles += 1
                for i, j in adjacencies:
                    if not self.__out_of_bounds(next_x + i, next_y + j):
                        if self.internal_map[next_x + i, next_y + j] == 0:
                            self.internal_map[next_x + i, next_y + j] = 2
                            num_filled_tiles += 1
                            q.append((next_x + i, next_y + j))

        if num_filled_tiles / (self.map_width * self.map_height) >= 0.45:
            # Test passed, more than 45% of map is walkable
            return

    def __next_gen(self, logic_mode: int) -> np.ndarray:
        assert logic_mode == 0 or logic_mode == 1, "Logic mode for cellular automata not found."
        next_map: np.ndarray = np.zeros(
            (self.map_width, self.map_height),
            dtype=np.int8,
            order="F"
        )
        if logic_mode == 0:
            for x in range(self.map_width):
                for y in range(self.map_height):
                    next_map[x, y] = self.__place_wall_logic_primary(x, y)
        else:
            for x in range(self.map_width):
                for y in range(self.map_height):
                    next_map[x, y] = self.__place_wall_logic_secondary(x, y)

        return next_map

    def __random_fill(self) -> None:
        for x in range(self.map_width):
            for y in range(self.map_height):
                # Create a border on the edge of the map
                if x == 0 or y == 0 or x == self.map_width - 1 or y == self.map_height - 1:
                    self.internal_map[x, y] = 1

                else:
                    chance = random.randint(1, 100)
                    if chance <= self.percent_walls:
                        self.internal_map[x, y] = 1
                    else:
                        self.internal_map[x, y] = 0

    def __place_wall_logic_primary(self, x: int, y: int) -> int:
        """Handle the cellular automata logic for next generation"""
        adj_1_walls: int = self.__get_nearby_wall_count(x, y, 1, 1)
        adj_2_walls: int = self.__get_nearby_wall_count(x, y, 2, 2)

        if adj_1_walls >= 5 or adj_2_walls <= 2:
            return 1
        return 0

    def __place_wall_logic_secondary(self, x: int, y: int) -> int:
        adj_1_walls: int = self.__get_nearby_wall_count(x, y, 1, 1)

        if adj_1_walls >= 5:
            return 1
        return 0

    def __get_nearby_wall_count(self, x: int, y: int, scope_x: int, scope_y: int) -> int:
        start_x: int = x - scope_x
        start_y: int = y - scope_y
        end_x: int = x + scope_x
        end_y: int = y + scope_y

        wall_counter: int = 0

        for ix in range(start_x, end_x + 1):
            for iy in range(start_y, end_y + 1):
                if self.__is_wall(ix, iy):
                    wall_counter += 1

        return wall_counter

    def __is_wall(self, x: int, y: int):
        # Consider out of bounds a wall
        if self.__out_of_bounds(x, y):
            return True
        if self.internal_map[x, y] == 1:
            return True
        return False

    def __out_of_bounds(self, x: int, y: int):
        return not (0 <= x < self.map_width and 0 <= y < self.map_height)

    def __str__(self):
        string: str = " ".join([
            "Width:",
            str(self.map_width),
            "\tHeight:",
            str(self.map_height),
            "\t% Walls:",
            str(self.percent_walls),
            "\n"
        ])

        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.internal_map[x, y] == 0:
                    string += "."
                elif self.internal_map[x, y] == 1:
                    string += "#"
                elif self.internal_map[x, y] == 2:
                    string += "o"
            string += "\n"

        return string


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
