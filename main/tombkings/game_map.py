from __future__ import annotations

from typing import Iterable, Iterator, Set, Optional, TYPE_CHECKING, Tuple

import numpy as np  # type: ignore
from tcod.console import Console

from entity import Actor, Item
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class GameMap:
    """Class managing data such as floors, walls, objects, what is visible, what is explored, and so on."""

    def __init__(self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()):

        self._engine = engine
        self._width = width
        self._height = height

        self._tiles = np.full((width, height), fill_value=tile_types.WALL, order="F")

        self._visible_tiles = np.full((width, height), fill_value=False, order="F")  # Tiles currently visible.
        self._explored_tiles = np.full((width, height), fill_value=False, order="F")  # Tiles previously seen.

        self._downstairs_location = (0, 0)

        self._entities = set(entities)

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def tiles(self) -> np.ndarray:
        return self._tiles

    @property
    def visible_tiles(self) -> np.ndarray:
        return self._visible_tiles

    @property
    def explored_tiles(self) -> np.ndarray:
        return self._explored_tiles

    @explored_tiles.setter
    def explored_tiles(self, value):
        self._explored_tiles = value

    @property
    def downstairs_location(self) -> Tuple[int, int]:
        return self._downstairs_location

    @downstairs_location.setter
    def downstairs_location(self, val: Tuple[int, int]) -> None:
        if not self.in_bounds(*val):
            raise ValueError(
                f"Coordinates {(val[0], val[1])} for `{self.downstairs_location.__name__}` are outside map boundaries")
        self._downstairs_location = val

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def entities(self) -> Set[Entity]:
        return self._entities

    @property
    def game_map(self) -> GameMap:
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """Iterate over this map's living actors."""
        yield from (
            entity for entity in self.entities if isinstance(entity, Actor) and entity.is_alive
        )

    @property
    def items(self) -> Iterator[Item]:
        """Iterate over this map's items."""
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def add_and_register_entity(self, entity: Entity):
        self._entities.add(entity)
        if isinstance(entity, Actor) and entity.ai and entity.energy:
            self.engine.ticker.schedule_turn(entity.energy.speed, entity)

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x,y-coordinates are inside the map bounds."""
        return 0 <= x < self._width and 0 <= y < self._height

    def render(self, console: Console) -> None:
        """
        Render the map and any entities visible to the player.
        If a tile is in the 'visible' array, then draw it with 'light' colors.
        If it is not in 'visible' but is in 'explored', draw it with 'dark' colors.
        Otherwise, the default is 'SHROUD'.
        """
        console.tiles_rgb[0:self._width, 0:self._height] = np.select(
            condlist=[self._visible_tiles, self._explored_tiles],
            choicelist=[self._tiles["light"], self._tiles["dark"]],
            default=tile_types.SHROUD,
        )

        # Render entities in the correct order
        entities_sorted = sorted(self._entities, key=lambda e: e.render_order.value)

        for entity in entities_sorted:
            if self._visible_tiles[entity.x, entity.y]:
                console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)

    def get_blocking_entity_at(self, pos_x: int, pos_y: int) -> Optional[Entity]:
        for entity in self._entities:
            if (
                    entity.blocks_movement
                    and entity.x == pos_x
                    and entity.y == pos_y
            ):
                return entity
        return None

    def get_actor_at(self, pos_x: int, pos_y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == pos_x and actor.y == pos_y:
                return actor

        return None


class GameWorld:
    """
    Holds the settings for the game map and generates new maps when moving down the stairs.
    """

    def __init__(
            self,
            *,
            engine: Engine,
            map_width: int,
            map_height: int,
            max_rooms: int,
            room_min_size: int,
            room_max_size: int,
            current_floor: int = 0,
    ):
        self._engine = engine
        self._map_width = map_width
        self._map_height = map_height

        self._max_rooms = max_rooms
        self._room_min_size = room_min_size
        self._room_max_size = room_max_size

        self._current_floor = current_floor

    @property
    def current_floor(self) -> int:
        return self._current_floor

    def generate_floor(self) -> None:
        from generation import BasicRectangular, CellularAutomata
        self._current_floor += 1

        if self.current_floor >= 3:
            test_gen = CellularAutomata(self._map_width, self._map_height, self._engine, percent_walls=40)
            self._engine.game_map = test_gen.generate_map()

        map_generator = BasicRectangular(self._room_min_size,
                                         self._room_max_size,
                                         self._map_width,
                                         self._map_height,
                                         self._max_rooms,
                                         self._engine)
        self._engine.game_map = map_generator.generate_map()
