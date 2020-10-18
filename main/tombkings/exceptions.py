

class Impossible(Exception):
    """Raised when an action is not possible to perform."""


class QuitWithoutSaving(SystemExit):
    """Can be raised to exit the game without automatically saving"""
