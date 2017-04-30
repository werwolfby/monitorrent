from aenum import Enum


class Status(Enum):
    Ok = 1,
    Error = 2,
    NotFound = 404,
    Unknown = 999

    @staticmethod
    def parse(name):
        names = {e.name.lower(): e for e in Status}
        return names[name.lower()]

    def __str__(self):
        if self == Status.Ok:
            return u"Ok"
        if self == Status.NotFound:
            return u"Not Found"
        if self == Status.Error:
            return u"Error"
        return u"Unknown"
