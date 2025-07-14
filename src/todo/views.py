from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from datetime import date, timedelta,datetime

import json
from django.shortcuts import render, redirect,get_object_or_404
from django.utils import timezone
from .models import Tache, TacheSelectionnee, FichePoste, SuiviTache
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from collections import defaultdict
from calendar import day_name
from django.db import transaction
from django.utils.timezone import localdate

from django.utils.timezone import now
from calendar import monthrange
from django.db.models import Count, Q

from django.db.models.functions import TruncMonth, TruncDate
import csv
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string

from xhtml2pdf import pisa  

@login_required
def export_statistiques(request, format, mois=None):
    user = request.user

    # Données déjà calculées dans historique_mensuel
    taches = (
        TacheSelectionnee.objects
        .filter(user=user)
        .select_related('tache')
        .annotate(month=TruncMonth("date_selection"))
    )

    historique = defaultdict(list)

    for t in taches:
        month_key = t.date_selection.strftime("%Y-%m")
        if not mois or month_key == mois:
            historique[month_key].append(t)

    if format == 'csv':
        # --- CSV ---
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="statistiques_{mois or "tous"}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Mois', 'Titre', 'État', 'Durée active (min)'])

        for m, taches_mois in historique.items():
            for t in taches_mois:
                if t.is_done:
                    etat = "Terminée"
                elif t.is_paused:
                    etat = "En pause"
                elif t.is_started:
                    etat = "En cours"
                else:
                    etat = "Non démarrée"
                writer.writerow([m, t.tache.titre, etat, round(t.duree_active().total_seconds() / 60, 2)])

        return response

    elif format == 'pdf':
        # --- PDF ---
        html = render_to_string("todo/pdf_export.html", {
            'historique': dict(historique),
            'mois': mois or "Tous",
            'user': user,
        })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="statistiques_{mois or "tous"}.pdf"'

        pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
        if pisa_status.err:
            return HttpResponse("Erreur de génération PDF", status=500)
        return response

    else:
        return HttpResponse("Format non supporté", status=400)



from collections import defaultdict
from django.db.models.functions import TruncMonth, TruncDate
from django.utils.timezone import now
from datetime import timedelta

@login_required
def statistique_globale(request):
    user = request.user
    today = now().date()

    # --- Statistiques du jour ---
    taches_auj = TacheSelectionnee.objects.filter(user=user, date_selection=today)
    total_selectionnees = taches_auj.count()
    terminees = taches_auj.filter(is_done=True).count()
    en_cours = taches_auj.filter(is_started=True, is_paused=False, is_done=False).count()
    en_pause = taches_auj.filter(is_paused=True, is_done=False).count()
    non_demarre = taches_auj.filter(is_started=False, is_paused=False, is_done=False).count()

    duree_totale = sum((s.duree() for s in SuiviTache.objects.filter(user=user, start_time__date=today)), timedelta())
    moyenne_par_tache = duree_totale / total_selectionnees if total_selectionnees > 0 else timedelta()

    historique_jour = []
    for sel in taches_auj:
        if sel.is_done:
            etat = "Terminée"
        elif sel.is_paused:
            etat = "En pause"
        elif sel.is_started:
            etat = "En cours"
        else:
            etat = "Non démarrée"
        
        historique_jour.append({
            'titre': sel.tache.titre,
            'etat': etat,
            'duree': sel.duree_active(),
        })

    # --- Historique mensuel ---
    taches = (
        TacheSelectionnee.objects
        .filter(user=user)
        .select_related('tache')
        .annotate(month=TruncMonth("date_selection"))
        .order_by("-date_selection")
    )

    historique = defaultdict(list)
    stats_par_mois = {}

    for t in taches:
        mois = t.date_selection.strftime("%Y-%m")
        historique[mois].append(t)

    for mois, taches_mois in historique.items():
        total = len(taches_mois)
        terminees = sum(1 for t in taches_mois if t.is_done)
        en_pause = sum(1 for t in taches_mois if t.is_paused and not t.is_done)
        en_cours = sum(1 for t in taches_mois if t.is_started and not t.is_paused and not t.is_done)
        non_demarre = sum(1 for t in taches_mois if not t.is_started and not t.is_done)

        duree_total = sum((t.duree_active() for t in taches_mois), timedelta())

        stats_par_mois[mois] = {
            'total': total,
            'terminees': terminees,
            'en_pause': en_pause,
            'en_cours': en_cours,
            'non_demarre': non_demarre,
            'duree_totale': duree_total,
        }

    context = {
        # stats jour
        'total': total_selectionnees,
        'terminees': terminees,
        'en_cours': en_cours,
        'en_pause': en_pause,
        'non_demarre': non_demarre,
        'duree_totale': duree_totale,
        'moyenne_tache': moyenne_par_tache,
        'historique': historique_jour,

        # historique mensuel
        'stats_par_mois': stats_par_mois,
        'historique_grouped': historique,
        'mois_disponibles': sorted(historique.keys(), reverse=True),
        'mois_selectionne': request.GET.get("mois")
    }

    return render(request, 'todo/statistique.html', context)




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
   

    date_selection = parse_date(date_str) if date_str else localdate()
    if not date_selection:
        date_selection = localdate()

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
    action = request.POST.get("action")
    now = timezone.now()

    with transaction.atomic():
        if action == "start":
            # Mettre en pause les autres tâches
            autres = TacheSelectionnee.objects.filter(
                user=request.user,
                is_started=True,
                
                is_paused=False
            ).exclude(id=selection.id)

            for autre in autres:
                autre.is_paused = True
                autre.is_started = False
                autre.save()

                suivi = SuiviTache.objects.filter(
                    tache=autre.tache,
                    user=request.user,
                    end_time__isnull=True
                ).last()

                if suivi:
                    suivi.end_time = now
                    suivi.save()

            if not selection.is_started:
                selection.is_started = True
                selection.start_time = now

            selection.is_paused = False
            selection.save()

            SuiviTache.objects.create(
                tache=selection.tache,
                user=request.user,
                start_time=now
            )

        elif action == "pause":
            if selection.is_started and not selection.is_paused:
                selection.is_paused = True
                selection.is_started = False  # Ajout ici pour arrêter le chrono
                selection.pause_time = now
                selection.save()

                suivi = SuiviTache.objects.filter(
                    tache=selection.tache,
                    user=request.user,
                    end_time__isnull=True
                ).last()

                if suivi:
                    suivi.end_time = now
                    suivi.save()


        elif action == "done":
            if (selection.is_started or selection.is_paused) and not selection.is_done:
                selection.is_done = True
                selection.is_started = False
                selection.is_paused = False
                selection.pause_time = None
                selection.end_time = now
                selection.save()

                # Fermer un suivi en cours s’il y en a
                suivi = SuiviTache.objects.filter(
                    tache=selection.tache,
                    user=request.user,
                    end_time__isnull=True
                ).last()

                if suivi:
                    suivi.end_time = now
                    suivi.save()

                # Calcule de la durée réelle (somme des suivis)
                total = timedelta()
                for s in SuiviTache.objects.filter(
                    tache=selection.tache,
                    user=request.user
                ):
                    total += s.duree()

                # Sauvegarde dans TacheSelectionnee (si tu ajoutes un champ duree_total)
                # selection.duree_total = total
                # selection.save()


    return redirect("dashboard")
