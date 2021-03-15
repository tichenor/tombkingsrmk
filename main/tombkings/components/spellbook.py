from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from components.spell import Spell
    from entity import Actor


class Spellbook(BaseComponent):

    parent: Actor

    def __init__(self, capacity: int):
        self._capacity = capacity
        self._spells: List[Spell] = []

    @property
    def spells(self) -> List[Spell]:
        return self._spells

    @property
    def capacity(self) -> int:
        return self._capacity