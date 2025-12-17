"""Data schemas for API responses.

These schemas represent only the data portion of responses.
The quas-docs package automatically wraps them in base response envelopes.

Following best practices from quas-docs to avoid "additionalProp1" issues
by using proper Pydantic models instead of Dict[str, Any] for nested structures.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ============================================================================
# Nested Data Models (to avoid additionalProp1 issues)
# ============================================================================

class WalletInfo(BaseModel):
    """Wallet information."""
    class Config:
        extra = "forbid"
    
    balance: Optional[float] = None
    currency_name: Optional[str] = None
    currency_code: Optional[str] = None
    currency_symbol: Optional[str] = None


class UserProfileInfo(BaseModel):
    """User profile information."""
    class Config:
        extra = "forbid"
    
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    referral_link: Optional[str] = None


class AddressInfo(BaseModel):
    """Address information."""
    class Config:
        extra = "forbid"
    
    country: Optional[str] = None
    state: Optional[str] = None


class UserDataModel(BaseModel):
    """User data model."""
    class Config:
        extra = "allow"
    
    id: str
    username: Optional[str] = None
    email: Optional[str] = None
    date_joined: Optional[str] = None
    has_updated_default_password: Optional[bool] = None
    wallet: Optional[WalletInfo] = None
    roles: List[str] = []
    # Profile fields (merged from profile)
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    referral_link: Optional[str] = None
    # Address fields (merged from address)
    country: Optional[str] = None
    state: Optional[str] = None


class ProductVariantAttributes(BaseModel):
    """Product variant attributes."""
    class Config:
        extra = "allow"
    
    length: Optional[str] = None
    texture: Optional[str] = None
    color: Optional[str] = None
    lace_type: Optional[str] = None
    density: Optional[str] = None
    cap_size: Optional[str] = None
    hair_type: Optional[str] = None


class InventoryInfo(BaseModel):
    """Inventory information."""
    class Config:
        extra = "forbid"
    
    id: str
    variant_id: str
    quantity: int
    reserved_quantity: int
    low_stock_threshold: int
    is_low_stock: bool


class ProductVariantDataModel(BaseModel):
    """Product variant data."""
    class Config:
        extra = "forbid"
    
    id: str
    sku: str
    price_ngn: float
    price_usd: Optional[float] = None
    weight_g: Optional[int] = None
    attributes: ProductVariantAttributes
    is_in_stock: bool
    stock_quantity: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    inventory: Optional[InventoryInfo] = None


class ProductDataModel(BaseModel):
    """Product data model."""
    
    
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    category: str
    metadata: Optional[Dict[str, Any]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    launch_status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    variants: Optional[List[ProductVariantDataModel]] = None


class OrderItemData(BaseModel):
    """Order item data."""
    class Config:
        extra = "forbid"
    
    id: str
    variant_id: str
    quantity: int
    unit_price: float
    line_total: float
    variant: Optional[ProductVariantDataModel] = None
    created_at: Optional[str] = None


class OrderDataModel(BaseModel):
    """Order data model."""
    class Config:
        extra = "forbid"
    
    id: str
    status: str
    subtotal: float
    shipping_cost: float
    discount: float
    points_redeemed: int
    total: float
    amount: float  # Legacy field
    currency: str
    payment_ref: Optional[str] = None
    shipping_address: Optional[Dict[str, Any]] = None
    packed_by_crm_id: Optional[str] = None
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    user_id: Optional[str] = None
    user: Optional[UserDataModel] = None
    items: Optional[List[OrderItemData]] = None


class CartItemDataModel(BaseModel):
    """Cart item data."""
    class Config:
        extra = "forbid"
    
    id: str
    variant_id: str
    quantity: int
    unit_price: float
    line_total: float
    variant: Optional[ProductVariantDataModel] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CartDataModel(BaseModel):
    """Cart data model."""
    class Config:
        extra = "forbid"
    
    id: str
    user_id: Optional[str] = None
    guest_token: Optional[str] = None
    items: List[CartItemDataModel] = []
    total_items: int
    subtotal: float
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LoyaltyAccountData(BaseModel):
    """Loyalty account data."""
    class Config:
        extra = "forbid"
    
    id: str
    user_id: str
    tier: str
    points_balance: int
    total_points_earned: int
    total_points_redeemed: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LoyaltyLedgerEntry(BaseModel):
    """Loyalty ledger entry."""
    class Config:
        extra = "forbid"
    
    id: str
    account_id: str
    transaction_type: str
    points: int
    balance_after: int
    description: Optional[str] = None
    reference_id: Optional[str] = None
    created_at: Optional[str] = None


class CmsPageDataModel(BaseModel):
    """CMS page data model."""
    class Config:
        extra = "forbid"
    
    id: str
    slug: str
    title: str
    content: str
    published: bool
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PaymentDataModel(BaseModel):
    """Payment data model."""
    class Config:
        extra = "forbid"
    
    id: str
    user_id: Optional[str] = None
    order_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AddressDataModel(BaseModel):
    """Address data model."""
    class Config:
        extra = "forbid"
    
    id: str
    user_id: str
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    country: str
    postal_code: Optional[str] = None
    is_default: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RevampRequestDataModel(BaseModel):
    """Revamp request data model."""
    class Config:
        extra = "forbid"
    
    id: str
    user_id: str
    order_id: str
    status: str
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RatingDataModel(BaseModel):
    """Rating data model."""
    class Config:
        extra = "forbid"
    
    id: str
    order_id: str
    crm_staff_id: str
    rating: int
    comment: Optional[str] = None
    created_at: Optional[str] = None


class B2BInquiryDataModel(BaseModel):
    """B2B inquiry data model."""
    class Config:
        extra = "forbid"
    
    id: str
    company_name: str
    contact_name: str
    email: str
    phone: str
    message: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class StaffDataModel(BaseModel):
    """Staff data model."""
    class Config:
        extra = "forbid"
    
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ShippingZoneData(BaseModel):
    """Shipping zone data."""
    class Config:
        extra = "forbid"
    
    id: str
    name: str
    country: str
    methods: List[Dict[str, Any]] = []


# ============================================================================
# Response Data Schemas
# ============================================================================

# Auth response data schemas
class SignupData(BaseModel):
    """Data returned after successful signup."""
    class Config:
        extra = "forbid"
    
    reg_id: str


class VerifyEmailData(BaseModel):
    """Data returned after successful email verification."""
    class Config:
        extra = "forbid"
    
    user_data: UserDataModel


class TokenValidationData(BaseModel):
    """Data returned after token validation."""
    class Config:
        extra = "forbid"
    
    valid: bool
    user_data: UserDataModel


class RefreshTokenData(BaseModel):
    """Data returned for token refresh guidance."""
    class Config:
        extra = "forbid"
    
    message: str


class EmailAvailabilityData(BaseModel):
    """Data returned for email availability check."""
    class Config:
        extra = "forbid"
    
    email: str
    available: bool


class UsernameAvailabilityData(BaseModel):
    """Data returned for username availability check."""
    class Config:
        extra = "forbid"
    
    username: str
    available: bool


class PasswordResetRequestData(BaseModel):
    """Data returned after password reset request."""
    class Config:
        extra = "forbid"
    
    reset_id: Optional[str] = None


class PasswordResetVerificationData(BaseModel):
    """Data returned after password reset code verification."""
    class Config:
        extra = "forbid"
    
    reset_id: str
    verified: bool


# Error data schemas
class ValidationErrorItem(BaseModel):
    """Single validation error item."""
    class Config:
        extra = "forbid"
    
    field: str
    message: str


class ValidationErrorData(BaseModel):
    """Data for validation errors."""
    class Config:
        extra = "forbid"
    
    errors: List[ValidationErrorItem]


# Profile response data schemas
class ProfileData(BaseModel):
    """Data returned for user profile."""
    class Config:
        extra = "forbid"
    
    profile: UserDataModel


# CMS response data schemas
class CmsPageData(BaseModel):
    """Data returned for CMS page."""
    class Config:
        extra = "forbid"
    
    page: CmsPageDataModel


# Product response data schemas
class ProductListData(BaseModel):
    """Data returned for product list."""
    class Config:
        extra = "forbid"
    
    products: List[ProductDataModel]
    total: int
    page: int
    per_page: int
    total_pages: int


class ProductData(BaseModel):
    """Data returned for single product."""
    class Config:
        extra = "forbid"
    
    product: ProductDataModel


class ProductSearchData(BaseModel):
    """Data returned for product search."""
    class Config:
        extra = "forbid"
    
    products: List[ProductDataModel]


class ProductVariantsData(BaseModel):
    """Data returned for product variants."""
    class Config:
        extra = "forbid"
    
    variants: List[ProductVariantDataModel]


# Cart response data schemas
class CartData(BaseModel):
    """Data returned for cart."""
    class Config:
        extra = "forbid"
    
    cart: CartDataModel


class CartItemData(BaseModel):
    """Data returned for cart item operations."""
    class Config:
        extra = "forbid"
    
    item: CartItemDataModel


# Order response data schemas
class OrderListData(BaseModel):
    """Data returned for order list."""
    class Config:
        extra = "forbid"
    
    orders: List[OrderDataModel]
    total: int
    page: int
    per_page: int
    total_pages: int


class OrderData(BaseModel):
    """Data returned for single order."""
    class Config:
        extra = "forbid"
    
    order: OrderDataModel


# Address response data schemas
class AddressListData(BaseModel):
    """Data returned for address list."""
    class Config:
        extra = "forbid"
    
    addresses: List[AddressDataModel]


class AddressData(BaseModel):
    """Data returned for single address."""
    class Config:
        extra = "forbid"
    
    address: AddressDataModel


# Loyalty response data schemas
class LoyaltyInfoData(BaseModel):
    """Data returned for loyalty information."""
    class Config:
        extra = "forbid"
    
    loyalty: LoyaltyAccountData


class LoyaltyLedgerData(BaseModel):
    """Data returned for loyalty ledger."""
    class Config:
        extra = "forbid"
    
    entries: List[LoyaltyLedgerEntry]
    total: int
    page: int
    total_pages: int


# B2B response data schemas
class B2BInquiryData(BaseModel):
    """Data returned after B2B inquiry creation."""
    class Config:
        extra = "forbid"
    
    inquiry_id: str


# Payment response data schemas
class PaymentInitData(BaseModel):
    """Data returned after payment initialization."""
    class Config:
        extra = "forbid"
    
    payment: PaymentDataModel


class PaymentVerificationData(BaseModel):
    """Data returned after payment verification."""
    class Config:
        extra = "forbid"
    
    payment: PaymentDataModel


class PaymentStatusData(BaseModel):
    """Data returned for payment status."""
    class Config:
        extra = "forbid"
    
    payment: PaymentDataModel


class PaymentHistoryData(BaseModel):
    """Data returned for payment history."""
    class Config:
        extra = "forbid"
    
    payments: List[PaymentDataModel]
    total: int
    page: int
    per_page: int
    total_pages: int


# Checkout response data schemas
class CheckoutData(BaseModel):
    """Data returned after checkout."""
    class Config:
        extra = "forbid"
    
    order_id: str
    payment_status: Optional[str] = None
    payment_reference: Optional[str] = None
    authorization_url: Optional[str] = None


# Shipping response data schemas
class ShippingZonesData(BaseModel):
    """Data returned for shipping zones."""
    class Config:
        extra = "forbid"
    
    zones: List[ShippingZoneData]


# Inventory response data schemas
class InventoryData(BaseModel):
    """Data returned for inventory information."""
    class Config:
        extra = "forbid"
    
    inventory: InventoryInfo


# Revamp response data schemas
class RevampRequestData(BaseModel):
    """Data returned after revamp request creation."""
    class Config:
        extra = "forbid"
    
    revamp: RevampRequestDataModel


class RevampStatusData(BaseModel):
    """Data returned for revamp status."""
    class Config:
        extra = "forbid"
    
    revamp: RevampRequestDataModel


# CRM response data schemas
class RatingData(BaseModel):
    """Data returned after rating creation."""
    class Config:
        extra = "forbid"
    
    rating: RatingDataModel


# Stats response data schemas
class StatsData(BaseModel):
    """Data returned for user statistics."""
    class Config:
        extra = "forbid"
    
    stats: Dict[str, Any]  # Stats can be flexible, so keeping as dict


# Admin response data schemas
class UserListData(BaseModel):
    """Data returned for user list."""
    class Config:
        extra = "forbid"
    
    users: List[UserDataModel]
    total: int
    page: int
    per_page: int
    total_pages: int


class UserData(BaseModel):
    """Data returned for single user."""
    class Config:
        extra = "forbid"
    
    user: UserDataModel


class RoleAssignmentData(BaseModel):
    """Data returned after role assignment."""
    class Config:
        extra = "forbid"
    
    user: UserDataModel
    role: str


class ProductCreateData(BaseModel):
    """Data returned after product creation."""
    class Config:
        extra = "forbid"
    
    product: ProductDataModel


class ProductVariantData(BaseModel):
    """Data returned for product variant operations."""
    class Config:
        extra = "forbid"
    
    variant: ProductVariantDataModel


class InventoryAdjustData(BaseModel):
    """Data returned after inventory adjustment."""
    class Config:
        extra = "forbid"
    
    inventory: InventoryInfo


class OrderStatusUpdateData(BaseModel):
    """Data returned after order status update."""
    class Config:
        extra = "forbid"
    
    order: OrderDataModel


class B2BInquiryStatusData(BaseModel):
    """Data returned after B2B inquiry status update."""
    class Config:
        extra = "forbid"
    
    inquiry: B2BInquiryDataModel


class LoyaltyAdjustData(BaseModel):
    """Data returned after loyalty points adjustment."""
    class Config:
        extra = "forbid"
    
    loyalty: LoyaltyAccountData


class CmsPageCreateData(BaseModel):
    """Data returned after CMS page creation."""
    class Config:
        extra = "forbid"
    
    page: CmsPageDataModel


class CmsPageUpdateData(BaseModel):
    """Data returned after CMS page update."""
    class Config:
        extra = "forbid"
    
    page: CmsPageDataModel


class StaffCreateData(BaseModel):
    """Data returned after staff creation."""
    class Config:
        extra = "forbid"
    
    staff: StaffDataModel


class RevampStatusUpdateData(BaseModel):
    """Data returned after revamp status update."""
    class Config:
        extra = "forbid"
    
    revamp: RevampRequestDataModel


class CrmRatingsListData(BaseModel):
    """Data returned for CRM ratings list."""
    class Config:
        extra = "forbid"
    
    ratings: List[RatingDataModel]
    total: int
    page: int
    per_page: int
    total_pages: int


# Admin list response data schemas
class CmsPageListData(BaseModel):
    """Data returned for CMS page list."""
    class Config:
        extra = "forbid"
    
    pages: List[CmsPageDataModel]
    total: int
    page: int
    per_page: int
    total_pages: int


class B2BInquiryListData(BaseModel):
    """Data returned for B2B inquiry list."""
    class Config:
        extra = "forbid"
    
    inquiries: List[B2BInquiryDataModel]
    total: int
    page: int
    per_page: int
    total_pages: int


class LoyaltyAccountListData(BaseModel):
    """Data returned for loyalty account list."""
    class Config:
        extra = "forbid"
    
    accounts: List[LoyaltyAccountData]
    total: int
    page: int
    per_page: int
    total_pages: int


class RevampRequestListData(BaseModel):
    """Data returned for revamp request list."""
    class Config:
        extra = "forbid"
    
    revamps: List[RevampRequestDataModel]
    total: int
    page: int
    per_page: int
    total_pages: int


class StaffListData(BaseModel):
    """Data returned for staff list."""
    class Config:
        extra = "forbid"
    
    staff: List[StaffDataModel]
    total: int
    page: int
    per_page: int
    total_pages: int


class InventoryListData(BaseModel):
    """Data returned for inventory list."""
    class Config:
        extra = "forbid"
    
    inventory: List[InventoryInfo]
    total: int
    page: int
    per_page: int
    total_pages: int

class ApiVersionDataModel(BaseModel):
    name: str
    version: str
    env: str