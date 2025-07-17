# authentication/views.py
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, authenticate ,logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse

from . import forms 
from .forms import CreateUserForm, PersonalUserUpdateForm, RHUserUpdateForm
from .models import User,Skill
from logs.utils import enregistrer_action
from calendar import monthrange
from todo.models import FichePoste, Tache,TacheSelectionnee   

from .forms import FichePosteForm
from django.utils import timezone

from todo.views import get_planning_context
from datetime import date, timedelta,datetime
from django.core.paginator import Paginator

from statics.utils import generate_graphs 
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import logging
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver
from functools import wraps



logger = logging.getLogger(__name__)

def is_rh_or_admin(user):
    return user.is_authenticated and user.role in ['admin', 'rh']

def get_performance_class(percentage):
    if percentage is None:
        return 'no-data'
    if percentage >= 90:
        return 'excellent'
    if percentage >= 70:
        return 'good'
    if percentage >= 50:
        return 'average'
    return 'poor'


@login_required
@user_passes_test(is_rh_or_admin)
def dashboard_rh(request):
    try:
        user_id = request.GET.get('user_id', 'all')
        period = request.GET.get('period', 'week')

        users = User.objects.exclude(role='admin').order_by('last_name')
        today = now().date()
        start_of_week = today - timedelta(days=today.weekday())
        jours_semaine = [start_of_week + timedelta(days=i) for i in range(5)]  # Lundi à vendredi

        stats = []
        for user in users:
            user_data = {
                'user': user,
                'days': [],
                'weekly_avg': 0,
                'trend': 'stable'
            }

            daily_percentages = []
            for day in jours_semaine:
                tasks_done = TacheSelectionnee.objects.filter(
                    user=user,
                    date_selection=day,
                    is_done=True
                ).count()

                percentage = round((tasks_done / 6) * 100) if tasks_done <= 6 else 100

                day_data = {
                    'date': day,
                    'percentage': percentage,
                    'tasks': f"{tasks_done}/6",
                    'css_class': get_performance_class(percentage)
                }
                user_data['days'].append(day_data)
                daily_percentages.append(percentage)

            user_data['weekly_avg'] = round(sum(daily_percentages) / len(jours_semaine))
            user_data['weekly_class'] = get_performance_class(user_data['weekly_avg'])

            stats.append(user_data)

        # Génération des graphiques
        graphs = generate_graphs(user_id=user_id, period=period)

        context = {
            'stats': stats,
            'week_days': jours_semaine,
            'week_range': f"{start_of_week:%d/%m} - {(start_of_week + timedelta(days=4)):%d/%m}",
            'users': users,
            'selected_user': user_id,
            'selected_period': period,
            **graphs
        }

        return render(request, 'authentication/dashboard_rh.html', context)

    except Exception as e:
        logger.error(f"Error generating dashboard data: {str(e)}")
        raise

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
def detail_fiche_poste(request, fiche_id):
    fiche = get_object_or_404(FichePoste, id=fiche_id)
    return render(request, 'authentication/detail_fiche_poste.html', {'fiche': fiche})

