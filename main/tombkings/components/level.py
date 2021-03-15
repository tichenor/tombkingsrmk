from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


class Level(BaseComponent):

    parent: Actor

    def __init__(
            self,
            current_level: int = 1,
            current_xp: int = 0,
            level_up_base: int = 0,
            level_up_factor: int = 150,
            xp_given: int = 0,
    ):

        self._current_level = current_level
        self._current_xp = current_xp
        self._level_up_base = level_up_base
        self._level_up_factor = level_up_factor
        self._xp_given = xp_given

    @property
    def experience_to_next_level(self) -> int:
        """The formula for calculating when to level up."""
        return self._level_up_base + self._current_level * self._level_up_factor

    @property
    def requires_level_up(self) -> bool:
        """Return True if the actor have enough experience to level up."""
        return self._current_xp >= self.experience_to_next_level

    @property
    def experience_given(self) -> int:
        """The amount of experience this actor is worth."""
        return self._xp_given

    @property
    def current_level(self) -> int:
        return self._current_level

    @property
    def current_experience(self) -> int:
        return self._current_xp

    def add_experience(self, xp: int) -> None:
        if xp == 0 or self._level_up_base == 0:
            return
        self._current_xp += xp

        if self.requires_level_up:
            self.engine.message_log.add_message(
                f"You feel more experienced."
            )

    def increase_level(self) -> None:
        self._current_xp -= self.experience_to_next_level
        self._current_level += 1