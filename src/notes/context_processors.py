# notes/context_processors.py

from .models import NoteReception

def notes_non_lues(request):
    if request.user.is_authenticated:
        count = NoteReception.objects.filter(destinataire=request.user, est_lue=False).count()
    else:
        count = 0
    return {'notes_non_lues': count}
