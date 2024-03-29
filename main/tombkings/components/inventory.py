from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item


class Inventory(BaseComponent):

    parent: Actor

    def __init__(self, capacity: int):
        self._capacity = capacity
        self._items: List[Item] = []

    def drop(self, item: Item) -> None:
        """Remove an item from the inventory and restore it to the game map at the actor's current location."""
        self._items.remove(item)
        item.place(self.parent.x, self.parent.y, self.game_map)
        self.engine.message_log.add_message(f"You dropped the {item.name}.")

    @property
    def items(self) -> List[Item]:
        return self._items

    @property
    def capacity(self) -> int:
        return self._capacity