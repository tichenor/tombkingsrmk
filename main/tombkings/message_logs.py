from typing import Iterable, List, Reversible, Tuple
import textwrap

import tcod

from config import Config as cfg


class Message:

    def __init__(self, text: str, fg: Tuple[int, int, int]):
        self._plain_text = text
        self._fg = fg
        self._count = 1

    @property
    def full_text(self) -> str:
        """The full text of this message, including the count if necessary."""
        if self._count > 1:
            return f"{self._plain_text} (x{self._count})"
        return self._plain_text

    @property
    def plain_text(self):
        return self._plain_text

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value):
        self._count = value

    @property
    def fg(self):
        return self._fg


class MessageLog:

    def __init__(self) -> None:
        self._messages: List[Message] = []

    def add_message(
            self,
            text: str,
            fg: Tuple[int, int, int] = cfg.Color.WHITE,
            *,
            stack: bool = True,
    ) -> None:
        """
        Add a message to this log.
        :param text: The message text.
        :param fg: The text color (fg stands for forground).
        :param stack: If True, the message can stack with a previous message with the same text.
        """
        if stack and self._messages and text == self._messages[-1].plain_text:
            self._messages[-1].count += 1
        else:
            self._messages.append(Message(text, fg))

    def render(
            self,
            console: tcod.Console,
            x: int,
            y: int,
            width: int,
            height: int,
    ) -> None:
        """
        Render this log over the given area.
        :param console: The console to draw upon.
        :param x, y, width, height: The rectangular region to render on.
        """
        self.render_messages(console, x, y, width, height, self._messages)

    @classmethod
    def render_messages(
            cls,
            console: tcod.Console,
            x: int,
            y: int,
            width: int,
            height: int,
            messages: Reversible[Message],
    ) -> None:
        """
        Render the messages provided. The messages are rendered starting from the last and working backwards.
        :param console: The console to draw upon
        :param x, y, width, height: The rectangular region to render on.
        :param messages: The list of messages.
        """
        y_offset = height - 1

        for msg in reversed(messages):
            for line in reversed(list(cls.wrap(msg.full_text, width))):
                console.print(x=x, y=y+y_offset, string=line, fg=msg.fg)
                y_offset -= 1
                if y_offset < 0:
                    return  # No more space to print messages.

    @staticmethod
    def wrap(string: str, width: int) -> Iterable[str]:
        """Return a wrapped text message."""
        for line in string.splitlines():  # Handle newlines in message.
            yield from textwrap.wrap(
                line, width, expand_tabs=True,
            )

    @property
    def messages(self):
        return self._messages

