from __future__ import annotations

import copy
import math
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union

from components.energy import Energy
from components.equipment import Equipment
from components.equippable import Equippable
from components.skills import Skills
from render_order import RenderOrder

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.fighter import Fighter
    from components.consumable import Consumable
    from components.inventory import Inventory
    from components.level import Level
    from game_map import GameMap

T = TypeVar("T", bound="Entity")


class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """

    # A parent (owner) of an entity can be either a game map (e.g. monsters and the player belong the the map) or
    # an inventory (e.g. for items stored in an inventory).
    parent: Union[GameMap, Inventory]

    def __init__(
            self,
            parent: Optional[GameMap, Inventory] = None,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<unnamed entity>",
            blocks_movement: bool = False,
            render_order: RenderOrder = RenderOrder.CORPSE
    ):
        self._x = x
        self._y = y
        self._char = char
        self._color = color
        self._name = name
        self._blocks_movement = blocks_movement
        self._render_order = render_order

        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent
            parent.entities.add(self)

    def copy_to(self: T, game_map: GameMap, x: int, y: int) -> T:
        """Make a copy ('spawn') of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = game_map
        game_map.add_and_register_entity(clone)
        return clone

    def place(self, x: int, y: int, game_map: Optional[GameMap] = None) -> None:
        """Place this entity at a new location. Handles moving across GameMaps."""
        self.x = x
        self.y = y
        if game_map:
            if hasattr(self, "parent"):  # Possibly not initialized.
                if self.parent is self.game_map:
                    self.game_map.entities.remove(self)

            self.parent = game_map
            game_map.entities.add(self)

    def move(self, dx: int, dy: int) -> None:
        self._x += dx
        self._y += dy

    def distance_to(self, x: int, y: int) -> float:
        """Return the distance between this entity and the specified x,y-coordinate."""
        return math.sqrt((x - self._x) ** 2 + (y - self._y) ** 2)

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, val: int) -> None:
        self._x = val

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, val: int) -> None:
        self._y = val

    @property
    def char(self) -> str:
        return self._char

    @char.setter
    def char(self, val: str) -> None:
        if len(val) != 1:
            raise ValueError("Entity `char` attribute must be a single character.")
        self._char = val

    @property
    def color(self) -> Tuple[int, int, int]:
        return self._color

    @color.setter
    def color(self, val: Tuple[int, int, int]) -> None:
        if any(i < 0 or i > 255 for i in val):
            raise ValueError("Entity `color` attribute must be tuple of three integers between 0 and 255.")
        self._color = val

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        self._name = val

    @property
    def blocks_movement(self) -> bool:
        return self._blocks_movement

    @blocks_movement.setter
    def blocks_movement(self, value: bool) -> None:
        self._blocks_movement = value

    @property
    def render_order(self) -> RenderOrder:
        return self._render_order

    @render_order.setter
    def render_order(self, val: RenderOrder) -> None:
        self._render_order = val

    @property
    def game_map(self) -> GameMap:
        return self.parent.game_map


class Actor(Entity):

    ticker: Ticker

    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<unnamed actor>",
            ai_cls: Type[BaseAI],
            fighter: Fighter,
            inventory: Inventory,
            equipment: Equipment,
            skills: Skills,
            level: Level,
            energy: Energy,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
        )

        self.ai: Optional[BaseAI] = ai_cls(self)

        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

        self.equipment = equipment
        self.equipment.parent = self

        self.skills = skills
        self.skills.parent = self

        self.level = level
        self.level.parent = self

        self.energy = energy
        self.energy.parent = self

    @property
    def is_alive(self) -> bool:
        """Return True as long as this actor can perform actions."""
        return bool(self.ai)


class Item(Entity):

    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<unnamed item>",
            consumable: Optional[Consumable] = None,
            equippable: Optional[Equippable] = None,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement = False,
            render_order=RenderOrder.ITEM
        )

        self.consumable = consumable
        if self.consumable:
            self.consumable.parent = self

        self.equippable = equippable
        if self.equippable:
            self.equippable.parent = self
