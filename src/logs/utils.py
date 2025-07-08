
from .models import JournalAction

def enregistrer_action(user, action, description=""):
    JournalAction.objects.create(
        user=user,
        action=action,
        description=description
    )
