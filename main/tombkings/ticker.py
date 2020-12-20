from typing import List, Dict

from entity import Actor


class Ticker:
    """Simple time scheduling system."""

    def __init__(self):
        self._ticks = 0
        self._schedule: Dict[int, List[Actor]] = {}

    def schedule_turn(self, interval, actor: Actor):
        self._schedule.setdefault(self._ticks + interval, []).append(actor)

    def next_turn(self):
        return self._schedule.pop(self._ticks, [])

    @property
    def ticks(self):
        return self._ticks

    @ticks.setter
    def ticks(self, value):
        self._ticks = value
