from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity import Actor


class Energy:
    """This class represents a time system component that allows any actor with this component to
    take turns performing actions. Actions cost energy, and energy is gained each tick."""

    parent: Actor

    def __init__(self, speed: int = 10):
        self._speed = speed

    @property
    def speed(self):
        """Return the speed of an actor used when scheduling its next turn. Currently there is some slight
        randomness to it."""
        speed_mod = 0
        if random.uniform(0, 1) < 0.5:
            speed_mod = random.randint(-1, 1)
        return self._speed + speed_mod


