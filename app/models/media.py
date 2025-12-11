"""
Media model for file management for events.

This module defines the Media model that represents uploaded files (images, videos, documents)
belonging to events. Media includes metadata, optimization, and relationships to content.

Author: Emmanuel Olowu
Link: https://github.com/zeddyemy
Package: EventSphere
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped as M, relationship

from app.extensions import db
from quas_utils.date_time import QuasDateTime


class Media(db.Model):
    """Model for media files within Events."""

    __tablename__ = 'media'

    # Primary key
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)    

    # File Information
    filename: M[str] = db.Column(db.String(255), nullable=False)
    original_filename: M[str] = db.Column(db.String(255), nullable=False)
    file_path: M[str] = db.Column(db.String(500), nullable=False)
    file_url: M[str] = db.Column(db.String(500), nullable=False)
    thumbnail_url: M[Optional[str]] = db.Column(db.String(500))

    # File Metadata
    file_size: M[int] = db.Column(db.Integer, nullable=False)  # bytes
    file_type: M[str] = db.Column(db.String(50), nullable=False)  # image, video, document
    mime_type: M[str] = db.Column(db.String(100), nullable=False)
    file_extension: M[str] = db.Column(db.String(10), nullable=False)

    # Image/Video specific metadata
    width: M[Optional[int]] = db.Column(db.Integer)
    height: M[Optional[int]] = db.Column(db.Integer)
    duration: M[Optional[float]] = db.Column(db.Float())  # for videos

    # Cloudinary specific
    cloudinary_public_id: M[str] = db.Column(db.String(200), nullable=False, unique=True)
    cloudinary_folder: M[str] = db.Column(db.String(200), nullable=False)

    # Optimization metadata
    optimized_versions: M[Dict[str, str]] = db.Column(db.JSON, default=dict, comment="URLs for different optimized versions (thumbnail, medium, large)")

    # Usage tracking
    is_featured: M[bool] = db.Column(db.Boolean(), default=False)
    usage_count: M[int] = db.Column(db.Integer, default=0)

    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, index=True)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)

    # Relationships

    def __repr__(self) -> str:
        return f"<Media {self.id}, {self.filename} ({self.file_type})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert media instance to dictionary representation."""
        return {
            'id': str(self.id),
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_url': self.file_url,
            'thumbnail_url': self.thumbnail_url,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'file_extension': self.file_extension,
            'width': self.width,
            'height': self.height,
            'duration': self.duration,
            'cloudinary_public_id': self.cloudinary_public_id,
            'cloudinary_folder': self.cloudinary_folder,
            'optimized_versions': self.optimized_versions,
            'is_featured': self.is_featured,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def aspect_ratio(self) -> Optional[float]:
        """Calculate aspect ratio if dimensions are available."""
        if self.width and self.height and self.height > 0:
            return self.width / self.height
        return None

    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024)

    def increment_usage(self) -> None:
        """Increment usage count."""
        self.usage_count += 1
        db.session.commit()

    def mark_featured(self, featured: bool = True) -> None:
        """Mark or un-mark media as featured."""
        self.is_featured = featured
        db.session.commit()

    def get_path(self) -> str:
        """Get the public URL path for the media file."""
        return self.file_url or ""

    @staticmethod
    def get_event_media(
        event_id: uuid.UUID,
        file_type: Optional[str] = None,
        include_featured: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List["Media"]:
        """Get media for a specific Event with optional filters."""
        query = Media.query.filter_by(event_id=event_id)

        if file_type:
            query = query.filter_by(file_type=file_type)

        if include_featured is not None:
            query = query.filter_by(is_featured=include_featured)

        query = query.order_by(Media.created_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    @staticmethod
    def search_event_media(
        event_id: uuid.UUID,
        search_term: str,
        file_type: Optional[str] = None
    ) -> List["Media"]:
        """Search media within a Event."""
        from sqlalchemy import or_, and_

        query = Media.query.filter(
            and_(
                Media.event_id == event_id,
                or_(
                    Media.filename.ilike(f'%{search_term}%'),
                    Media.original_filename.ilike(f'%{search_term}%')
                )
            )
        )

        if file_type:
            query = query.filter_by(file_type=file_type)

        return query.order_by(Media.created_at.desc()).all()