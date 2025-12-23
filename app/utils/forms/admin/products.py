"""
Author: Emmanuel Olowu
Link: https://github.com/zeddyemy
Copyright: © 2024 Emmanuel Olowu <zeddyemy@gmail.com>
License: GNU, see LICENSE for more details.
Package: StoreZed
"""
from wsgiref.validate import validator
from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, TextAreaField, SelectField, HiddenField, SelectMultipleField, ValidationError, widgets)
from wtforms.validators import DataRequired, Optional
from flask_wtf.file import FileField, FileAllowed

from app.utils.helpers.category import get_category_choices
from app.models.category import ProductCategory

# class to change the way SelectMultipleField
# is rendered by jinja
class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


size_choices = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '2XL', '3XL', '4XL',]

class AddProductForm(FlaskForm):
    """ form to add new product """
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    selling_price = IntegerField('Selling Price', validators=[DataRequired()])
    actual_price = IntegerField('Actual Price', validators=[Optional()])
    
    global size_choices
    select_available_sizes = MultiCheckboxField('Sizes', choices=size_choices, validators=[Optional()])
    
    colors = StringField('Colors', validators=[Optional()])
    product_category = SelectField('Product Category', choices=[], validate_choice=False)
    product_img = FileField('Product Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')])
    product_tags = HiddenField('product Tags')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_category.choices = get_category_choices()


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
