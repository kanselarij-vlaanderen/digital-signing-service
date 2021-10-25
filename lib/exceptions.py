
class NoQueryResultsException(Exception):
    pass


class ResourceNotFoundException(Exception):
    """uri or id does not reference an existing resource"""
    def __init__(self, uri):
        super().__init__(f"\"{uri}\" not found." )
        self.uri = uri

class InvalidStateException(Exception):
    """state does not allow the requested action."""


class InvalidArgumentException(Exception):
    """provided argument is not valid"""