from django.db.models import Count, Sum
from datetime import datetime, timedelta
from calendar import monthrange
@login_required
def historique_par_mois(request):
    # Liste des mois en français pour le template
    MOIS_FR = [
        (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), 
        (4, 'Avril'), (5, 'Mai'), (6, 'Juin'),
        (7, 'Juillet'), (8, 'Août'), (9, 'Septembre'),
        (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')
    ]
    
    # Récupérer les paramètres avec valeurs par défaut
    now = datetime.now()
    mois = int(request.GET.get('mois', now.month))
    annee = int(request.GET.get('annee', now.year))
    
    # Calculer les dates de début et fin du mois
    _, dernier_jour = monthrange(annee, mois)
    date_debut = datetime(annee, mois, 1).date()
    date_fin = datetime(annee, mois, dernier_jour).date()
    
    # Récupérer toutes les semaines du mois
    semaines = []
    current_date = date_debut
    semaine_num = 1
    
    while current_date <= date_fin:
        # Déterminer le début et la fin de la semaine
        debut_semaine = current_date
        fin_semaine = debut_semaine + timedelta(days=6)
        if fin_semaine > date_fin:
            fin_semaine = date_fin
        
        # Récupérer les données pour chaque jour de la semaine
        jours = []
        for jour in range(7):
            date_courante = debut_semaine + timedelta(days=jour)
            if date_courante > date_fin:
                break
            
            # Compter les tâches (optimisation: une seule requête par jour)
            taches = TacheSelectionnee.objects.filter(
                user=request.user,
                date_selection=date_courante
            ).aggregate(
                total=Count('id'),
                terminees=Count('id', filter=Q(is_done=True))
            )
            total = taches['total']
            terminees = taches['terminees']
            
            # Calculer le pourcentage
            pourcentage = round((terminees / total) * 100) if total > 0 else 0
            
            # Déterminer la note
            if terminees >= 6:
                note = "🎉 Excellent"
            elif terminees == 5:
                note = "✅ Bien"                
            elif 3 <= terminees <= 4:
                note = "⚠️ Moyen"
            else:
                note = "🔴 Insuffisant"
            
            jours.append({
                'date': date_courante,
                'date_str': date_courante.strftime('%d/%m'),
                'jour_semaine': date_courante.strftime('%A'),
                'total': total,
                'terminees': terminees,
                'pourcentage': pourcentage,
                'note': note
            })
        
        semaines.append({
            'numero': semaine_num,
            'debut': debut_semaine,
            'fin': fin_semaine,
            'jours': jours
        })
        
        # Passer à la semaine suivante
        current_date = fin_semaine + timedelta(days=1)
        semaine_num += 1
    
    context = {
        'mois_selected': mois,
        'annee_selected': annee,
        'mois_nom': dict(MOIS_FR).get(mois, ''),
        'semaines': semaines,
        'mois_fr': MOIS_FR,
        'annees': range(now.year - 2, now.year + 2),  # 5 ans autour de l'année actuelle
        'current_year': now.year,
        'current_month': now.month,
    }
    return render(request, 'todo/historique_mois.html', context)

@login_required
def historique_jour(request, date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Récupérer les tâches
    taches = TacheSelectionnee.objects.filter(
        user=request.user,
        date_selection=date_obj
    ).select_related('tache')
    
    # Calcul des statistiques
    total = taches.count()
    terminees = taches.filter(is_done=True).count()
    
    # Calcul du temps total et moyen
    suivis = SuiviTache.objects.filter(
        user=request.user,
        start_time__date=date_obj
    )
    
    duree_totale = sum((s.duree() for s in suivis), timedelta())
    moyenne = duree_totale / total if total > 0 else timedelta()
    
    context = {
        'date': date_obj,
        'taches': taches,
        'total': total,
        'terminees': terminees,
        'duree_totale': duree_totale,
        'duree_moyenne': moyenne,
    }
    return render(request, 'todo/historique_jour.html', context)