from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from datetime import date, timedelta
import json

from .models import Tache, FichePoste

@login_required
def planning_hebdo(request):
    employe = request.user
    debut_semaine = date.today() - timedelta(days=date.today().weekday())
    fin_semaine = debut_semaine + timedelta(days=6)

    taches = Tache.objects.filter(
        fiche_poste__employe=employe,
        date_planifiee__range=(debut_semaine, fin_semaine)
    ).values(
        'titre',
        'est_terminee',
        'date_planifiee',
        'heure_debut',
        'heure_fin'
    )

    # Format explicite de la date
    taches_list = list(taches)
    for t in taches_list:
        t['date_planifiee'] = t['date_planifiee'].strftime('%Y-%m-%d')
        if t['heure_debut']:
            t['heure_debut'] = t['heure_debut'].strftime('%H:%M:%S')
        if t['heure_fin']:
            t['heure_fin'] = t['heure_fin'].strftime('%H:%M:%S')

    return render(request, 'todo/planning_hebdo.html', {
        'taches_json': json.dumps(taches_list, cls=DjangoJSONEncoder),
        'debut_semaine': debut_semaine,
        'fin_semaine': fin_semaine,
    })
