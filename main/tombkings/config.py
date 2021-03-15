from typing import Tuple, List


class Config:

    # General

    DEBUG = True

    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50

    GAME_TITLE = "Tomb kings"

    LIMIT_FPS = 20

    class Vision:

        DEFAULT_FOV_RADIUS = 8

    class Gui:

        HEIGHT = 12  # Unused.
        DUNGEON_FLOOR_TEXT_POS_X = 0
        DUNGEON_FLOOR_TEXT_POS_Y = 47

    class LevelUpWindow:

        POS_Y: int = 0

        TITLE: str = "Your experience in battle has reached new heights."
        TEXT: str = "Select an attribute to increase."
        WIDTH: int = len(TITLE) + 4
        HEIGHT: int = 8

        FOREGROUND_COLOR: Tuple[int, int, int] = (255, 255, 255)
        BACKGROUND_COLOR: Tuple[int, int, int] = (0, 0, 0)

        @staticmethod
        def get_pos_x(player_x: int) -> int:
            if player_x <= Config.LevelUpWindow.WIDTH:
                return Config.SCREEN_WIDTH // 2
            return 0

    class CharacterInfoWindow:

        POS_Y: int = 0

        TITLE: str = "Character information"
        WIDTH: int = len(TITLE) + 4
        HEIGHT: int = 8

        FOREGROUND_COLOR: Tuple[int, int, int] = (255, 255, 255)
        BACKGROUND_COLOR: Tuple[int, int, int] = (0, 0, 0)

        @staticmethod
        def get_pos_x(player_x: int) -> int:
            if player_x <= Config.CharacterInfoWindow.WIDTH:
                return Config.SCREEN_WIDTH // 2
            return 0

    class MainMenu:

        WIDTH = 24

    class Log:

        POS_X = 21
        POS_Y = 45
        WIDTH = 40
        HEIGHT = 5

    class HealthBar:

        POS_X = 0
        POS_Y = 45
        WIDTH = 20
        HEIGHT = 1

    class Map:

        WIDTH = 80
        HEIGHT = 43

        ROOM_MAX_SIZE = 10
        ROOM_MIN_SIZE = 6
        MAX_ROOMS = 30

        MAX_MONSTERS_PER_ROOM = 3
        MAX_ITEMS_PER_ROOM = 2
        MAX_MONSTERS_PER_FLOOR = 40
        MAX_ITEMS_PER_FLOOR = 20

        MAX_ITEMS_BY_FLOOR: List[Tuple[int, int]] = [
            (1, 1),
            (4, 2),
        ]

        MAX_MONSTERS_BY_FLOOR: List[Tuple[int, int]] = [
            (1, 2),
            (4, 3),
            (6, 5),
        ]

    class Experience:

        LEVEL_UP_HEALTH = 8
        LEVEL_UP_POWER = 1
        LEVEL_UP_DEFENSE = 1

    class Color:

        WHITE = (0xFF, 0xFF, 0xFF)
        BLACK = (0x0, 0x0, 0x0)
        RED = (0xFF, 0x0, 0x0)
        GREEN = (0x0, 0xB0, 0x0)

        MENU_TITLE = (255, 255, 63)
        MENU_TEXT = WHITE

        PLAYER_ATK = (0xE0, 0xE0, 0xE0)
        ENEMY_ATK = (0xFF, 0xC0, 0xC0)
        NEEDS_TARGET = (0x3F, 0xFF, 0xFF)
        STATUS_EFFECT_APPLIED = (0x3F, 0xFF, 0x3F)
        DESCEND = (0x9F, 0x3F, 0xFF)

        PLAYER_DIE = (0xFF, 0x30, 0x30)
        ENEMY_DIE = (0xFF, 0xA0, 0x30)

        INVALID = (0xFF, 0xFF, 0x00)
        IMPOSSIBLE = (0x80, 0x80, 0x80)
        ERROR = (0xFF, 0x40, 0x40)

        WELCOME_TEXT = (0x20, 0xA0, 0xFF)
        HEALTH_RECOVERED = (0x0, 0xFF, 0x0)

        BAR_TEXT = WHITE
        BAR_FILLED = (0x0, 0x60, 0x0)
        BAR_EMPTY = (0x40, 0x10, 0x10)

    class Tooltip:

        POS_X = 21
        POS_Y = 44
