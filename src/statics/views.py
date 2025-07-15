from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from datetime import date, timedelta,datetime
import json
from django.shortcuts import render, redirect,get_object_or_404
from django.utils import timezone
from todo.models import Tache, TacheSelectionnee, FichePoste, SuiviTache
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from collections import defaultdict
from calendar import monthrange,day_name
from django.db import transaction
from django.utils.timezone import localdate,now


from django.db.models import Count, Q,Sum
from django.db.models.functions import TruncMonth, TruncDate
import csv
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa  

JOURS_FR = {
    'Monday': 'Lundi',
    'Tuesday': 'Mardi',
    'Wednesday': 'Mercredi',
    'Thursday': 'Jeudi',
    'Friday': 'Vendredi',
    'Saturday': 'Samedi',
    'Sunday': 'Dimanche'
}

@login_required
def historique_par_mois(request):
    # Validation des paramètres
    mois = request.GET.get('mois')
    annee = request.GET.get('annee')
    
    if not mois or not annee:
        return redirect('statistique-utilisateur')
    
    try:
        mois = int(mois)
        annee = int(annee)
        date_debut = datetime(annee, mois, 1).date()
        _, dernier_jour = monthrange(annee, mois)
        date_fin = datetime(annee, mois, dernier_jour).date()
    except (ValueError, TypeError):
        return redirect('statistique-utilisateur')

    # Récupération des données par jour (uniquement du lundi au vendredi)
    jours_data = []
    current_date = date_debut
    
    while current_date <= date_fin:
        # Ne traiter que les jours de semaine (0=lundi, 4=vendredi)
        if current_date.weekday() < 5:  # 0-4 correspond à lundi-vendredi
            taches_jour = TacheSelectionnee.objects.filter(
                user=request.user,
                date_selection=current_date
            )
            
            total = taches_jour.count()
            terminees = taches_jour.filter(is_done=True).count()
            
            # Protection contre la division par zéro
            if total == 0:
                pourcentage = 0
                note = "Aucune tâche"
                badge_class = "bg-secondary"
            else:
                pourcentage = round((terminees / total) * 100)
                
                # Évaluation qualitative basée sur 6 tâches max
                if terminees >= 6:
                    note = "🎉 Excellent"
                    badge_class = "bg-success"
                elif terminees == 5:
                    note = "✅ Très bien"
                    badge_class = "bg-primary"
                elif terminees >= 3:
                    note = "⚠️ Moyen"
                    badge_class = "bg-warning"
                else:
                    note = "🔴 Insuffisant"
                    badge_class = "bg-danger"
            
            jours_data.append({
                'date': current_date,
                'date_str': current_date.strftime('%d/%m'),
                'jour_semaine': JOURS_FR[current_date.strftime('%A')], 
                'total': total,
                'terminees': terminees,
                'pourcentage': pourcentage,
                'note': note,
                'badge_class': badge_class,
                'has_data': total > 0
            })
        
        current_date += timedelta(days=1)

    # Grouper par semaine (lundi-vendredi)
    semaines = []
    semaine_courante = []
    semaine_num = 1
    
    for jour in jours_data:
        # Nouvelle semaine chaque lundi
        if not semaine_courante or jour['date'].weekday() == 0:
            if semaine_courante:
                semaines.append({
                    'numero': semaine_num,
                    'debut': semaine_courante[0]['date'],
                    'fin': semaine_courante[-1]['date'],
                    'jours': semaine_courante
                })
                semaine_num += 1
            semaine_courante = []
        
        semaine_courante.append(jour)
    
    # Ajouter la dernière semaine
    if semaine_courante:
        semaines.append({
            'numero': semaine_num,
            'debut': semaine_courante[0]['date'],
            'fin': semaine_courante[-1]['date'],
            'jours': semaine_courante
        })

    # Noms des mois en français
    mois_noms = {
        1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
        5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
        9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
    }

    context = {
        'mois_nom': mois_noms.get(mois, ""),
        'annee_selected': annee,
        'semaines': semaines,
    }
    return render(request, 'statics/historique_mois.html', context)
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
    
    pourcentage = round((terminees / total) * 100) if total else 0
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
        'jour': {
        'pourcentage': pourcentage
         }
    }
    return render(request, 'statics/historique_jour.html', context)




