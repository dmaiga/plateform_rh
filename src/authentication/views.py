# authentication/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate ,logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse

from . import forms 
from .forms import CreateUserForm, PersonalUserUpdateForm, RHUserUpdateForm
from .models import User
from logs.utils import enregistrer_action

from todo.models import FichePoste, Tache  # importe les modèles du module todo
from datetime import date

def is_rh_or_admin(user):
    return user.is_authenticated and user.role in ['admin', 'rh']

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



@login_required
@user_passes_test(is_rh_or_admin)
def create_user_view(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password('pass123') 
            user.save()
            enregistrer_action(request.user, 'CREATE_USER', f"Création de {user.username}")
            messages.success(request, f"✅ Utilisateur {user.username} créé avec succès.")
            print(f"Utilisateur {user.username} créé avec succès.")
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
