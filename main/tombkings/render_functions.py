from __future__ import annotations

from typing import TYPE_CHECKING

from config import Config as cfg

if TYPE_CHECKING:
    from tcod import Console
    from engine import Engine
    from game_map import GameMap


def render_bar(
        console: Console,
        current_value: int,
        max_value: int,
        total_width: int,
) -> None:

    bar_width = int(float(current_value) / max_value * total_width)

    console.draw_rect(
        x=cfg.HealthBar.POS_X,
        y=cfg.HealthBar.POS_Y,
        width=cfg.HealthBar.WIDTH,
        height=cfg.HealthBar.HEIGHT,
        ch=1,
        bg=cfg.Color.BAR_EMPTY
    )

    if bar_width > 0:

        console.draw_rect(
            x=cfg.HealthBar.POS_X,
            y=cfg.HealthBar.POS_Y,
            width=bar_width,
            height=1,
            ch=1,
            bg=cfg.Color.BAR_FILLED
        )

        console.print(
            x=cfg.HealthBar.POS_X + 1,
            y=cfg.HealthBar.POS_Y,
            string=f"HP: {current_value}/{max_value}",
            fg=cfg.Color.BAR_TEXT
        )


def render_names_at_mouse_location(
        console: Console,
        x: int,
        y: int,
        engine: Engine,
) -> None:
    """Render the names of any entities at the mouse position at the specified (x,y)-position."""
    m_x, m_y = engine.mouse_location
    names_at_location = _get_names_at(x=m_x, y=m_y, game_map=engine.game_map)
    console.print(x=x, y=y, string=names_at_location)


def _get_names_at(x: int, y: int, game_map: GameMap) -> str:
    """Return a string of names of all entities at a given coordinate."""
    if not game_map.in_bounds(x, y) or not game_map.visible_tiles[x, y]:
        return ""

    names = ", ".join(
        entity.name for entity in game_map.entities if entity.x == x and entity.y == y
    )

    return names.capitalize()