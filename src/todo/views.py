from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from datetime import date, timedelta
import json
from django.shortcuts import render, redirect,get_object_or_404
from django.utils import timezone
from .models import Tache, TacheSelectionnee, FichePoste, SuiviTache
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from collections import defaultdict
from calendar import day_name


@login_required
def programmer_semaine(request):
    user = request.user
    today = timezone.localdate()

    if request.method == 'POST':
        date_str = request.POST.get("date_selection")
        date_selection = parse_date(date_str) or today

        # ✅ Liste des tâches actuellement sélectionnées pour ce jour
        anciennes_selectionnees = TacheSelectionnee.objects.filter(user=user, date_selection=date_selection)

        # ✅ Nouvelles tâches sélectionnées dans le formulaire
        tache_ids = set(map(int, request.POST.getlist('taches')))

        # ✅ Supprimer celles décochées
        anciennes_selectionnees.exclude(tache__id__in=tache_ids).delete()

        # ✅ Ajouter les nouvelles (en évitant les doublons)
        for tache_id in tache_ids:
            tache = Tache.objects.get(id=tache_id)
            TacheSelectionnee.objects.get_or_create(
                user=user,
                tache=tache,
                date_selection=date_selection
            )

        return redirect('dashboard')

    # GET
    date_str = request.GET.get("date")
    date_selection = parse_date(date_str) if date_str else today

    taches = Tache.objects.filter(fiche_poste=user.fiche_poste)
    selectionnees = TacheSelectionnee.objects.filter(user=user, date_selection=date_selection)
    taches_selectionnees_ids = [s.tache.id for s in selectionnees]

    return render(request, 'todo/programmer_semaine.html', {
        'taches': taches,
        'taches_selectionnees_ids': taches_selectionnees_ids,
        'date_selection': date_selection,
        'today': today,
    })



@login_required
def get_planning_context(request):
    offset = int(request.GET.get("semaine", 0))
    today = timezone.localdate()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    jours = [start_of_week + timedelta(days=i) for i in range(7)]

    taches_selectionnees = TacheSelectionnee.objects.filter(
        user=request.user,
        date_selection__range=(jours[0], jours[-1])
    ).select_related('tache')

    taches_par_jour = defaultdict(list)
    for tsel in taches_selectionnees:
        taches_par_jour[tsel.date_selection].append(tsel)

    return {
        'jours': jours,
        'taches_par_jour': taches_par_jour,
        'offset': offset,
    }
@login_required
def planning_hebdo(request):
    ctx = get_planning_context(request)
    return render(request, "todo/planning_hebdo.html", ctx)



@login_required
def selection_taches(request):
    user = request.user
    today = timezone.now().date()

    if request.method == 'POST':
        date_str = request.POST.get("date_selection")
        date_selection = parse_date(date_str) or today

        tache_ids = request.POST.getlist('taches')
        for tache_id in tache_ids:
            tache = Tache.objects.get(id=tache_id)
            TacheSelectionnee.objects.get_or_create(
                user=user,
                tache=tache,
                date_selection=date_selection
            )
        return redirect('mes-taches')  

    # Si GET, on peut aussi préremplir pour la date passée en paramètre
    date_str = request.GET.get("date")
    date_selection = parse_date(date_str) if date_str else today

    taches = Tache.objects.filter(fiche_poste=user.fiche_poste)
    selectionnees = TacheSelectionnee.objects.filter(user=user, date_selection=date_selection)
    taches_selectionnees_ids = [s.tache.id for s in selectionnees]

    return render(request, 'todo/selection_taches.html', {
        'taches': taches,
        'taches_selectionnees_ids': taches_selectionnees_ids,
        'date_selection': date_selection,
        'today': today,
    })


@login_required
def mes_taches(request):
    user = request.user
    date_str = request.GET.get("date")
    date_selection = timezone.now().date()

    if date_str:
        try:
            date_selection = parse_date(date_str) or date_selection
        except Exception:
            pass

    taches_selectionnees = TacheSelectionnee.objects.filter(
        user=user,
        date_selection=date_selection
    )

    return render(request, 'todo/mes_taches.html', {
        'taches_selectionnees': taches_selectionnees,
        'date_selection': date_selection,
    })

@login_required
def detail_tache(request, sel_id):
    selection = get_object_or_404(TacheSelectionnee, id=sel_id, user=request.user)
    return render(request, "todo/detail_tache.html", {
        "selection": selection,
        "tache": selection.tache
    })

@login_required
@require_POST
def supprimer_tache_selectionnee(request, sel_id):
    sel = get_object_or_404(TacheSelectionnee, id=sel_id, user=request.user)
    sel.delete()
    return redirect("mes-taches")

@require_POST
@login_required
def changer_etat_tache_selectionnee(request, sel_id):
    selection = get_object_or_404(TacheSelectionnee, id=sel_id, user=request.user)
    action = request.POST.get('action')
    now = timezone.now()

    if action == "start":
        if not selection.is_started:
            selection.is_started = True
            selection.start_time = now
            selection.save()
            SuiviTache.objects.create(tache=selection.tache, user=request.user, start_time=now)
        elif selection.is_paused:
            selection.is_paused = False
            selection.is_started = True  
            selection.save()
            SuiviTache.objects.create(tache=selection.tache, user=request.user, start_time=now)


    elif action == "pause":
        if selection.is_started and not selection.is_paused:
            selection.is_paused = True
            selection.save()
            suivi = SuiviTache.objects.filter(tache=selection.tache, user=request.user, end_time__isnull=True).last()
            if suivi:
                suivi.end_time = now
                suivi.save()

    elif action == "done":
        if selection.is_started and not selection.is_done:
            selection.is_done = True
            selection.end_time = now
            selection.is_paused = False
            selection.save()
            suivi = SuiviTache.objects.filter(tache=selection.tache, user=request.user, end_time__isnull=True).last()
            if suivi:
                suivi.end_time = now
                suivi.save()
            total = timedelta()
            for s in SuiviTache.objects.filter(tache=selection.tache, user=request.user):
                total += s.duree()
            selection.tache.duree_total = total
            selection.tache.save()

    return redirect("dashboard")

