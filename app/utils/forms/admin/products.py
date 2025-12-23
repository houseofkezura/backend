"""
Product forms for admin web interface.
"""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, HiddenField, 
    SelectMultipleField, DecimalField, ValidationError, widgets
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from flask_wtf.file import FileField, FileAllowed

from app.utils.helpers.category import get_category_choices
from app.models.category import ProductCategory
from app.enums.products import LaunchStatus


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select field that displays as a list of checkboxes.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class ProductForm(FlaskForm):
    """
    Form for creating/editing products.
    Matches the Product model structure.
    """
    # Basic Information
    name = StringField(
        'Product Name',
        validators=[DataRequired(), Length(min=1, max=255)],
        description="Enter the product name"
    )
    
    sku = StringField(
        'SKU',
        validators=[Optional(), Length(max=100)],
        description="Leave blank to auto-generate"
    )
    
    slug = StringField(
        'Slug',
        validators=[Optional(), Length(max=255)],
        description="URL-friendly identifier (auto-generated if blank)"
    )
    
    description = TextAreaField(
        'Description',
        validators=[Optional()],
        description="Product description"
    )
    
    # Category
    category_id = SelectField(
        'Category',
        choices=[],
        validators=[DataRequired()],
        validate_choice=False,
        coerce=str,  # Coerce to string to handle UUIDs
        description="Select a product category"
    )
    
    # Product Details
    care = TextAreaField(
        'Care Instructions',
        validators=[Optional()],
        description="Product care instructions"
    )
    
    details = TextAreaField(
        'Product Details',
        validators=[Optional()],
        description="Additional product details"
    )
    
    material = StringField(
        'Material',
        validators=[Optional(), Length(max=255)],
        description="Product material"
    )
    
    # SEO Fields
    meta_title = StringField(
        'Meta Title',
        validators=[Optional(), Length(max=255)],
        description="SEO meta title"
    )
    
    meta_description = TextAreaField(
        'Meta Description',
        validators=[Optional()],
        description="SEO meta description"
    )
    
    meta_keywords = StringField(
        'Meta Keywords',
        validators=[Optional(), Length(max=500)],
        description="SEO keywords (comma-separated)"
    )
    
    # Status
    launch_status = SelectField(
        'Status',
        choices=[
            (status.value, status.value) for status in LaunchStatus
        ],
        validators=[Optional()],
        default=LaunchStatus.IN_STOCK.value,
        description="Product availability status"
    )
    
    # Categories (for many-to-many relationship)
    categories = MultiCheckboxField(
        'Additional Categories',
        choices=[],
        validators=[Optional()],
        validate_choice=False,
        description="Select additional categories (optional)"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate category choices
        self.category_id.choices = get_category_choices()
        # For multi-select categories
        all_categories = get_category_choices()
        # Remove the empty option for multi-select
        self.categories.choices = [c for c in all_categories if c[0]]  # Remove empty option
    
    def validate_sku(self, field):
        """Validate SKU uniqueness."""
        if field.data:
            from app.models.product import Product
            existing = Product.query.filter_by(sku=field.data).first()
            if existing and (not hasattr(self, 'product_id') or existing.id != self.product_id):
                raise ValidationError('SKU already exists')
    
    def validate_slug(self, field):
        """Validate slug uniqueness."""
        if field.data:
            from app.models.product import Product
            existing = Product.query.filter_by(slug=field.data).first()
            if existing and (not hasattr(self, 'product_id') or existing.id != self.product_id):
                raise ValidationError('Slug already exists')


# Legacy alias for backward compatibility
AddProductForm = ProductForm


def generate_category_field(format='checkbox', sel_cats=None, indent_level=0):
    categories: list[ProductCategory] = ProductCategory.query.filter(ProductCategory.parent_id == None).order_by(ProductCategory.name).all()
    
    if sel_cats is None:
        sel_cats = []

    def generate_child(category_children: list[ProductCategory], the_indent_level: int = 0):
        html = ''
        if format == 'checkbox':
            html = '<ul class="is-child">\n'
            for category in category_children:
                is_checked = category in sel_cats
                category_id = f"categories-{category.id}"
                data_parent = f"data-parent={category.parent_id if category.parent_id else ''}"
                html += f'    <li data-category={category.id}>\n' \
                            f'        <input id="{category_id}" name="categories" ' \
                            f'type="checkbox" value="{category.id}" {"checked" if is_checked else ""} {data_parent}> ' \
                            f'<label for="{category_id}">{category.name}</label>\n'
                child_html = generate_child(category.children)
                if child_html:
                    html += f'        {child_html}\n'
                html += '    </li>\n'
            html += '</ul>'
        
        elif format == 'select':
            for category in category_children:
                optionIndent = '&nbsp' * the_indent_level
                html += f'    <option value="{category.id}">{optionIndent}{category.name}</option>\n'
                child_html = generate_child(category.children, the_indent_level + 3)
                if child_html:
                    html += f'        {child_html}\n'
            
        return html
        
    # Generate the HTML field
    html = ''
    if format == 'checkbox':
        html = '<ul class="form-control form-checkbox list-view h-fit min-h-[40px] max-h-[300px] border border-outline-clr rounded-lg shadow-sm-light w-full p-2.5 overflow-y-scroll" id="categories" data-category-checkboxes>\n'
        for category in categories:
            is_checked = category in sel_cats
            category_id = f"categories-{category.id}"
            data_parent = f"data-parent={category.parent_id if category.parent_id else ''}"
            html += f'    <li data-category={category.id}>\n' \
                    f'        <input id="{category_id}" name="categories" ' \
                    f'type="checkbox" value="{category.id}" {"checked" if is_checked else ""} {data_parent}> ' \
                    f'<label for="{category_id}">{category.name}</label>\n'
            child_html = generate_child(category.children)
            if child_html:
                html += f'        {child_html}\n'
            html += '    </li>\n'
        html += '</ul>'

    elif format == 'select':
        html = '<select class="form-control text-sm rounded-lg shadow-sm-light border border-outline-clr focus:ring-theme-clr focus:border-theme-clr block w-full p-2.5 placeholder-gray-400 outline-none bg-gray-50 text-gray-900" id="parent-cat" name="parent_cat" data-parent-select>\n'
        html += '    <option value="">— Parent category —</option>\n'

        for category in categories:
            html += f'    <option value="{category.id}">{category.name}</option>\n'
            child_html = generate_child(category.children, indent_level + 3)
            if child_html:
                html += f'    {child_html}\n'

        html += '</select>'

    return html
