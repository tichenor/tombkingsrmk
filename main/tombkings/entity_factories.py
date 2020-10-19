from components import consumable
from components.ai import BaseAI, HostileAI
from components import consumable
from components.equipment import Equipment
from components.equippable import Equippable
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from components.skills import Skills
from entity import Actor, Item
from equipment_slots import EquipmentSlot


class EntityFactory:
    """Contains prefabricated instances of each entity (actor, item, etc.) that can be copied into the game."""

    """
    Monsters.
    """

    player = Actor(
        char="@",
        color=(255, 255, 255),
        name="Player",
        ai_cls=BaseAI,
        fighter=Fighter(hp=30, defense=2, power=5),
        inventory=Inventory(capacity=26),
        equipment=Equipment(),
        skills=Skills(),
        level=Level(level_up_base=200),
    )

    enemy_orc = Actor(
        char="o",
        color=(63, 127, 63),
        name="orc",
        ai_cls=HostileAI,
        fighter=Fighter(hp=10, defense=0, power=3),
        inventory=Inventory(capacity=0),
        equipment=Equipment(),
        skills=Skills(),
        level=Level(xp_given=35)
    )

    enemy_troll = Actor(
        char="T",
        color=(0, 127, 0),
        name="troll",
        ai_cls=HostileAI,
        fighter=Fighter(hp=16, defense=1, power=4),
        inventory=Inventory(capacity=0),
        equipment=Equipment(),
        skills=Skills(),
        level=Level(xp_given=100),
    )

    """
    Items.
    """

    potion_health = Item(
        char="!",
        color=(127, 0, 255),
        name="health potion",
        consumable=consumable.HealingConsumable(amount=10)
    )

    scroll_lightning = Item(
        char="~",
        color=(255, 255, 0),
        name="scroll of lightning",
        consumable=consumable.ScrollLightningBolt(damage=20, max_range=5)
    )

    scroll_confuse = Item(
        char="~",
        color=(207, 63, 255),
        name="scroll of confusion",
        consumable=consumable.ScrollConfusion(num_turns=10),
    )

    scroll_fireball = Item(
        char="~",
        color=(255, 0, 0),
        name="scroll of fireball",
        consumable=consumable.ScrollFireball(damage=12, radius=3)
    )

    weapon_dagger = Item(
        char="/",
        color=(0, 191, 255),
        name="dagger",
        equippable=Equippable(slot=EquipmentSlot.WEAPON, bonus_power=1)
    )

    armor_leather = Item(
        char="[",
        color=(139, 69, 19),
        name="leather armor",
        equippable=Equippable(slot=EquipmentSlot.BODY_ARMOR, bonus_defense=1)
    )
