from __future__ import annotations

from typing import TYPE_CHECKING

from config import Config as cfg
from components.base_component import BaseComponent
from render_order import RenderOrder

if TYPE_CHECKING:
    from entity import Actor


class Fighter(BaseComponent):

    parent: Actor

    def __init__(self, hp: int, defense: int, power: int):

        self.max_hp = hp
        self._hp = hp
        self.defense = defense
        self.power = power

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))  # Constrain hp to be between 0 and max_hp
        if self._hp == 0 and self.parent.ai:
            self.on_death()

    def add_hp(self, amount: int) -> int:
        """Restore some health and return the actual amount restored."""
        if self.hp == self.max_hp:
            return 0

        new_hp = self._hp + amount
        if new_hp > self.max_hp:
            new_hp = self.max_hp

        recovered = new_hp - self.hp

        self.hp = new_hp

        return recovered

    def remove_hp(self, amount: int) -> None:
        self.hp -= amount


    def on_death(self) -> None:
        """Temporary death function."""
        if self.engine.player is self.parent:
            message = "You died!"
            message_color = cfg.Color.PLAYER_DIE
        else:
            message = f"{self.parent.name} is dead!"
            message_color = cfg.Color.ENEMY_DIE

        self.parent.char = "%"
        self.parent.color = (191, 0, 0)
        self.parent.blocks_movement = False
        self.parent.ai = None
        self.parent.name = f"remains of {self.parent.name}"
        self.parent.render_order = RenderOrder.CORPSE

        self.engine.message_log.add_message(message, message_color)


