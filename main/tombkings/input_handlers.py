from __future__ import annotations

import os
from typing import Optional, TYPE_CHECKING, Callable, Tuple, Union
from overrides import overrides

import tcod.event

import actions
from actions import Action, BumpAction, WaitAction, PickupAction
import exceptions
from config import Config as cfg

if TYPE_CHECKING:
    from components.spell import Spell
    from engine import Engine
    from entity import Item

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # Vi keys.
    tcod.event.K_h: (-1, 0),
    tcod.event.K_j: (0, 1),
    tcod.event.K_k: (0, -1),
    tcod.event.K_l: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (1, -1),
    tcod.event.K_b: (-1, 1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER
}

# Other actions and menus

PICKUP_ITEM_KEY = tcod.event.K_g
DROP_ITEM_KEY = tcod.event.K_d
OPEN_INVENTORY_KEY = tcod.event.K_i
SHOW_MESSAGE_HISTORY_KEY = tcod.event.K_v
LOOK_AROUND_KEY = tcod.event.K_x
DOWNSTAIRS_KEY = tcod.event.K_LESS
CHARACTER_INFO_KEY = tcod.event.K_c
SPELL_MENU_KEY = tcod.event.K_z

# Special

DEBUG_CONSOLE_KEY = tcod.event.K_t

CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}

