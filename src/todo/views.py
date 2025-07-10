from django.shortcuts import render
from .models import Tache, FichePoste

from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from django.utils import timezone

@login_required
def planning_hebdo(request):
    employe = request.user
    aujourd_hui = date.today()
    debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())  # lundi
    fin_semaine = debut_semaine + timedelta(days=6)

    fiches = FichePoste.objects.filter(employe=employe)
    taches = Tache.objects.filter(
        fiche_poste__in=fiches,
        date_planifiee__range=(debut_semaine, fin_semaine)
    )

    return render(request, 'authentication/planning_hebdo.html', {
        'taches': taches,
        'debut_semaine': debut_semaine,
        'fin_semaine': fin_semaine
    })
