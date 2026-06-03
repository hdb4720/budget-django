from django.db import transaction
from django.core.exceptions import ValidationError
from budget.models import Account


from django.db import transaction
from budget.models import Account

def resolve_account(name: str) -> Account:
    """
    Return an Account object for the given name.
    Create the account with safe defaults if it does not exist.
    """
    name = name.strip()
    if not name:
        raise ValueError("Account name is empty")

    with transaction.atomic():
        account, created = Account.objects.get_or_create(
            name=name,
            defaults={
                "short_name": name[:20],
                "institution": "",
                "type": "UNKNOWN",
                "opening_balance": 0,
                "notes": "",
            }
        )
        return account
