class NoGivenElementException(Exception):
    """Shouldn't be raised on its own. Parent class for other exceptions used in the program"""

    def __init__(self, mode, value):
        message = f"Given {mode} '{value}' doesn't exist. Your program might be lacking some components or " \
                  f"API has incomplete data."
        super().__init__(message)


class NoGivenTypeException(NoGivenElementException):
    """Raised when a pokemon or a move tries to use a type that doesn't exist"""

    def __init__(self, typ):
        super().__init__("type", typ)


class NoGivenAbilityException(NoGivenElementException):
    """Raised when a pokemon tries to use an ability that doesn't exist"""

    def __init__(self, ability):
        super().__init__("ability", ability)


class NoGivenMoveException(NoGivenElementException):
    """Raised when a pokemon tries to use a move that doesn't exist"""

    def __init__(self, move):
        super().__init__("move", move)


class NoGivenPokemonException(NoGivenElementException):
    """Raised when program tries to use a pokemon that doesn't exist"""

    def __init__(self, pokemon):
        super().__init__("pokeon", pokemon)
