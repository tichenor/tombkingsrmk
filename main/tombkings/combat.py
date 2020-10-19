from __future__ import annotations

import random
from enum import Enum, auto
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from entity import Actor

BASE_MISS_CHANCE_MELEE = 8


class CombatResult(Enum):
    MISS = auto()
    HIT = auto()
    CRITICAL = auto()
    BLOCK = auto()


class Combat:
    class Melee:

        @staticmethod
        def attack(attacker: Actor, defender: Actor) -> Tuple[CombatResult, int]:
            """Simulate an attack and return the result together with any damage inflicted."""
            if not Combat.Melee._roll_to_hit(attacker, defender):
                return CombatResult.MISS, 0

            damage = Combat.Melee._roll_damage(attacker, defender)

            if Combat.Melee._roll_critical(attacker, defender):
                return CombatResult.CRITICAL, damage * 2

            return CombatResult.HIT, damage

        @staticmethod
        def _roll_to_hit(attacker: Actor, defender: Actor) -> bool:
            """
            Simulate a random boolean outcome based on the statistics of an attacker and a defender to
            determine if a melee attack is able to connect or not.
            """
            # The fighting and shielding skills as well as defense and evasion stats makes the defender harder to hit.
            defender_modifier = 0.50 * defender.skills.fighting \
                                + (0.33 + 0.03 * defender.skills.shielding) * defender.fighter.defense \
                                + defender.fighter.evasion
            # The fighting skill and the accuracy stat increase the attacker's chance to land a hit.
            attacker_modifier = attacker.skills.fighting + attacker.fighter.accuracy

            chance_to_miss = int(round(BASE_MISS_CHANCE_MELEE + defender_modifier - attacker_modifier))

            return random.randint(0, 100) > chance_to_miss

        @staticmethod
        def _roll_damage(attacker: Actor, defender: Actor) -> int:
            """
            Simulate a random outcome of damage inflicted for when an attacker lands a hit on a defender.
            """
            # Damage spread.
            spread = attacker.fighter.power // 3
            # Fighting skill affects total power.
            power = attacker.fighter.power * (0.80 + 0.05 * attacker.skills.fighting)
            # Do a raw damage roll.
            raw_damage = power + random.randint(-spread, spread)

            # If the attacker is significantly stronger than the defender or vice versa, armor has varying effectiveness.
            if random.randint(0, 20) + defender.skills.fighting > 2 * attacker.fighter.power:
                # Target is a strong defender.
                armor_reduction = 0.60 * defender.fighter.armor + 0.03 * defender.skills.shielding
            else:
                # The attacker is significantly stronger.
                armor_reduction = 0.35 * defender.fighter.armor + 0.03 * defender.skills.shielding

            # Damage equation.
            final_damage = int(round(raw_damage - armor_reduction))
            return final_damage

        @staticmethod
        def _roll_critical(attacker: Actor, defender: Actor) -> bool:
            return random.randint(0, 100) > 90
