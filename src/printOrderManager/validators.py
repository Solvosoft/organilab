# Import for the validations
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.core.validators import URLValidator
from django.core.validators import RegexValidator

# Validator for the Login and Register Print Form
# Creating my own validations


def validate_email(value):
    email_validator = EmailValidator()
    try:
        email_validator(value)
    except:
        raise ValidationError("Invalid email, please enter a valid email")
    return value
