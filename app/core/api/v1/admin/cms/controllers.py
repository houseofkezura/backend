"""
Admin CMS controller.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.cms import CmsPage
from app.utils.helpers.api_response import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class AdminCmsController:
    """Controller for admin CMS endpoints."""

    @staticmethod
    def list_pages() -> Response:
        """List all CMS pages."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            published = request.args.get('published', type=bool)
            
            query = CmsPage.query
            
            if published is not None:
                query = query.filter_by(published=published)
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            pages = [p.to_dict() for p in pagination.items]
            
            return success_response(
                "CMS pages retrieved successfully",
                200,
                {
                    "pages": pages,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list CMS pages", error=e)
            return error_response("Failed to retrieve CMS pages", 500)

    @staticmethod
    def create_page() -> Response:
        """Create a new CMS page."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            from app.schemas.admin import CmsPageCreateRequest
            payload = CmsPageCreateRequest.model_validate(request.get_json() or {})
            
            # Check if slug exists
            existing = CmsPage.query.filter_by(slug=payload.slug).first()
            if existing:
                return error_response("Page with this slug already exists", 409)
            
            page = CmsPage()
            page.slug = payload.slug
            page.title = payload.title
            page.content = payload.content
            page.published = payload.published
            if payload.published:
                from app.utils.date_time import DateTimeUtils
                page.published_at = DateTimeUtils.aware_utcnow()
            
            db.session.add(page)
            db.session.commit()
            
            log_event(f"CMS page created: {slug} by admin {current_user.id}")
            
            return success_response(
                "CMS page created successfully",
                201,
                {"page": page.to_dict()}
            )
        except Exception as e:
            log_error("Failed to create CMS page", error=e)
            db.session.rollback()
            return error_response("Failed to create CMS page", 500)

    @staticmethod
    def update_page(page_id: str) -> Response:
        """Update a CMS page."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                page_uuid = uuid.UUID(page_id)
            except ValueError:
                return error_response("Invalid page ID format", 400)
            
            page = CmsPage.query.get(page_uuid)
            if not page:
                return error_response("CMS page not found", 404)
            
            from app.schemas.admin import CmsPageUpdateRequest
            payload = CmsPageUpdateRequest.model_validate(request.get_json() or {})
            
            if payload.slug is not None:
                # Check slug uniqueness
                existing = CmsPage.query.filter_by(slug=payload.slug).filter(CmsPage.id != page_uuid).first()
                if existing:
                    return error_response("Slug already in use", 409)
                page.slug = payload.slug
            if payload.title is not None:
                page.title = payload.title
            if payload.content is not None:
                page.content = payload.content
            if payload.published is not None:
                page.published = payload.published
                if payload.published and not page.published_at:
                    from app.utils.date_time import DateTimeUtils
                    page.published_at = DateTimeUtils.aware_utcnow()
            
            db.session.commit()
            
            log_event(f"CMS page updated: {page_id} by admin {current_user.id}")
            
            return success_response(
                "CMS page updated successfully",
                200,
                {"page": page.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to update CMS page {page_id}", error=e)
            db.session.rollback()
            return error_response("Failed to update CMS page", 500)

    @staticmethod
    def delete_page(page_id: str) -> Response:
        """Delete a CMS page."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                page_uuid = uuid.UUID(page_id)
            except ValueError:
                return error_response("Invalid page ID format", 400)
            
            page = CmsPage.query.get(page_uuid)
            if not page:
                return error_response("CMS page not found", 404)
            
            db.session.delete(page)
            db.session.commit()
            
            log_event(f"CMS page deleted: {page_id} by admin {current_user.id}")
            
            return success_response("CMS page deleted successfully", 200)
        except Exception as e:
            log_error(f"Failed to delete CMS page {page_id}", error=e)
            db.session.rollback()
            return error_response("Failed to delete CMS page", 500)

