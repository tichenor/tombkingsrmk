import copy
import sys
import traceback

import tcod

import setup
from config import Config as cfg

import exceptions
import input_handlers


def main() -> None:
    # Load tiles
    tileset = tcod.tileset.load_tilesheet(
        'assets/dejavu10x10_gs_tc.png', 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    handler: input_handlers.BaseEventHandler = setup.MainMenu()

    with tcod.context.new_terminal(
            cfg.SCREEN_WIDTH,
            cfg.SCREEN_HEIGHT,
            tileset=tileset,
            title=cfg.GAME_TITLE,
            vsync=True,
    ) as context:
        # order F changes how numpy (which tcod uses) accesses 2D arrays from [y,x] to [x,y]
        root_console = tcod.Console(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT, order="F")

        try:
            # Game loop
            while True:
                # Draw things to the screen.
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)

                # Handle events.
                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        # Update the handling of input based on the event (e.g. opening menu, reading scroll may
                        # change how input should be handled and how things should be drawn to the screen).
                        handler = handler.handle_events(event)
                except Exception as err:  # Handle exceptions in-game.
                    traceback.print_exc()  # Print error to stderr.
                    # Then print it to the in-game message log.
                    if isinstance(handler, input_handlers.EventHandler):
                        err_type, err_val, *_ = sys.exc_info()
                        handler.engine.message_log.add_message(
                            err.__class__.__name__ + ": " + err.__str__(), cfg.Color.ERROR
                        )
                        if cfg.DEBUG:
                            handler.engine.debug_log.add_message(traceback.format_exc(), cfg.Color.ERROR)

        except exceptions.QuitWithoutSaving:
            raise
        except SystemExit:  # Save and quit.
            setup.save_game(handler, "savegame.sav")
            raise
        except BaseException:  # Save on any other unexpected exception.
            setup.save_game(handler, "savegame.sav")
            raise


if __name__ == '__main__':
    main()
