"""
This package contains the database models for the Flask application.

Each model corresponds to a table in the database.

Author: Emmanuel Olowu
Link: https://github.com/zeddyemy
Copyright: © 2024 Emmanuel Olowu <zeddyemy@gmail.com>
"""
from flask import Flask
from sqlalchemy.orm import aliased

from .user import AppUser, Profile, Address, TempUser
from .role import Role, UserRole
from .media import Media

from .wallet import Wallet
from .payment import Payment, Transaction
from .subscription import Subscription, SubscriptionPlan
from .order import Order, OrderItem, Shipment
from .product import Product, ProductVariant, Inventory
from .cart import Cart, CartItem
from .crm import CrmStaff, CrmRating
from .loyalty import LoyaltyAccount, LoyaltyLedger
from .cms import CmsPage, B2BInquiry
from .audit import AuditLog
