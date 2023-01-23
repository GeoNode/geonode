import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class NumberValidator(object):
    def __init__(self, min_digits=0):
        self.min_digits = min_digits

    def validate(self, password, user=None):
        if not len(re.findall(r"\d", password)) >= self.min_digits:
            raise ValidationError(
                _(f"The password must contain at least" f"{self.min_digits} digit(s), 0-9."),
                code="password_no_number",
                params={"min_digits": self.min_digits},
            )

    def get_help_text(self):
        return _(f"Your password must contain at least" f"{self.min_digits} digit(s), 0-9.")


class UppercaseValidator(object):
    def validate(self, password, user=None):
        if not re.findall(r"[A-Z]", password):
            raise ValidationError(
                _(
                    "The password must contain at least \
                    1 uppercase letter, A-Z."
                ),
                code="password_no_upper",
            )

    def get_help_text(self):
        return _("Your password must contain at least 1 uppercase letter, A-Z.")


class LowercaseValidator:
    def validate(self, password, user=None):
        if not re.findall(r"[a-z]", password):
            raise ValidationError(
                _(
                    "The password must contain at least \
                    1 lowercase letter, a-z."
                ),
                code="password_no_lower",
            )

    def get_help_text(self):
        return _("Your password must contain at least 1 lowercase letter, a-z.")


class SpecialCharsValidator(object):
    def validate(self, password, user=None):
        if not re.findall(r"""[@#$%^&*()+=`{}:";'<>?,./\[\]]""", password):
            raise ValidationError(
                _(
                    """The password must contain at least \
                    1 symbol, @#$%^&*()[]{}+=`:";'<>?,./."""
                ),
                code="password_no_upper",
            )

    def get_help_text(self):
        return _(
            """Your password must contain at least \
                1 symbol, @#$%^&*()[]{}+=`:";'<>?,./."""
        )
