from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


class Skills(BaseComponent):

    parent: Actor

    def __init__(
            self,
            fighting: int = 0,
            shielding: int = 0,
            conjuring: int = 0,
            archery: int = 0,
    ):
        self._base_fighting = fighting
        self._base_shielding = shielding
        self._base_conjuring = conjuring
        self._base_archery = archery

    @property
    def fighting(self) -> int:
        return self._base_fighting + self._bonus_fighting

    @property
    def shielding(self) -> int:
        return self._base_shielding + self._bonus_shielding

    @property
    def conjuring(self) -> int:
        return self._base_conjuring + self._bonus_conjuring

    @property
    def archery(self) -> int:
        return self._base_archery + self._bonus_archery

    @property
    def _bonus_fighting(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.bonus_skill_fighting

    @property
    def _bonus_shielding(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.bonus_skill_shielding

    @property
    def _bonus_conjuring(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.bonus_skill_conjuring

    @property
    def _bonus_archery(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.bonus_skill_archery