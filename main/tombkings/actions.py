from __future__ import annotations

import random
from typing import Optional, Tuple, TYPE_CHECKING

from overrides import overrides

from config import Config as cfg
from combat import Combat, CombatResult
import exceptions

if TYPE_CHECKING:
    from components.spell import Spell
    from engine import Engine
    from entity import Entity, Actor, Item


class Action:

    def __init__(self, actor: Actor) -> None:
        super().__init__()
        self._actor = actor

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to."""
        return self._actor.game_map.engine

    def perform(self) -> None:
        """
        Perform this action with the objects needed to determine its scope.
        `self.engine` is the scope this action is being performed in.
        `self.actor` is the object performing the action.
        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()

    @property
    def actor(self):
        return self._actor


class DirectionalAction(Action):
    """Superclass for any action performed with a direction, such as moving or attacking something next to you."""
    def __init__(self, actor: Actor, dx: int, dy: int):
        super().__init__(actor)

        self.dx = dx
        self.dy = dy

    @property
    def destination(self) -> Tuple[int, int]:
        """Returns this action's destination."""
        return self._actor.x + self.dx, self._actor.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this action's destination (if any)."""
        return self.engine.game_map.get_blocking_entity_at(*self.destination)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this action's destination."""
        return self.engine.game_map.get_actor_at(*self.destination)

    @overrides
    def perform(self) -> None:
        raise NotImplementedError()


class MovementAction(DirectionalAction):

    @overrides
    def perform(self) -> None:

        dest_x, dest_y = self.destination

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at(dest_x, dest_y):
            # Destination is blocked by an entity.
            raise exceptions.Impossible("That way is blocked.")

        self._actor.move(self.dx, self.dy)


class BumpAction(DirectionalAction):

    @overrides
    def perform(self) -> None:

        if self.target_actor:
            return MeleeAction(self._actor, self.dx, self.dy).perform()
        else:
            return MovementAction(self._actor, self.dx, self.dy).perform()


class MeleeAction(DirectionalAction):

    @overrides
    def perform(self) -> None:

        target = self.target_actor

        if not target:
            raise exceptions.Impossible("There is nothing to attack.")

        result, damage = Combat.Melee.attack(self._actor, self.target_actor)
        description = f"{self._actor.name} attacks the {target.name}"

        if result == CombatResult.MISS:
            description = f"{description} but it misses."

        elif damage == 0:
            description = f"{description} but does no damage."

        elif result == CombatResult.HIT:
            description = f"{description} for {damage} hit points."

        elif result == CombatResult.CRITICAL:
            verb: str = random.choice(
                [
                    "*slices*",
                    "*whacks*",
                    "*carves*",
                    "*crushes*",
                    "*mangles*",
                ]
            )
            tail = "".join("!" for _ in range(random.randint(2, 5)))
            description = f"{self._actor.name} {verb} the {target.name} for {damage} hit points{tail}"

        if self._actor == self.engine.player:
            color = cfg.Color.PLAYER_ATK
        else:
            color = cfg.Color.ENEMY_ATK

        self.engine.message_log.add_message(
            description, color
        )

        target.fighter.remove_hp(damage)


class PickupAction(Action):
    """Pick up an item and add it to the inventory, if there is room for it."""
    def __init__(self, actor: Actor):
        super().__init__(actor)

    @overrides
    def perform(self) -> None:
        actor_pos_x, actor_pos_y = self._actor.x, self._actor.y
        inventory = self._actor.inventory

        for item in self.engine.game_map.items:
            if actor_pos_x == item.x and actor_pos_y == item.y:

                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.")

                self.engine.game_map.entities.remove(item)
                item.parent = self._actor.inventory
                inventory.items.append(item)

                self.engine.message_log.add_message(f"You pick up the {item.name}.")
                return

        raise exceptions.Impossible("There is nothing here to pick up.")


class EquipAction(Action):

    def __init__(self, actor: Actor, item: Item):
        super().__init__(actor)
        self.item = item

    @overrides
    def perform(self) -> None:
        self._actor.equipment.toggle_equip(self.item)


class ItemAction(Action):

    def __init__(self, actor: Actor, item: Item, target_position: Optional[int, int] = None):
        super().__init__(actor)
        self._item = item
        if not target_position:
            target_position = actor.x, actor.y
        self._target_position = target_position

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this action's target position."""
        return self.engine.game_map.get_actor_at(*self._target_position)

    @property
    def destination(self) -> Tuple[int, int]:
        """Return the coordinates for this action's destination."""
        return self._target_position

    @overrides
    def perform(self) -> None:
        """Invoke the item's ability. This action will be passed in the method to provide context."""
        if self._item.consumable:
            self._item.consumable.activate(self)


class SpellAction(Action):

    def __init__(self, actor: Actor, spell: Spell, target_position: Optional[int, int] = None):
        super().__init__(actor)
        self._spell = spell
        if not target_position:
            target_position = actor.x, actor.y
        self._target_position = target_position

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this action's target position."""
        return self.engine.game_map.get_actor_at(*self._target_position)

    @property
    def destination(self) -> Tuple[int, int]:
        """Return the coordinates for this action's destination."""
        return self._target_position

    @overrides
    def perform(self) -> None:
        """Invoke this action's spell effect. This action will be passed in the method to provide context."""
        self._spell.invoke(self)


class DropItem(ItemAction):

    @overrides
    def perform(self) -> None:
        """If the actor drops an equipped item, de-equip it before dropping it."""
        if self._actor.equipment.is_item_equipped(self._item):
            self._actor.equipment.toggle_equip(self._item)
        self._actor.inventory.drop(self._item)


class StairsAction(Action):

    @overrides
    def perform(self) -> None:
        """Take the stairs if any exist at the actor's location."""
        if (self._actor.x, self._actor.y) == self.engine.game_map.downstairs_location:
            self.engine.game_world.generate_floor()
            self.engine.message_log.add_message(
                "You descend the staircase.", cfg.Color.DESCEND
            )
        else:
            raise exceptions.Impossible("There are no stairs here.")


class WaitAction(Action):

    @overrides
    def perform(self) -> None:
        pass