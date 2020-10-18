from components import consumable
from components.ai import BaseAI, HostileAI
from components import consumable
from components.fighter import Fighter
from components.inventory import Inventory
from entity import Actor, Item


class EntityFactory:

    player = Actor(
        char="@",
        color=(255, 255, 255),
        name="Player",
        ai_cls=BaseAI,
        fighter=Fighter(hp=30, defense=2, power=5),
        inventory=Inventory(capacity=26)
    )

    orc = Actor(
        char="o",
        color=(63, 127, 63),
        name="orc",
        ai_cls=HostileAI,
        fighter=Fighter(hp=10, defense=0, power=3),
        inventory=Inventory(capacity=0),
    )

    troll = Actor(
        char="T",
        color=(0, 127, 0),
        name="troll",
        ai_cls=HostileAI,
        fighter=Fighter(hp=16, defense=1, power=4),
        inventory=Inventory(capacity=0)
    )

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
