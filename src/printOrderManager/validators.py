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


#    def clean_email(self):
#        email = self.cleaned_data['email']
#       logging.error("Error "+email)
#        email_validator = EmailValidator()
#        try:
#            email_validator(email)
#        except:
#            raise forms.ValidationError(
#                "Invalid email, please enter a valid email")
#        return email
#    def clean_email(self):
#        if (self.cleaned_data.get('email', '')
#                .endswith('gmail.com')):
#            raise ValidationError(
#                "Invalid email address."+self.cleaned_data.get('location', ''))
#
#        return self.cleaned_data.get('email', '')
