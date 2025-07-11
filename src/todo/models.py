from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

JOUR_CHOICES = [
    ("LUN", "Lundi"),
    ("MAR", "Mardi"),
    ("MER", "Mercredi"),
    ("JEU", "Jeudi"),
    ("VEN", "Vendredi"),
]


class Tache(models.Model):
    fiche_poste = models.ForeignKey('FichePoste', on_delete=models.CASCADE, related_name="taches")
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priorite = models.IntegerField(default=3)
    jour_prevu = models.CharField(max_length=3, choices=JOUR_CHOICES, null=True, blank=True)
    prevue_aujourdhui = models.BooleanField(default=False)
    est_terminee = models.BooleanField(default=False)
    heure_debut = models.DateTimeField(null=True, blank=True)
    heure_fin = models.DateTimeField(null=True, blank=True)
    duree_total = models.DurationField(null=True, blank=True)
    commentaire_rh = models.TextField(blank=True)
    date_planifiee = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.titre



class FichePoste(models.Model):
    titre = models.CharField(max_length=255)
    employe = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fiches", null=True, blank=True)
    is_modele = models.BooleanField(default=False) 

    def __str__(self):
        if self.is_modele:
            return f"[Modèle] {self.titre}"
        return f"{self.titre} - {self.employe.get_full_name() if self.employe else 'Non assignée'}"
