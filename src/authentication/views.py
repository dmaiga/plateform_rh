# authentication/views.py
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, authenticate ,logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import timedelta
from . import forms 
from .forms import CreateUserForm, PersonalUserUpdateForm, RHUserUpdateForm
from .models import User
from logs.utils import enregistrer_action

from todo.models import FichePoste, Tache  # importe les modèles du module todo
from datetime import date
from .forms import FichePosteForm

def is_rh_or_admin(user):
    return user.is_authenticated and user.role in ['admin', 'rh']

@login_required
@user_passes_test(is_rh_or_admin)
def supprimer_tache(request, tache_id):
    tache = get_object_or_404(Tache, id=tache_id)
    fiche_id = tache.fiche_poste.id
    tache.delete()
    messages.success(request, "🗑️ Tâche supprimée.")
    return redirect('ajouter-taches-modele', fiche_id=fiche_id)

@login_required
@user_passes_test(is_rh_or_admin)
def modifier_tache(request, tache_id):
    tache = get_object_or_404(Tache, id=tache_id)

    if request.method == 'POST':
        tache.titre = request.POST.get('titre')
        tache.description = request.POST.get('description')
        tache.save()
        messages.success(request, "✏️ Tâche modifiée.")
        return redirect('ajouter-taches-modele', fiche_id=tache.fiche_poste.id)

    return render(request, 'authentication/modifier_tache.html', {'tache': tache})


@login_required
@user_passes_test(is_rh_or_admin)
def create_modele_fiche_poste(request):
    if request.method == 'POST':
        form = FichePosteForm(request.POST)
        if form.is_valid():
            fiche = form.save(commit=False)
            fiche.is_modele = True
            fiche.employe = None
            fiche.save()
            return redirect('liste-modeles-fiches')  
    else:
        form = FichePosteForm()
    return render(request, 'authentication/create_modele_fiche.html', {'form': form})

@login_required
@user_passes_test(is_rh_or_admin)
def supprimer_modele_fiche(request, fiche_id):
    fiche = get_object_or_404(FichePoste, id=fiche_id, is_modele=True)
    fiche.delete()
    messages.success(request, "Modèle de fiche supprimé avec succès.")
    return redirect('liste-modeles-fiches')

@login_required
@user_passes_test(is_rh_or_admin)
def liste_modeles_fiches(request):
    modeles = FichePoste.objects.filter(is_modele=True)
    return render(request, 'authentication/liste_modeles_fiches.html', {'modeles': modeles})

@login_required
@user_passes_test(is_rh_or_admin)
def ajouter_taches_modele(request, fiche_id):
    fiche = get_object_or_404(FichePoste, id=fiche_id, is_modele=True)

    if request.method == 'POST':
        titre = request.POST.get('titre')
        description = request.POST.get('description')
        duree = request.POST.get('duree')

        if titre:
            duree_interval = timedelta(minutes=int(duree)) if duree else None
            Tache.objects.create(
                fiche_poste=fiche,
                titre=titre,
                description=description,
                duree_total=duree_interval
            )
            messages.success(request, "✅ Tâche ajoutée avec succès.")
            return redirect('ajouter-taches-modele', fiche_id=fiche.id)

    return render(request, 'authentication/ajouter_taches_modele.html', {'fiche': fiche})

@login_required
@user_passes_test(is_rh_or_admin)
def dashboard_rh(request):
    query = request.GET.get('q', '')

    # On exclut les admins dès le départ
    users = User.objects.exclude(role='admin')

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(statut__icontains=query)
        )

    users = users.order_by('last_name')

    return render(request, 'authentication/dashboard_rh.html', {
        'users': users,
        'query': query,
    })






@login_required
def mon_profil(request):
    user = request.user
    if request.method == 'POST':
        form = PersonalUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('mon-profil') 
    else:
        form = PersonalUserUpdateForm(instance=user)
    
    return render(request, 'authentication/mon_profil.html', {'form': form})



