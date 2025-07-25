from django.shortcuts import render, redirect
from .models import Document
from .forms import DocumentForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from logs.utils import enregistrer_action
from django.contrib import messages

def has_upload_permission(user):
    return user.is_authenticated and user.role in ['admin', 'rh']

@login_required
def document_list(request):
    user = request.user
    documents = Document.objects.all()
    query = request.GET.get('q', '')
    type_filter = request.GET.get('type', '')
    now = timezone.now().date()

    documents = Document.objects.none()

    if user.role == 'admin':
        documents = Document.objects.all()

    elif user.role == 'rh':
        documents = Document.objects.filter(
            Q(visibilite__in=['stagiaire', 'employe', 'rh', 'temporaire', 'admin']) |
            Q(visibilite='prive', auteur=user) |
            Q(affectations=user)
        )

    elif user.role == 'employe':
        documents = Document.objects.filter(
            Q(visibilite__in=['stagiaire', 'employe']) |
            Q(visibilite='prive', auteur=user) |
            Q(affectations=user)
        )

    elif user.role == 'stagiaire':
        documents = Document.objects.filter(
            (
                Q(visibilite='stagiaire') |
                Q(visibilite='prive', auteur=user) |
                Q(affectations=user)
            ) &
            (
                Q(date_expiration_acces__isnull=True) |
                Q(date_expiration_acces__gte=now)
            )
        )

    # Appliquer les filtres de recherche
    if query:
        documents = documents.filter(
            Q(titre__icontains=query) | Q(description__icontains=query)
        )
    
    if type_filter:
        documents = documents.filter(type=type_filter)
    
    return render(request, 'documents/document_list.html', {
        'documents': documents.distinct(),
        'query': query,
        'type_filter': type_filter,
    })


@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)

    if not document.peut_etre_vu_par(request.user):
        return HttpResponseForbidden("Vous n'avez pas accès à ce document.")

    return render(request, 'documents/document_detail.html', {
        'document': document
    })

@login_required
def upload_document(request):
    user = request.user

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.auteur = user

            try:
                if user.role == 'stagiaire':
                    if form.cleaned_data['visibilite'] not in ['prive', 'stagiaire', 'employe']:
                        doc.visibilite = 'prive'
                    doc.date_expiration_acces = None
                    doc.save()
                    # Pas de m2m
                elif user.role == 'employe':
                    if form.cleaned_data['visibilite'] not in ['prive', 'employe']:
                        doc.visibilite = 'prive'
                    doc.date_expiration_acces = None
                    doc.save()
                    form.save_m2m()
                else:
                    doc.save()
                    form.save_m2m()

                enregistrer_action(user, 'UPLOAD_DOCUMENT', f"Téléversement du document : {doc.titre}")
                messages.success(request, f"📄 Le document « {doc.titre} » a été ajouté avec succès.")
                return redirect('document-list')

            except Exception as e:
                messages.error(request, f"❌ Une erreur est survenue lors de l'enregistrement : {e}")
        else:
            messages.warning(request, "⚠️ Le formulaire contient des erreurs. Veuillez vérifier les champs.")
    else:
        form = DocumentForm(user=user)

    return render(request, 'documents/upload_document.html', {'form': form})