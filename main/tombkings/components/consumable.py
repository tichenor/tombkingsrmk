from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from overrides import overrides

import actions
import components.ai
import components.inventory
from components.base_component import BaseComponent
from config import Config as cfg
from exceptions import Impossible
from input_handlers import (
    ActionOrHandler,
    AreaRangedTargetingHandler,
    SingleRangedTargetingHandler,
)

if TYPE_CHECKING:
    from entity import Actor, Item


class Consumable(BaseComponent):

    parent: Item

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        """Try to return the action for this item."""
        return actions.ItemAction(consumer, self.parent)

    def activate(self, action: actions.ItemAction) -> None:
        """
        Invoke this item's ability.
        :param action: The context for this activation.
        """
        raise NotImplementedError()

    def consume(self) -> None:
        """Remove the item from its containing inventory."""
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory):
            inventory.items.remove(entity)


class HealingConsumable(Consumable):

    def __init__(self, amount: int):
        self._amount = amount

    @overrides
    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.actor
        amount_recovered = consumer.fighter.add_hp(self._amount)

        if amount_recovered > 0:
            self.engine.message_log.add_message(
                f"You consume the {self.parent.name} and recover {amount_recovered} hit points.",
                cfg.Color.HEALTH_RECOVERED,
            )
            self.consume()
        else:
            raise Impossible(f"You are already at full health.")


class ScrollLightningBolt(Consumable):

    def __init__(self, damage: int, max_range: int):
        self._damage = damage
        self._max_range = max_range

    @overrides
    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.actor
        target = None
        closest_dist = self._max_range + 1

        for actor in self.engine.game_map.actors:
            if actor is not consumer and self.parent.game_map.visible_tiles[actor.x, actor.y]:
                dist = consumer.distance_to(actor.x, actor.y)
                if dist < closest_dist:
                    target = actor
                    closest_dist = dist

        if target:
            self.engine.message_log.add_message(
                f"A bolt of lightning strikes the {target.name} with a loud thunder, dealing {self._damage} damage."
            )
            target.fighter.remove_hp(self._damage)
            self.consume()
        else:
            raise Impossible("No enemy is close enough to strike.")


class ScrollConfusion(Consumable):

    def __init__(self, num_turns: int):
        self._num_turns = num_turns

    @overrides
    def get_action(self, consumer: Actor) -> SingleRangedTargetingHandler:
        """Ask the player to select a target location by switching the event handler. The callback is
        executing an item action at the selected location using the consumer and the parent (the item this
        component belongs to)."""
        self.engine.message_log.add_message(
            "Select a target location.", cfg.Color.NEEDS_TARGET
        )
        return SingleRangedTargetingHandler(
            self.engine,
            callback=lambda position: actions.ItemAction(consumer, self.parent, position),
        )

    @overrides
    def activate(self, action: actions.ItemAction) -> None:
        consumer = action.actor
        target = action.target_actor

        if not self.engine.game_map.visible_tiles[action.destination]:
            raise Impossible("You cannot target an area that you cannot see.")
        if not target:
            raise Impossible("You must select an enemy to target.")
        if target is consumer:
            raise Impossible("Why would you want to do that?")

        self.engine.message_log.add_message(
            f"They eyes of the {target.name} look vacant as they start to stumble around.",
            cfg.Color.STATUS_EFFECT_APPLIED,
        )
        target.ai = components.ai.ConfusedAI(
            entity=target, previous_ai=target.ai, turns_remaining=self._num_turns,
        )
        self.consume()


class ScrollFireball(Consumable):

    def __init__(self, damage: int, radius: int):
        self._damage = damage
        self._radius = radius

    @overrides
    def get_action(self, consumer: Actor) -> AreaRangedTargetingHandler:
        self.engine.message_log.add_message(
            "Select a target location.", cfg.Color.NEEDS_TARGET
        )
        return AreaRangedTargetingHandler(
            self.engine,
            radius=self._radius,
            callback=lambda position: actions.ItemAction(consumer, self.parent, position)
        )

    @overrides
    def activate(self, action: actions.ItemAction) -> None:
        target_position = action.destination
        if not self.engine.game_map.visible_tiles[target_position]:
            raise Impossible("You cannot target an area that you cannot see.")

        any_hit = False
        for actor in self.engine.game_map.actors:
            if actor.distance_to(*target_position) <= self._radius:
                self.engine.message_log.add_message(
                    f"The {actor.name} is engulfed in a firey explosion, taking {self._damage} damage."
                )
                actor.fighter.remove_hp(self._damage)
                any_hit = True

        if not any_hit:
            raise Impossible("There are no targets in the radius.")
        self.consume()







