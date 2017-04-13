from enum import IntEnum, Enum


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class State(Enum):
    NEW = 'new'
    CLOSED = 'closed'
    ENTRUSTED = 'entrusted'
    VERIFIED = 'verified'
    REOPENED = 'reopened'
    LIVE = 'live'
    RESOLVED_FIXED = 'resolved-fixed'
    RESOLVED_UNREPROPDUCIBLE = 'resolved-unreproducible'
    RESOLVED_DUPLICATE = 'resolved-duplicate'
    RESOLVED_IMPOSSIBLE = 'resolved-impossible'
    RESOLVED_NOT_A_BUG = 'resolved-notabug'
