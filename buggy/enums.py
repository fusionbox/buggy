from enumfields import IntEnum, Enum


class Priority(IntEnum):
    HOLD = 1
    NORMAL = 2
    URGENT = 3

    class Labels:
        HOLD = 'hold'
        NORMAL = 'normal'
        URGENT = 'urgent'


class State(Enum):
    NEW = 'new'
    CLOSED = 'closed'
    ENTRUSTED = 'entrusted'
    VERIFIED = 'verified'
    REOPENED = 'reopened'
    LIVE = 'live'
    RESOLVED_FIXED = 'resolved-fixed'
    RESOLVED_UNREPRODUCIBLE = 'resolved-unreproducible'
    RESOLVED_DUPLICATE = 'resolved-duplicate'
    RESOLVED_IMPOSSIBLE = 'resolved-impossible'
    RESOLVED_NOT_A_BUG = 'resolved-notabug'

    class Labels:
        NEW = 'new'
        CLOSED = 'closed'
        ENTRUSTED = 'entrusted'
        VERIFIED = 'verified'
        REOPENED = 'reopened'
        LIVE = 'live'
        RESOLVED_FIXED = 'resolved - fixed'
        RESOLVED_UNREPRODUCIBLE = 'resolved - unreproducible'
        RESOLVED_DUPLICATE = 'resolved - duplicate'
        RESOLVED_IMPOSSIBLE = 'resolved - impossible'
        RESOLVED_NOT_A_BUG = 'resolved - not a bug'
