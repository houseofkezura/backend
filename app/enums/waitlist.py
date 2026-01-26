from enum import Enum


class WaitlistStatus(Enum):
    """
    Enumeration of possible waitlist entry statuses.
    """
    PENDING = "pending"
    INVITED = "invited"
    CONVERTED = "converted"

    def __str__(self):
        return self.value
