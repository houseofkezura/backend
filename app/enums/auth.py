from enum import Enum


class RoleNames(Enum):
    """ENUMS for the name filed in Role Model"""
    SUPER_ADMIN = "Super Admin" # System configuration access
    ADMIN = "Admin" # Full access to dashboard/operations
    CRM_Staff = "CRM Staff" # Packaging team, access to order fulfillment
    CUSTOMER = "Customer" # Default Role
    ORGANIZER = "Organizer"

    @classmethod
    def get_member_by_value(cls, value):
        return next((member for name, member in cls.__members__.items() if member.value == value), None)
    
    def __str__(self):
        return self.value