@login_required
def export_statistiques(request, date):
    user = request.user
    date_obj = datetime.strptime(date, '%Y-%m-%d').date()

    taches = (
        TacheSelectionnee.objects
        .filter(user=user, date_selection=date_obj)
        .select_related("tache")
    )
    # Calcul des stats
    total = taches.count()
    terminees = taches.filter(is_done=True).count()
    pourcentage = round((terminees / total) * 100) if total else 0

    context = {
        'date': date_obj,
        'user': user,
        'taches': taches,
        'jour': {
            'pourcentage': pourcentage
        }
    }

    html = render_to_string("statics/pdf_export.html", context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="journee_{date}.pdf"'

    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
    if pisa_status.err:
        return HttpResponse("Erreur PDF", status=500)
    return response

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
        historique_jour.append({
            'titre': sel.tache.titre,
            'etat': sel.etat_courant,
            'duree': sel.duree_active(),
        })

    # --- Préparation des données pour les selecteurs ---
    mois_fr = [
        (1, "Janvier"), (2, "Février"), (3, "Mars"), (4, "Avril"),
        (5, "Mai"), (6, "Juin"), (7, "Juillet"), (8, "Août"),
        (9, "Septembre"), (10, "Octobre"), (11, "Novembre"), (12, "Décembre")
    ]
    
    # Années disponibles (de la première tâche à aujourd'hui)
    premiere_tache = TacheSelectionnee.objects.filter(user=user).order_by('date_selection').first()
    annee_min = premiere_tache.date_selection.year if premiere_tache else today.year
    annees = range(annee_min, today.year + 1)

    context = {
        'total': total_selectionnees,
        'terminees': terminees,
        'en_cours': en_cours,
        'en_pause': en_pause,
        'non_demarre': non_demarre,
        'duree_totale': duree_totale,
        'moyenne_tache': moyenne_par_tache,
        'historique': historique_jour,
        'mois_fr': mois_fr,
        'annees': reversed(annees),  # Affichage des années récentes en premier
    }
    return render(request, 'statics/statistique.html', context)


from io import BytesIO
@login_required
def export_semaine(request, format, start_date_str):
    user = request.user
    start_date = parse_date(start_date_str)
    end_date = start_date + timedelta(days=6)

    taches = (
        TacheSelectionnee.objects
        .filter(user=user, date_selection__range=[start_date, end_date])
        .select_related('tache')
    )

    historique = defaultdict(list)
    jour_pourcentages = {}

    for t in taches:
        jour = t.date_selection
        if jour.weekday() < 5:  # Lundi à vendredi
            historique[jour].append(t)

    for jour, taches_du_jour in historique.items():
        total = len(taches_du_jour)
        terminees = sum(1 for t in taches_du_jour if t.is_done)
        pourcentage_jour = round((terminees / total) * 100) if total > 0 else 0
        jour_pourcentages[jour] = pourcentage_jour

    jours_effectifs = len(jour_pourcentages)
    pourcentage_global = round(sum(jour_pourcentages.values()) / jours_effectifs) if jours_effectifs else 0

    if pourcentage_global < 60:
        appreciation = "Insuffisant"
    elif pourcentage_global < 80:
        appreciation = "Bon"
    else:
        appreciation = "Excellent"

    if format == 'pdf':
        html = render_to_string("statics/semaine_pdf.html", {
            'historique': dict(historique),
            'start_date': start_date,
            'end_date': end_date,
            'user': user,
            'pourcentage': pourcentage_global,
            'appreciation': appreciation,
            'pourcentages_journaliers': jour_pourcentages,
        })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="semaine_{start_date}.pdf"'

        pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
        if pisa_status.err:
            return HttpResponse("Erreur de génération PDF", status=500)
        return response

    elif format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="semaine_{start_date}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Titre', 'État', 'Durée (min)', 'Commentaire RH', 'Commentaire Employé'])

        for date, taches_jour in dict(historique).items():
            for t in taches_jour:
                etat = "Terminée" if t.is_done else "En pause" if t.is_paused else "En cours" if t.is_started else "Non démarrée"
                writer.writerow([
                    date.strftime('%Y-%m-%d'),
                    t.tache.titre,
                    etat,
                    round(t.duree_active().total_seconds() / 60, 2),
                    t.commentaire_rh or t.tache.commentaire_rh or "",
                    t.commentaire_employe or ""
                ])
        return response

    return HttpResponse("Format non supporté", status=400)
