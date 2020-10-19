from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Tuple, Dict

from components.base_component import BaseComponent
from equipment_slots import EquipmentSlot
from exceptions import Impossible

if TYPE_CHECKING:
    from entity import Actor, Item


class Equipment(BaseComponent):

    parent: Actor

    def __init__(
            self,
            *items: Tuple[EquipmentSlot, Item]
    ):
        # Initialize an empty dictionary of possible slots.
        self._equipped_items: Dict[EquipmentSlot, Optional[Item]] = {
            slot: None for slot in EquipmentSlot
        }
        # Populate it with any arguments provided in the constructor.
        for slot, item in items:
            self._equipped_items[slot] = item

    @property
    def bonus_defense(self) -> int:
        bonus = 0
        for slot in EquipmentSlot:
            if self._is_something_equipped(slot):
                bonus += self._equipped_items[slot].equippable.bonus_defense
        return bonus

    @property
    def bonus_power(self) -> int:
        bonus = 0
        for slot in EquipmentSlot:
            if self._is_something_equipped(slot):
                bonus += self._equipped_items[slot].equippable.bonus_power
        return bonus

    @property
    def bonus_armor(self) -> int:
        bonus = 0
        for slot in EquipmentSlot:
            if self._is_something_equipped(slot):
                bonus += self._equipped_items[slot].equippable.bonus_armor
        return bonus

    @property
    def bonus_accuracy(self) -> int:
        bonus = 0
        for slot in EquipmentSlot:
            if self._is_something_equipped(slot):
                bonus += self._equipped_items[slot].equippable.bonus_accuracy
        return bonus

    @property
    def bonus_evasion(self) -> int:
        bonus = 0
        for slot in EquipmentSlot:
            if self._is_something_equipped(slot):
                bonus += self._equipped_items[slot].equippable.bonus_evasion
        return bonus

    @property
    def bonus_skill_fighting(self) -> int:
        bonus = 0
        for slot in EquipmentSlot:
            if self._is_something_equipped(slot):
                bonus += self._equipped_items[slot].equippable.bonus_skill_fighting
        return bonus

    @property
    def bonus_skill_shielding(self) -> int:
        bonus = 0
        for slot in EquipmentSlot:
            if self._is_something_equipped(slot):
                bonus += self._equipped_items[slot].equippable.bonus_skill_shielding
        return bonus

    @property
    def bonus_skill_conjuring(self) -> int:
        bonus = 0
        for slot in EquipmentSlot:
            if self._is_something_equipped(slot):
                bonus += self._equipped_items[slot].equippable.bonus_skill_conjuring
        return bonus

    @property
    def bonus_skill_archery(self) -> int:
        bonus = 0
        for slot in EquipmentSlot:
            if self._is_something_equipped(slot):
                bonus += self._equipped_items[slot].equippable.bonus_skill_archery
        return bonus

    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        if equippable_item.equippable is None:
            raise Impossible("You cannot equip this item.")
        slot = equippable_item.equippable.slot
        if self._equipped_items[slot] == equippable_item:
            self._unequip_item_from_slot(slot, add_message)
        else:
            self._equip_item(equippable_item, add_message)

    def is_item_equipped(self, item: Item) -> bool:
        if item is not None:
            for equipment in self._equipped_items.values():
                if item == equipment:
                    return True
        return False

    def _equip_item(self, item: Item, add_message: bool) -> None:
        """Try to equip an `item` into the slot given by its `equippable` component."""
        if item.equippable is None:
            # Item must have an equippable component.
            raise Impossible("You cannot equip this item.")
        slot = item.equippable.slot
        currently_equipped_item = self._equipped_items[slot]
        if currently_equipped_item is not None:
            # Unequip any currently worn item before equipping a new item.
            self._unequip_item_from_slot(slot, add_message)
        self._equipped_items[slot] = item
        if add_message:
            self._equip_message(item.name)

    def _unequip_item_from_slot(self, slot: EquipmentSlot, add_message: bool) -> None:
        """Remove any item currently equipped in the specified `slot`."""
        currently_equipped_item = self._equipped_items[slot]
        if currently_equipped_item is None:
            raise Impossible("Cannot unequip an item that is not equipped.")
        if add_message:
            self._unequip_message(currently_equipped_item.name)
        self._equipped_items[slot] = None

    def _is_something_equipped(self, slot: EquipmentSlot) -> bool:
        """Return True if a slot is equipped with an item that have an `Equippable` component."""
        item = self._equipped_items[slot]
        return item is not None and item.equippable is not None

    def _equip_message(self, item_name: str) -> None:
        self.parent.game_map.engine.message_log.add_message(
            f"You equip the {item_name}."
        )

    def _unequip_message(self, item_name: str) -> None:
        self.parent.game_map.engine.message_log.add_message(
            f"You remove the {item_name}."
        )