@login_required
@user_passes_test(is_rh_or_admin)
def employees_view(request):
    query = request.GET.get('q', '')
    department_filter = request.GET.get('department', '')
    role_filter = request.GET.get('role', '')
    statut_filter = request.GET.get('statut', '')

    users = User.objects.exclude(role='admin').select_related('fiche_poste', 'manager')

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(poste_occupe__icontains=query) |
            Q(ville__icontains=query)
        )
    
    if department_filter:
        users = users.filter(department__iexact=department_filter)
    
    if role_filter:
        users = users.filter(role__iexact=role_filter)
    
    if statut_filter:
        users = users.filter(statut__iexact=statut_filter)

    users = users.order_by('first_name')

    # Pour les filtres
    departments = User.objects.exclude(department='').values_list('department', flat=True).distinct()

    return render(request, 'authentication/employees_view.html', {
        'users': users,
        'query': query,
        'departments': departments,
        'role_choices': User.ROLE_CHOICES,
        'statut_choices': User.STATUT_CHOICES,
        'selected_department': department_filter,
        'selected_role': role_filter,
        'selected_statut': statut_filter,
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
    today = timezone.localdate()
    filtre = request.GET.get("filtre", "all")

    # Base queryset - utilise les champs de TacheSelectionnee directement
    taches_auj = TacheSelectionnee.objects.filter(user=request.user, date_selection=today)
    taches_filtrees = taches_auj

    # Filtrage cohérent avec le modèle
    if filtre == "terminees":
        taches_filtrees = taches_auj.filter(is_done=True)  # Supprimez tache__
    elif filtre == "en_cours":
        taches_filtrees = taches_auj.filter(is_started=True, is_done=False)
    elif filtre == "pause":
        taches_filtrees = taches_auj.filter(is_paused=True, is_done=False)

    # Compteurs cohérents
    nb_total = taches_auj.count()
    nb_terminees = taches_auj.filter(is_done=True).count()
    nb_en_cours = taches_auj.filter(is_started=True, is_done=False).count()
    nb_pause = taches_auj.filter(is_paused=True, is_done=False).count()


    planning_ctx = get_planning_context(request)

    return render(request, 'authentication/dashboard.html', {
        'taches_auj': taches_filtrees,
        'nb_total': nb_total,
        'nb_terminees': nb_terminees,
        'nb_en_cours': nb_en_cours,
        'nb_pause': nb_pause,
        'filtre_actuel': filtre,
        **planning_ctx,
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
                        
                        jour_prevu=tache.jour_prevu,
                        commentaire_rh=tache.commentaire_rh
                    )
            
                # Affectation automatique
                user.fiche_poste = nouvelle_fiche
                user.save()
            

            enregistrer_action(request.user, 'CREATE_USER', f"Création de {user.username}")
            messages.success(request, f"✅ Utilisateur {user.username} créé avec succès.")
            return redirect('dashboard-rh')
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
    user_cible = get_object_or_404(User, id=user_id)
    form = RHUserUpdateForm(instance=user_cible)
    skills = user_cible.skills.all()
    
    # Pagination pour les compétences
    skill_paginator = Paginator(skills, 5)
    skill_page = request.GET.get('skill_page')
    skills_page_obj = skill_paginator.get_page(skill_page)
    
    # Pagination pour les fiches de poste disponibles
    available_fiches = FichePoste.objects.all()
    fiche_paginator = Paginator(available_fiches, 5)
    fiche_page = request.GET.get('fiche_page')
    fiches_page_obj = fiche_paginator.get_page(fiche_page)

    if request.method == 'POST':
        form = RHUserUpdateForm(request.POST, request.FILES, instance=user_cible)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Profil de {user_cible.get_full_name()} mis à jour")
            return redirect('user-detail', user_id=user_id)

    context = {
        'form': form,
        'user_cible': user_cible,
        'skills_page_obj': skills_page_obj,
        'fiches_page_obj': fiches_page_obj,
        'active_tab': request.GET.get('tab', 'infos')
    }
    return render(request, 'authentication/edit_user_rh.html', context)


@login_required
@user_passes_test(is_rh_or_admin)
def remove_skill(request, user_id, skill_id):
    user = get_object_or_404(User, id=user_id)
    skill = get_object_or_404(Skill, id=skill_id)
    
    if request.method == 'POST':
        user.skills.remove(skill)
        messages.success(request, f"Compétence {skill.name} retirée")
    
    return redirect('edit-user-rh', user_id=user_id)

@login_required
@user_passes_test(is_rh_or_admin)
def assign_fiche_poste(request, user_id, fiche_id):
    user = get_object_or_404(User, id=user_id)
    fiche = get_object_or_404(FichePoste, id=fiche_id)
    
    if request.method == 'POST':
        user.fiche_poste = fiche
        user.save()
        messages.success(request, f"Fiche de poste {fiche.titre} attribuée")
    
    return redirect('edit-user-rh', user_id=user_id)