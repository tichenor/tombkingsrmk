from __future__ import annotations

import random
from typing import TYPE_CHECKING

from config import Config as cfg
from components.base_component import BaseComponent
from render_order import RenderOrder

if TYPE_CHECKING:
    from entity import Actor


class Fighter(BaseComponent):

    parent: Actor

    def __init__(
            self,
            hp: int = 10,
            defense: int = 0,
            power: int = 0,
            armor: int = 0,
            accuracy: int = 0,
            evasion: int = 0,
    ):

        self._max_hp = hp
        self._hp = hp
        self._base_defense = defense
        self._base_power = power
        self._base_armor = armor
        self._base_accuracy = accuracy
        self._base_evasion = evasion

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self._max_hp))  # Constrain hp to be between 0 and max_hp
        if self._hp == 0 and self.parent.ai:
            self.on_death()

    @property
    def defense(self) -> int:
        return self._base_defense + self._bonus_defense

    @property
    def power(self) -> int:
        return self._base_power + self._bonus_power

    @property
    def armor(self) -> int:
        return self._base_armor + self._bonus_armor

    @property
    def accuracy(self) -> int:
        return self._base_accuracy + self._bonus_accuracy

    @property
    def evasion(self) -> int:
        return self._base_evasion + self._bonus_evasion

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def _bonus_defense(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.bonus_defense
        return 0

    @property
    def _bonus_power(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.bonus_power
        return 0

    @property
    def _bonus_armor(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.bonus_armor

    @property
    def _bonus_accuracy(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.bonus_accuracy

    @property
    def _bonus_evasion(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.bonus_evasion

    def modify_max_hp(self, val: int) -> None:
        if self._max_hp + val <= 0:
            raise ValueError(f"Maximum hit points of {self.parent.name} must be at least 1.")
        self._max_hp += val
        self._hp += val

    def increase_base_power(self, val: int) -> None:
        self._base_power += val

    def increase_base_defense(self, val: int) -> None:
        self._base_defense += val

    def add_hp(self, amount: int) -> int:
        """Restore some health and return the actual amount restored."""
        if self._hp == self._max_hp:
            return 0

        new_hp = self._hp + amount
        if new_hp > self._max_hp:
            new_hp = self._max_hp

        recovered = new_hp - self._hp

        self._hp = new_hp

        return recovered

    def remove_hp(self, amount: int) -> None:
        self.hp -= amount

    def on_death(self) -> None:
        """Temporary death function."""
        if self.engine.player is self.parent:
            message = "You died!"
            message_color = cfg.Color.PLAYER_DIE
        else:
            message = random.choice(
                [
                    f"The {self.parent.name} falls lifeless to the floor.",
                    f"The {self.parent.name} dies.",
                    f"The {self.parent.name} is executed!",
                    f"The {self.parent.name} is no more.",
                    f"The {self.parent.name} is obliterated!",
                    f"The {self.parent.name} got destroyed!",
                    f"The eyes of the {self.parent.name} go blank as it collapes on the ground."
                ]
            )
            message_color = cfg.Color.ENEMY_DIE

        self.parent.char = "%"
        self.parent.color = (191, 0, 0)
        self.parent.blocks_movement = False
        self.parent.ai = None
        self.parent.name = f"remains of {self.parent.name}"
        self.parent.render_order = RenderOrder.CORPSE

        self.engine.player.level.add_experience(self.parent.level.experience_given)
        self.engine.message_log.add_message(message, message_color)


