from __future__ import annotations

import random
from typing import List, Tuple, TYPE_CHECKING, Optional

import numpy as np  # type: ignore
import tcod
from overrides import overrides

from actions import Action, MeleeAction, MovementAction, WaitAction, BumpAction

if TYPE_CHECKING:
    from entity import Actor


class BaseAI(Action):

    def perform(self) -> None:
        raise NotImplementedError()

    def _get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """Compute and return a path to the target position. If there is no valid path, return an empty list."""
        # Copy the walkable array from the game map.
        cost = np.array(self._actor.game_map.tiles["walkable"], dtype=np.int8)

        for entity in self._actor.game_map.entities:
            # Check that an entity blocks movement and the cost isn't zero (blocking).
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will crowd behind each other in hallways. A higher number
                # means enemies will take longer paths in order to surround the player.
                cost[entity.x, entity.y] += 10

        # Create a graph from the cost array and pass it to a new pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self._actor.x, self._actor.y))  # Starting position.

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]


class HostileAI(BaseAI):

    """
    Basic bread-and-butter hostile AI class. If the actor of this AI is in the players FOV, it attempts to
    move towards the player or attack if close enough. It remembers the last position it saw the player in
    using the 'examine_location' parameter, which it moves towards if it exists and is not in the players FOV.
    This parameter can be set for other purposes if the AI should investigate a location.
    """

    def __init__(self, actor: Actor):
        super().__init__(actor)
        self.path: List[Tuple[int, int]] = []
        self.examine_location: Tuple[int, int] = None

    @overrides
    def perform(self) -> None:

        target = self.engine.player
        dx = target.x - self._actor.x
        dy = target.y - self._actor.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        if self.engine.game_map.visible_tiles[self._actor.x, self._actor.y]:
            self.examine_location = target.x, target.y
            if distance <= 1:
                return MeleeAction(self._actor, dx, dy).perform()

            self.path = self._get_path_to(target.x, target.y)

        elif self.examine_location:
            examine_x, examine_y = self.examine_location

            if (self._actor.x, self._actor.y) == (examine_x, examine_y):
                self.examine_location = None

            else:
                self.path = self._get_path_to(examine_x, examine_y)

        if self.path:

            dest_x, dest_y = self.path.pop(0)
            return MovementAction(self._actor, dest_x - self._actor.x, dest_y - self._actor.y).perform()

        return WaitAction(self._actor).perform()


class ConfusedAI(BaseAI):
    """
    A confused actor will stumble around aimlessly for a given number of turns before returning to its previous AI.
    If an actor occupies a tile it is randomly moving into, it will attempt to attack them.
    """

    def __init__(self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int):
        super().__init__(entity)
        self._previous_ai = previous_ai
        self._turns_remaining = turns_remaining

    @overrides
    def perform(self) -> None:
        """Revert the AI back to the original state if the effect has run its course."""
        if self._turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"The {self.actor.name} seems to come to their senses."
            )
            self._actor.ai = self._previous_ai
        else:
            # Pick a random direction
            dx, dy = random.choice(
                [
                    (-1, -1),  # north west
                    (0, -1),  # north
                    (1, -1),  # north east
                    (-1, 0),  # west
                    (1, 0),  # east
                    (-1, 1),  # south west
                    (0, 1),  # south
                    (1, 1),  # south east
                ]
            )

            self._turns_remaining -= 1
            return BumpAction(self.actor, dx, dy).perform()
