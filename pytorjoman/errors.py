class NotFoundError(Exception):
    pass


class AlreadyExistError(Exception):
    pass


class IncorrectPasswordError(Exception):
    pass


class UnknownError(Exception):
    pass


class UnloggedInError(Exception):
    pass

class TokenExpiredError(Exception):
    pass

class NotAllowedError(Exception):
    pass