@login_required
def dashboard(request):
    if request.user.role in ["rh", "admin"]:
        return redirect('dashboard-rh')

    employe = request.user

    fiches = FichePoste.objects.filter(employe=employe)
    toutes_taches = Tache.objects.filter(fiche_poste__in=fiches).order_by(
        '-prevue_aujourdhui', 'est_terminee', 'priorite'
    )

    taches_aujourdhui = toutes_taches.filter(prevue_aujourdhui=True)
    taches_terminees = toutes_taches.filter(est_terminee=True)
    taches_en_cours = toutes_taches.filter(heure_debut__isnull=False, heure_fin__isnull=True)
    taches_a_faire = toutes_taches.filter(est_terminee=False, heure_debut__isnull=True)
   

    return render(request, 'authentication/dashboard.html', {
        'toutes_taches': toutes_taches,
        'taches_aujourdhui': taches_aujourdhui,
        'taches_en_cours': taches_en_cours,
        'taches_terminees': taches_terminees,
        'taches_a_faire': taches_a_faire,
    })



from todo.models import FichePoste, Tache

@login_required
@user_passes_test(is_rh_or_admin)
def create_user_view(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            fiche_modele = form.cleaned_data.get('fiche_poste_modele')
            user = form.save(commit=False)
            user.set_password('pass123')
            user.save()

            if fiche_modele:
                nouvelle_fiche = FichePoste.objects.create(
                    titre=fiche_modele.titre,
                    employe=user,
                    is_modele=False
                )
            
                # Clonage des tâches
                for tache in fiche_modele.taches.all():
                    Tache.objects.create(
                        fiche_poste=nouvelle_fiche,
                        titre=tache.titre,
                        description=tache.description,
                        priorite=tache.priorite,
                        jour_prevu=tache.jour_prevu,
                        commentaire_rh=tache.commentaire_rh
                    )
            
                # Affectation automatique
                user.fiche_poste = nouvelle_fiche
                user.save()
            

            enregistrer_action(request.user, 'CREATE_USER', f"Création de {user.username}")
            messages.success(request, f"✅ Utilisateur {user.username} créé avec succès.")
            return redirect('dashboard')
        else:
            messages.error(request, "⚠️ Erreur dans le formulaire : vérifiez les champs.")
    else:
        form = CreateUserForm()
    return render(request, 'authentication/create_user.html', {'form': form})


def logout_user(request):
    
    logout(request)
    return redirect('login')

def login_page(request):
    form = forms.LoginForm()
    message = ''
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                if user.role in ['admin', 'rh']:
                    return redirect('dashboard-rh')
                else:
                    return redirect('dashboard')
            else:
                message = 'Identifiants invalides.'
    return render(
        request, 'authentication/login.html', context={'form': form, 'message': message})

@login_required
@user_passes_test(is_rh_or_admin)
def user_detail(request):
    user_id = request.GET.get('id')
    user_cible = User.objects.filter(id=user_id).first()

    if not user_cible:
        messages.error(request, "❌ Utilisateur introuvable.")
        return redirect('dashboard-rh')

    # Journalisation
    enregistrer_action(request.user, 'CONSULT_USER_DETAIL', f"Consultation du profil de {user_cible.username}")

    return render(request, 'authentication/user_detail.html', {'user_cible': user_cible})

@login_required
@user_passes_test(is_rh_or_admin)
def edit_user_rh(request, user_id):
    user_cible = User.objects.filter(id=user_id).first()

    if not user_cible:
        messages.error(request, "❌ Utilisateur introuvable.")
        return redirect('dashboard-rh')

    if request.method == 'POST':
        form = RHUserUpdateForm(request.POST, instance=user_cible)
        if form.is_valid():
            form.save()
            enregistrer_action(request.user, 'UPDATE_USER_RH', f"Mise à jour RH de {user_cible.username}")
            messages.success(request, f"✅ Données mises à jour pour {user_cible.username}")
            url= reverse('user-detail') + f"?id={user_id}"
            return HttpResponseRedirect(url)
    else:
        form = RHUserUpdateForm(instance=user_cible)

    return render(request, 'authentication/edit_user_rh.html', {'form': form, 'user_cible': user_cible})

