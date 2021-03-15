from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from overrides import overrides

import actions
from config import Config as cfg
from components.base_component import BaseComponent
from exceptions import Impossible
from input_handlers import ActionOrHandler

if TYPE_CHECKING:
    from entity import Actor


class Spell(BaseComponent):

    parent: Actor

    def __init__(self, name: str):
        self._name = name

    def get_action(self) -> Optional[ActionOrHandler]:
        """Try to return the action for this spell."""
        return actions.SpellAction(self.parent, self)

    def invoke(self, action: actions.SpellAction) -> None:
        raise NotImplementedError()

    @property
    def name(self) -> str:
        return self._name


class HealingSpell(Spell):

    def __init__(self, name: str, amount: int):
        super().__init__(name)
        self._amount = amount

    @overrides
    def invoke(self, action: actions.SpellAction) -> None:
        caster = action.actor
        amount_recovered = caster.fighter.add_hp(self._amount)

        if amount_recovered > 0:
            self.engine.message_log.add_message(
                f"You consume the {self.parent.name} and recover {amount_recovered} hit points.",
                cfg.Color.HEALTH_RECOVERED,
            )
            return
        raise Impossible(f"You are already at full health.")