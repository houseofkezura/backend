from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional, Length
from flask_wtf.file import FileField, FileAllowed
from app.utils.helpers.category import get_category_choices

class CategoryForm(FlaskForm):
    """
    Form for creating/editing product categories.
    """
    name = StringField(
        'Category Name',
        validators=[DataRequired(), Length(min=1, max=100)],
        description="Enter category name"
    )
    
    slug = StringField(
        'Slug',
        validators=[Optional(), Length(max=100)],
        description="URL-friendly version of the name (auto-generated if empty)"
    )
    
    description = TextAreaField(
        'Description',
        validators=[Optional()],
        description="Category description"
    )
    
    parent_id = SelectField(
        'Parent Category',
        validators=[Optional()],
        coerce=str,
        description="Select a parent category (optional)"
    )
    
    cat_img = FileField(
        'Category Image',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')
        ],
        description="Upload category image"
    )

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        # Populate parent choices
        # We need to filter out the current category itself if we are editing (to avoid loops)
        # But this logic might be better placed in the route or helper
        choices = get_category_choices()
        self.parent_id.choices = [("", "No Parent")] + choices
