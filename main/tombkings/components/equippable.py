from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_slots import EquipmentSlot

if TYPE_CHECKING:
    from entity import Item


class Equippable(BaseComponent):

    parent: Item

    def __init__(
            self,
            slot: EquipmentSlot,
            bonus_power: int = 0,
            bonus_defense: int = 0,
            bonus_armor: int = 0,
            bonus_accuracy: int = 0,
            bonus_evasion: int = 0,
            bonus_skill_fighting: int = 0,
            bonus_skill_shielding: int = 0,
            bonus_skill_conjuring: int = 0,
            bonus_skill_archery: int = 0,
    ):
        self._slot = slot

        self._bonus_power = bonus_power
        self._bonus_defense = bonus_defense
        self._bonus_armor = bonus_armor
        self._bonus_accuracy = bonus_accuracy
        self._bonus_evasion = bonus_evasion

        self._bonus_skill_fighting = bonus_skill_fighting
        self._bonus_skill_shielding = bonus_skill_shielding
        self._bonus_skill_conjuring = bonus_skill_conjuring
        self._bonus_skill_archery = bonus_skill_archery

    @property
    def slot(self) -> EquipmentSlot:
        return self._slot

    @property
    def bonus_power(self) -> int:
        return self._bonus_power

    @property
    def bonus_defense(self) -> int:
        return self._bonus_defense

    @property
    def bonus_armor(self) -> int:
        return self._bonus_armor

    @property
    def bonus_accuracy(self) -> int:
        return self._bonus_accuracy

    @property
    def bonus_evasion(self) -> int:
        return self._bonus_evasion

    @property
    def bonus_skill_fighting(self) -> int:
        return self._bonus_skill_fighting

    @property
    def bonus_skill_shielding(self) -> int:
        return self._bonus_skill_shielding

    @property
    def bonus_skill_conjuring(self) -> int:
        return self._bonus_skill_conjuring

    @property
    def bonus_skill_archery(self) -> int:
        return self._bonus_skill_archery
