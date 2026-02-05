from __future__ import annotations
from typing import Optional, List
from sqlalchemy.orm import Query
from flask_sqlalchemy.pagination import Pagination
from flask import request
from sqlalchemy import desc

from app.models.order import Order
from app.extensions import db
from app.logging import log_error

def fetch_all_orders(
        page_num: Optional[int] = None,
        per_page: Optional[int] = None,
        paginate: bool = False,
        status: Optional[str] = None,
        search_term: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Order] | Pagination:
    ''' Get orders from the database with optional filtering and pagination.
    
    Args:
        page_num: Page number for pagination
        per_page: Items per page
        paginate: Return pagination object when True
        status: Filter by order status
        search_term: Search in order number, guest email, or user email
        user_id: Filter by user ID

    Returns:
        Pagination object or list of Order instances
    '''
    
    # Get parameters from request if not provided
    if page_num is None:
        page_num = request.args.get("page", 1, type=int)
    
    if per_page is None:
        per_page = request.args.get("per_page", 20, type=int) # Default to 20 for orders
    
    if status is None:
        status = request.args.get("status", "").strip()
        
    if search_term is None:
        search_term = request.args.get("search", "").strip()

    query: Query = Order.query
    
    # Apply filters
    if status:
        query = query.filter(Order.status == status)
        
    if user_id:
        query = query.filter(Order.user_id == user_id)
    
    if search_term:
        term = f"%{search_term}%"
        # Search in order number, guest email, and related user's email
        from app.models.user import AppUser
        query = query.outerjoin(AppUser).filter(
            (Order.order_number.ilike(term)) |
            (Order.guest_email.ilike(term)) |
            (AppUser.email.ilike(term)) | 
            (AppUser.first_name.ilike(term)) |
            (AppUser.last_name.ilike(term))
        )

    # Apply consistent ordering (newest first)
    query = query.order_by(Order.created_at.desc())
    
    # Execute query with/without pagination
    if paginate:
        pagination = query.paginate(page=page_num, per_page=per_page, error_out=False)
        return pagination
    
    return query.all()

def fetch_order(identifier: str) -> Optional[Order]:
    """
    Fetch a single order by ID or Order Number.
    """
    if not identifier:
        return None
        
    order = None
    try:
        # Try as UUID first
        order = Order.query.filter_by(id=identifier).first()
    except Exception:
        pass
        
    if not order:
        # Try as order number
        order = Order.query.filter_by(order_number=identifier).first()
        
    return order
