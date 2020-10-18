from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

from overrides import overrides

from config import Config as cfg
import exceptions

if TYPE_CHECKING:
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

        damage = self._actor.fighter.power - target.fighter.defense
        attack_desc = f"{self._actor.name.capitalize()} attacks {target.name}"
        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.", cfg.Color.PLAYER_ATK
            )
            target.fighter.hp -= damage
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", cfg.Color.PLAYER_ATK
            )


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
        self._item.consumable.activate(self)


class DropItem(ItemAction):

    @overrides
    def perform(self) -> None:
        self._actor.inventory.drop(self._item)


class WaitAction(Action):

    @overrides
    def perform(self) -> None:
        pass