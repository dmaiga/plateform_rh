from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import Http404
from django.utils import timezone
from .forms import NoteForm
from .models import NoteInterne, NoteReception
from logs.utils import enregistrer_action  

from django.http import JsonResponse



def get_unread_notes_count(user):
    return NoteReception.objects.filter(destinataire=user, est_lue=False).count()


@login_required
def note_envoyee_detail(request, note_id):
    note = get_object_or_404(NoteInterne, id=note_id, expediteur=request.user)
    receptions = note.receptions.select_related('destinataire')

    return render(request, 'notes/note_envoyee_detail.html', {
        'note': note,
        'receptions': receptions
    })

@login_required
def sent_notes(request):
    notes_envoyees = NoteInterne.objects.filter(expediteur=request.user) \
        .prefetch_related('destinataires') \
        .order_by('-date_creation')

    return render(request, 'notes/sent_notes.html', {
        'notes_envoyees': notes_envoyees
    })


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
    reception = get_object_or_404(
        NoteReception.objects.select_related('note', 'note__expediteur'),
        note__id=note_id,
        destinataire=request.user
    )

    if not reception.est_lue:
        reception.est_lue = True
        reception.date_lecture = timezone.now()
        reception.save()

    return render(request, 'notes/note_detail.html', {
        'note': reception.note,
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



@login_required
def compteur_notes_non_lues(request):
    count = NoteReception.objects.filter(destinataire=request.user, lue=False, est_archivee=False).count()
    return JsonResponse({'count': count})
