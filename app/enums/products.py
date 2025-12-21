"""
Enums for product-related models.
"""

from enum import Enum


class ProductCategory(Enum):
    """Product categories."""
    WIGS = "Wigs"
    BUNDLES = "Bundles"
    HAIR_CARE = "Hair Care"
    
    def __str__(self):
        return self.value


class HairType(Enum):
    """Hair type options."""
    HUMAN_HAIR = "Human Hair"
    VIRGIN = "Virgin"
    REMY = "Remy"
    CURLY = "Curly"
    STRAIGHT = "Straight"
    WAVY = "Wavy"
    KINKY = "Kinky"
    COILY = "Coily"
    
    def __str__(self):
        return self.value


class Texture(Enum):
    """Hair texture options."""
    BODY_WAVE = "Body Wave"
    LOOSE_WAVE = "Loose Wave"
    DEEP_WAVE = "Deep Wave"
    STRAIGHT = "Straight"
    CURLY = "Curly"
    
    def __str__(self):
        return self.value


class LaceType(Enum):
    """Lace type options."""
    LACE_13X4 = "13x4"
    LACE_13X6 = "13x6"
    LACE_360 = "360"
    FULL_LACE = "Full Lace"
    NO_LACE = "No Lace"
    
    def __str__(self):
        return self.value


class Density(Enum):
    """Hair density options."""
    LIGHT = "Light"
    MEDIUM = "Medium"
    HEAVY = "Heavy"
    EXTRA_HEAVY = "Extra Heavy"
    
    def __str__(self):
        return self.value


class CapSize(Enum):
    """Cap size options."""
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    ADJUSTABLE = "Adjustable"
    
    def __str__(self):
        return self.value


class LaunchStatus(Enum):
    """Product launch status."""
    NEW_DROP = "New Drop"
    LIMITED_EDITION = "Limited Edition"
    PRE_ORDER = "Pre-Order"
    IN_STOCK = "In-Stock"
    OUT_OF_STOCK = "Out of Stock"
    
    def __str__(self):
        return self.value