ActionOrHandler = Union[Action, "BaseEventHandler"]
"""
An event handler return value that can trigger an action *or* switch active handlers.

If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted to be executed, and if it's valid, then
MainEventHandler will become the active handler.
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)  # Send the event to a ev_* method.
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    @overrides
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()


class EventHandler(BaseEventHandler):

    def __init__(self, engine: Engine):
        self._engine = engine

    @overrides
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)  # Send the event to a ev_* method.
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self._engine.player.is_alive:
                # The played was killed some time during or after the action.
                return GameOverHandler(self._engine)
            elif self._engine.player.level.requires_level_up:
                return LevelUpEventHandler(self._engine)
            return MainEventHandler(self._engine)  # Otherwise return to the main handler.
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """Perform actions returned from event methods. Return true if the action should advance a turn."""
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self._engine.message_log.add_message(exc.args[0], cfg.Color.IMPOSSIBLE)
            return False  # Skip enemy turn when an action is not possible to perform.

        self._engine.handle_ai()
        self._engine.update_fov()
        return True

    @overrides
    def on_render(self, console: tcod.Console) -> None:
        self._engine.render(console)

    @overrides
    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        """Update the mouse position on mouse motion events."""
        if self._engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self._engine.mouse_location = event.tile.x, event.tile.y

    @property
    def engine(self):
        return self._engine


class MainEventHandler(EventHandler):

    @overrides
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:

        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod
        player = self._engine.player

        # Movement/action keys
        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)

        elif key in WAIT_KEYS:
            action = WaitAction(player)

        elif key == DOWNSTAIRS_KEY and modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
            """Key is >, e.g. `shift + <`"""
            return actions.StairsAction(player)

        # Various menu/info commands
        elif key == SHOW_MESSAGE_HISTORY_KEY:
            return HistoryViewer(self._engine)

        elif key == PICKUP_ITEM_KEY:
            action = PickupAction(player)

        elif key == OPEN_INVENTORY_KEY:
            return InventoryActivateHandler(self._engine)

        elif key == CHARACTER_INFO_KEY:
            return CharacterInfoEventHandler(self._engine)

        elif key == DROP_ITEM_KEY:
            return InventoryDropHandler(self._engine)

        elif key == LOOK_AROUND_KEY:
            return LookHandler(self._engine)

        elif key == SPELL_MENU_KEY:
            return SpellMenuHandler(self._engine)

        # Other/special
        elif cfg.DEBUG and key == DEBUG_CONSOLE_KEY:
            return DebugConsoleHandler(self._engine)

        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()

        # No valid key was pressed
        return action


class GameOverHandler(EventHandler):

    @staticmethod
    def _on_quit() -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Delete the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game (played is dead).

    @overrides
    def ev_quit(self, event: tcod.event.Quit) -> None:
        self._on_quit()

    @overrides
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self._on_quit()


class AskUserEventHandler(EventHandler):
    """Superclass for handling user input for actions which require special input."""

    @overrides
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default, pressing any key will exit this input handler."""
        if event.sym in {  # Ignore modifier keys.
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    @overrides
    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """By default, any mouse click exits this input handler."""
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """
        Called when the user is trying to exit or cancel an action. By default this returns to the main event handler.
        """
        return MainEventHandler(self._engine)


class SpellMenuHandler(AskUserEventHandler):
    """Handles the user selecting a spell."""
    title = "Memorized spells"

    @overrides
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        num_spells = len(self.engine.player.spellbook.spells)
        height = max(num_spells + 2, 3)

        x = 0
        y = 0
        if self.engine.player.x <= 30:
            x = 40

        width = len(self.title) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.title,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if num_spells > 0:
            for i, spell in enumerate(self.engine.player.spellbook.spells):
                spell_key = chr(ord("a") + i)
                spell_str = f"({spell_key}) {spell.name}"
                console.print(x + 1, y + i + 1, spell_str)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    @overrides
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_spell = player.spellbook.spells[index]
            except IndexError:
                self._engine.message_log.add_message("Invalid entry.", cfg.Color.INVALID)
                return None
            return self.on_spell_selected(selected_spell)

        return super().ev_keydown(event)

    def on_spell_selected(self, spell: Spell) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid spell."""
        return spell.get_action()


class InventoryEventHandler(AskUserEventHandler):
    """This handler lets the user select an item. What happens depends on the subclass."""

    title = "<no title>"

    @overrides
    def on_render(self, console: tcod.Console) -> None:
        """
        Render an inventory menu that displays the items in the inventory and the letter to select them.
        Will move to a different position based on where the player is located, so the player can always see
        where they are.
        """
        super().on_render(console)
        num_items = len(self._engine.player.inventory.items)

        height = max(num_items + 2, 3)

        if self._engine.player.x <= 30:
            x = 40
        else:
            x = 0
        y = 0

        width = len(self.title) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.title,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if num_items > 0:
            for i, item in enumerate(self._engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                is_equipped = self.engine.player.equipment.is_item_equipped(item)
                item_str = f"({item_key}) {item.name}"
                if is_equipped:
                    item_str = f"{item_str} (worn)"
                    console.print(x + 1, y + i + 1, item_str, fg=cfg.Color.GREEN)
                else:
                    console.print(x + 1, y + i + 1, item_str)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    @overrides
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self._engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self._engine.message_log.add_message("Invalid entry.", cfg.Color.INVALID)
                return None
            return self.on_item_selected(selected_item)

        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        raise NotImplementedError()


class InventoryActivateHandler(InventoryEventHandler):
    """Handle using an inventory item."""

    title = "Select an item to use."

    @overrides
    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Return the action for the selected item."""
        if item.consumable:
            return item.consumable.get_action(self._engine.player)
        elif item.equippable:
            return actions.EquipAction(self._engine.player, item)
        else:
            return None


class InventoryDropHandler(InventoryEventHandler):
    """Handle dropping an inventory item."""

    title = "Select an item to drop."

    @overrides
    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Drop this item."""
        return actions.DropItem(self._engine.player, item)


class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index (position) on the game map."""

    def __init__(self, engine: Engine):
        """Set the cursor to the player's position when this handler is constructed."""
        super().__init__(engine)
        player = self._engine.player
        self._prev_mouse_location: Tuple[int, int] = engine.mouse_location
        engine.mouse_location = player.x, player.y

    @overrides
    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self._engine.mouse_location
        console.tiles_rgb["bg"][x, y] = cfg.Color.WHITE
        console.tiles_rgb["fg"][x, y] = cfg.Color.BLACK

    @overrides
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1  # Holding modifier keys will result in larger movement shifts.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self._engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor position (index) to the map size.
            x = max(0, min(x, self._engine.game_map.width - 1))
            y = max(0, min(y, self._engine.game_map.height - 1))
            self._engine.mouse_location = x, y
            return None

        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self._engine.mouse_location)

        return super().ev_keydown(event)

    @overrides
    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self._engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError()


