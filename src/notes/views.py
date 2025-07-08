from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import Http404
from .forms import NoteForm
from .models import NoteInterne, NoteReception
from logs.utils import enregistrer_action  

@login_required
def send_note(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.expediteur = request.user
            note.save()
            form.save_m2m()  # pour les destinataires

            # Création d'une NoteReception pour chaque destinataire
            for destinataire in note.destinataires.all():
                NoteReception.objects.get_or_create(note=note, destinataire=destinataire)

            messages.success(request, "✅ Note envoyée avec succès.")
            enregistrer_action(request.user, 'ENVOI_NOTE', f"Note envoyée à {note.destinataires.count()} utilisateur(s)")
            return redirect('inbox')  
        else:
            messages.error(request, "⚠️ Erreur dans le formulaire.")
    else:
        form = NoteForm()
    
    return render(request, 'notes/envoyer_note.html', {'form': form})



@login_required
def inbox(request):
    notes_receptions = NoteReception.objects.select_related('note', 'note__expediteur') \
        .filter(destinataire=request.user, est_archivee=False) \
        .order_by('-note__niveau_urgence', '-note__date_creation')

    return render(request, 'notes/inbox.html', {
        'notes_receptions': notes_receptions
    })


@login_required
def note_detail(request, note_id):
    try:
        reception = NoteReception.objects.select_related('note', 'note__expediteur') \
            .get(note__id=note_id, destinataire=request.user)
    except NoteReception.DoesNotExist:
        raise Http404("Note introuvable ou accès non autorisé.")

    # Marquer comme lue si non lue
    if not reception.est_lue:
        reception.est_lue = True
        reception.save()

    note = reception.note

    return render(request, 'notes/note_detail.html', {
        'note': note,
        'reception': reception
    })

@login_required
@require_POST
def archiver_note(request, note_id):
    try:
        reception = NoteReception.objects.get(note__id=note_id, destinataire=request.user)
        reception.est_archivee = True
        reception.save()
        messages.success(request, "🗃️ La note a bien été archivée.")
    except NoteReception.DoesNotExist:
        messages.error(request, "❌ Impossible d’archiver cette note.")

    return redirect('inbox')