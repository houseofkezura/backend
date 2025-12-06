from enum import Enum


class RoleNames(Enum):
    """ENUMS for the name filed in Role Model"""
    SUPER_ADMIN = "Super Admin" # System configuration access
    ADMIN = "Admin" # Full access to dashboard/operations
    OPERATIONS = "Operations" # Operations team access
    CRM_MANAGER = "CRM Manager" # CRM management access
    CRM_Staff = "CRM Staff" # Packaging team, access to order fulfillment
    FINANCE = "Finance" # Finance team access
    SUPPORT = "Support" # Customer support access
    CUSTOMER = "Customer" # Default Role
    ORGANIZER = "Organizer"

    @classmethod
    def get_member_by_value(cls, value):
        return next((member for name, member in cls.__members__.items() if member.value == value), None)
    
    def __str__(self):
        return self.value