class LookHandler(SelectIndexHandler):
    """Let the player look around using the keyboard."""

    @overrides
    def on_index_selected(self, x: int, y: int) -> MainEventHandler:
        """Return to the main handler."""
        self._engine.mouse_location = self._prev_mouse_location  # Move the location back to the last mouse position.
        return MainEventHandler(self._engine)


class SingleRangedTargetingHandler(SelectIndexHandler):
    """Handles targeting a single entity or actor, e.g. shooting an arrow, a lightning bolt, etc."""

    def __init__(self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]):
        super().__init__(engine)
        self._callback = callback

    @overrides
    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        self._engine.mouse_location = self._prev_mouse_location  # Move the location back to the last mouse position.
        return self._callback((x, y))


class AreaRangedTargetingHandler(SelectIndexHandler):
    """
    Handles targeting an area within a given radius, not necessarily containing any entities. Any entity
    within the given radius will be affected.
    """

    def __init__(
            self,
            engine: Engine,
            radius: int,
            callback: Callable[[Tuple[int, int]], Optional[Action]],
    ):
        super().__init__(engine)
        self._radius = radius
        self._callback = callback

    @overrides
    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = self._engine.mouse_location

        # Draw a rectangle around the targeted area so the player can see what will be affected.
        console.draw_frame(
            x=x - self._radius - 1,
            y=y - self._radius - 1,
            width=self._radius ** 2,
            height=self._radius ** 2,
            fg=cfg.Color.RED,
            clear=False,
        )

    @overrides
    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        self._engine.mouse_location = self._prev_mouse_location  # Move the location back to the last mouse position.
        return self._callback((x, y))


class CharacterInfoEventHandler(AskUserEventHandler):

    @overrides
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        player = self._engine.player

        x = cfg.CharacterInfoWindow.get_pos_x(self._engine.player.x)
        y = cfg.CharacterInfoWindow.POS_Y

        console.draw_frame(
            x=x,
            y=y,
            width=cfg.CharacterInfoWindow.WIDTH,
            height=cfg.CharacterInfoWindow.HEIGHT,
            title=cfg.CharacterInfoWindow.TITLE,
            clear=True,
            fg=cfg.CharacterInfoWindow.FOREGROUND_COLOR,
            bg=cfg.CharacterInfoWindow.BACKGROUND_COLOR,
        )

        console.print(
            x=x + 1,
            y=y + 1,
            string=f"Current level: {player.level.current_level}"
        )

        console.print(
            x=x + 1,
            y=y + 2,
            string=f"Experience points: {player.level.current_experience}",
        )

        console.print(
            x=x + 1,
            y=y + 3,
            string=f"To next level: {player.level.experience_to_next_level}"
        )

        console.print(
            x=x + 1,
            y=y + 5,
            string=f"Attack power: {player.fighter.power}"
        )

        console.print(
            x=x + 1,
            y=y + 6,
            string=f"Defense: {player.fighter.defense}"
        )


