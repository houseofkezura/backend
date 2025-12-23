"""
Author: Emmanuel Olowu
Link: https://github.com/zeddyemy
Copyright: © 2024 Emmanuel Olowu <zeddyemy@gmail.com>
License: GNU, see LICENSE for more details.
Package: StoreZed
"""
from sqlalchemy import inspect, or_
from sqlalchemy.orm import backref
from sqlalchemy.orm import Query
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.extensions import db
from quas_utils.date_time import QuasDateTime, to_gmt1_or_none
from .media import Media
from .product import Product, product_categories

class ProductCategory(db.Model):
    __tablename__ = "product_category"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = db.Column(db.String(50), nullable=False)
    alias = db.Column(db.String(50), nullable=True)
    description  = db.Column(db.String(200), nullable=True)
    slug = db.Column(db.String(80), nullable=False, unique=True)
    date_created = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    
    media_id = db.Column(UUID(as_uuid=True), db.ForeignKey("media.id", ondelete="CASCADE"), nullable=True)
    parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey("product_category.id"), nullable=True)  
    children = db.relationship("ProductCategory", backref=backref("parent", remote_side=[id]), lazy=True)
    
        
    def __repr__(self):
        return f"<ProdCat ID: {self.id}, name: {self.name}, parent: {self.parent_id}>"
    
    @staticmethod
    def add_search_filters(query: Query, search_term: str) -> Query:
        """
        Adds search filters to a SQLAlchemy query.
        """
        if search_term:
            search_term = f"%{search_term}%"
            query = query.filter(
                    or_(
                        ProductCategory.name.ilike(search_term),
                        ProductCategory.slug.ilike(search_term),
                    )
                )
        return query
    
    @classmethod
    def create_category(cls, name, slug, description="", media_id=None, commit=True, **kwargs):
        category = cls(name=name, description=description, slug=slug, media_id=media_id, **kwargs)
        
        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(category, key, value)
        
        db.session.add(category)
        
        if commit:
            db.session.commit()
        
        return category
    
    def get_thumbnail(self):
        media: Media = Media.query.get(self.media_id)
        return media.get_path() if media else None
    
    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self, commit=True, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        if commit:
            db.session.commit()

    def delete(self, commit=True):
        db.session.delete(self)
        
        if commit:
            db.session.commit()
    
    def to_dict(self, include_children=False) -> dict[str, any]:
        data = {
            "id": self.id,
            "name": self.name,
            "alias": self.alias,
            "description": self.description,
            "slug": self.slug,
            "parent_id": self.parent_id
            }
        if include_children:
            data["children"] = [child.to_dict() for child in self.children]
        return data

