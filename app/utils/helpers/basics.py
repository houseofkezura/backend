import re, random, string, logging, time
from typing import Any, Dict, List, Union, Optional
from flask import current_app, abort, request, url_for
from slugify import slugify


def paginate_results(request, results, result_per_page=10):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * result_per_page
    end = start + result_per_page

    the_results = [result.to_dict() for result in results]
    current_results = the_results[start:end]

    return current_results


def url_parts(url):
    """
    Splits a URL into its constituent parts.

    Args:
        url (str): The URL to split.

    Returns:
        list: A list of strings representing the parts of the URL.
    """
    
    the_url_parts = url.split('/')
    
    return the_url_parts


def get_or_404(query):
    """
    Executes a query and returns the result, or aborts with a 404 error if no result is found.

    Args:
        query (sqlalchemy.orm.query.Query): The SQLAlchemy query to execute.

    Returns:
        sqlalchemy.orm.query.Query: The result of the query.

    Raises:
        werkzeug.exceptions.NotFound: If the query returns no result.
    """
    
    result = query.one_or_none()
    if result is None:
        abort(404)
    
    return result


def int_or_none(s):
    """
    Converts a string to an integer, or returns None if the string cannot be converted.

    Args:
        s (str): The string to convert.

    Returns:
        int or None: The converted integer, or None if conversion is not possible.
    """
    
    try:
        return int(s)
    except:
        return None


def normalize_keys(data: Union[Dict[str, Any], List[Any], Any]) -> Union[Dict[str, Any], List[Any], Any]:
    """
    Recursively normalizes keys in a dictionary or list to snake_case.

    Args:
        data (Union[Dict[str, Any], List[Any], Any]): The input data to normalize. 
            Can be a dictionary, list, or any other type.

    Returns:
        Union[Dict[str, Any], List[Any], Any]: The normalized data with keys in snake_case.
            If the input is not a dictionary or list, it is returned as-is.

    Example:
        >>> payload = {"firstName": "John", "lastName": "Doe", "address": {"streetAddress": "123 Main St"}}
        >>> normalize_keys(payload)
        {'first_name': 'John', 'last_name': 'Doe', 'address': {'street_address': '123 Main St'}}
    """
    if isinstance(data, dict):
        normalized: Dict[str, Any] = {}
        for key, value in data.items():
            # Convert camelCase to snake_case
            normalized_key = re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower()
            normalized[normalized_key] = normalize_keys(value)
        return normalized
    elif isinstance(data, list):
        return [normalize_keys(item) for item in data]
    else:
        return data


def generate_random_string(length: int = 8, prefix: str = '', lowercase: bool = False) -> str:
    """
    Generates a random string of specified length, consisting of letters and digits.
    If a prefix is provided, it is prepended to the random string.
    
    Args:
        length (int): The desired length of the random part of the string.
        prefix (str, optional): An optional prefix to prepend to the random string.
        lowercase (bool, optional): Whether to use only lowercase characters. Defaults to False.

    Returns:
        str: A string that starts with the prefix (if provided) followed by 'length' random characters.

    """
    characters = string.ascii_lowercase + string.digits if lowercase else string.ascii_letters + string.digits
    random_part = ''.join(random.choice(characters) for _ in range(length))
    
    return f"{prefix}-{random_part}" if prefix else random_part


def generate_random_number(length: int = 6) -> int:
    """Generates a random number of the specified length.

    Args:
        length: The desired length of the random number.

    Returns:
        A string representing the generated random number.
    """

    if length < 1:
        raise ValueError("Length must be greater than 0")

    rand_num = random.randint(10**(length-1), 10**length - 1)
    
    return rand_num


from typing import Protocol, runtime_checkable

@runtime_checkable
class HasQueryProtocol(Protocol):
    query: Any


def generate_slug(name: str, model: HasQueryProtocol, existing_obj=None) -> str:
    """
    Generates a unique slug for a given name based on the type of db model.

    Parameters:
    name (str): The name to generate a slug for.
    model (db): The type of db model to generate a slug for.
    existing_obj (object): (Optional) The existing object to compare against to ensure uniqueness.
    

    Returns:
    str: The unique slug for the given name.

    Usage:
    Call this function passing in the name and db model you want to generate a slug for. 
    Optionally, you can pass in an existing object to compare against to ensure uniqueness.
    """
    base_slug = slugify(name)
    slug = base_slug
    timestamp = str(int(time.time() * 1000))
    counter = 1
    max_attempts = 4  # maximum number of attempts to create a unique slug
    
    # when updating, Check existing obj name is the same
    if existing_obj:
        if existing_obj.name == name:
            return existing_obj.slug

    
    # Check if slug already exists in database
    is_obj = model.query.filter_by(slug=slug).first()
    
    while is_obj:
        if counter > max_attempts:
            raise ValueError(f"Unable to create a unique slug after {max_attempts} attempts.")
        
        suffix = generate_random_string(5)
        slug = f"{base_slug}-{suffix}-{timestamp}" if counter == 2 else f"{base_slug}-{suffix}"

        # Check if the combination of slug and suffix is also taken
        # Use the helper function with the dynamically determined model type
        is_obj = model.query.filter_by(slug=slug).first()
        
        counter += 1

    return slug


def get_object_by_slug(model: HasQueryProtocol, slug: str):
    """
    Retrieve an object from the database based on its unique slug.

    Parameters:
    - model (db.Model): The SQLAlchemy model class representing the database table.
    - slug (str): The unique slug used to identify the object.

    Returns:
    db.Model or None: The object with the specified slug if found, or None if not found.

    Usage:
    Call this function with the model class and the slug of the object you want to retrieve.
    Returns the object if found, or None if no matching object is present in the database.
    """
    return model.query.filter_by(slug=slug).first()


def redirect_url(default='admin.index'):
    return request.args.get('next') or request.referrer or \
        url_for(default)


def parse_bool(value: Optional[str]) -> bool:
    """Parse a string value to boolean."""
    return str(value).lower() in ("true", "1", "yes") if value else False