class LevelUpEventHandler(AskUserEventHandler):

    @overrides
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        x = cfg.LevelUpWindow.get_pos_x(self.engine.player.x)  # Position the window so it isn't drawn over the player.
        y = cfg.LevelUpWindow.POS_Y

        console.draw_frame(
            x=x,
            y=y,
            width=cfg.LevelUpWindow.WIDTH,
            height=cfg.LevelUpWindow.HEIGHT,
            title=cfg.LevelUpWindow.TITLE,
            clear=True,
            fg=cfg.LevelUpWindow.FOREGROUND_COLOR,
            bg=cfg.LevelUpWindow.BACKGROUND_COLOR,
        )

        console.print(x=x+1, y=y+2, string=cfg.LevelUpWindow.TEXT)

        console.print(
            x=x+1,
            y=y+4,
            string=f"(a) Constitution (increase max health)"
        )

        console.print(
            x=x+1,
            y=y+5,
            string=f"(b) Strength (increase attack power)",
        )

    @overrides
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:

        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 1:  # Depends on the number of options, needs to change if options are changed.
            if index == 0:
                player.fighter.modify_max_hp(cfg.Experience.LEVEL_UP_HEALTH)
                player.level.increase_level()
            elif index == 1:
                player.fighter.increase_base_power(cfg.Experience.LEVEL_UP_POWER)
                player.level.increase_level()
        else:
            self.engine.message_log.add_message("Invalid entry.", cfg.Color.INVALID)
            return None

        return super().ev_keydown(event)

    @overrides
    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """Don't allow the player to click to exit the menu."""
        return None


class HistoryViewer(EventHandler):
    """Show the message/text history on a larger window that can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self._log_length = len(engine.message_log.messages)
        self._cursor = self._log_length - 1

    @overrides
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # First draw the main game state as the background.

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "Message history", alignment=tcod.CENTER
        )

        # Render the message log using the cursor parameter.
        self._engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self._engine.message_log.messages[: self._cursor + 1]
        )
        log_console.blit(console, 3, 3)

    @overrides
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainEventHandler]:
        # Conditional movement to get the right feel.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]

            if adjust < 0 and self._cursor == 0:
                # Only move from the top to the bottom when you are on the edge.
                self._cursor = self._log_length - 1
            elif adjust > 0 and self._cursor == self._log_length - 1:
                # Same with bottom to top movement.
                self._cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self._cursor = max(0, min(self._cursor + adjust, self._log_length - 1))

        elif event.sym == tcod.event.K_HOME:
            self._cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.K_END:
            self._cursor = self._log_length - 1  # Move directly to the last message.
        else:
            # Any other key pressed moves back to the main game state.
            return MainEventHandler(self._engine)
        return None


class PopupMessage(BaseEventHandler):
    """Display a popup text window that disappears when any key is pressed."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self._parent = parent_handler
        self._text = text

    @overrides
    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self._parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self._text,
            fg=cfg.Color.WHITE,
            bg=cfg.Color.BLACK,
            alignment=tcod.CENTER,
        )

    @overrides
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self._parent


class DebugConsoleHandler(EventHandler):

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self._log_length = len(engine.debug_log.messages)
        self._typing: bool = False
        self._input_text: str = ""

    @overrides
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        log_console = tcod.Console(console.width - 6, console.height - 6)
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "Debug command line", alignment=tcod.CENTER
        )

        self._engine.debug_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 4,
            self._engine.debug_log.messages
        )

        if self._typing:
            log_console.draw_frame(0, log_console.height - 3, log_console.width, 3)
            log_console.print_box(0, log_console.height - 3, log_console.width, 3, "")
            log_console.print(1, log_console.height - 2, self._input_text)

        log_console.blit(console, 3, 3)

    @overrides
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainEventHandler]:

        if event.sym in CONFIRM_KEYS:

            if not self._typing:
                # Start typing by pressing return or enter
                self._typing = True
                return
            # If user is typing, return or enter submits the message/command
            self._engine.debug_log.add_message(self._input_text, stack=False)
            self._engine.parse_user_command(self._input_text)
            self._input_text = ""
            self._typing = False
            return

        elif event.sym == tcod.event.K_BACKSPACE:
            # Remove the last character from input
            if self._input_text:
                self._input_text = self._input_text[:-1]
                return

        # Any other keypress exits the debugger
        elif not self._typing:
            return MainEventHandler(self._engine)

    @overrides
    def ev_textinput(self, event: tcod.event.TextInput) -> Optional[MainEventHandler]:
        if not self._typing:
            return
        self._input_text += event.text
        return



