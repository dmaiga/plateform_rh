from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class SuiviTache(models.Model):
    tache = models.ForeignKey('Tache', on_delete=models.CASCADE, related_name='suivis')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    # Dans models.py > SuiviTache
    def duree(self):
        end = self.end_time or timezone.now()
        if self.start_time:
            return end - self.start_time
        return timedelta(0)

    def __str__(self):
        return f"{self.user} - {self.tache.titre} ({self.start_time} → {self.end_time or 'en cours'})"


class Tache(models.Model):
    fiche_poste = models.ForeignKey("todo.FichePoste", on_delete=models.CASCADE, related_name="taches")
    
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    jour_prevu = models.PositiveIntegerField(null=True, blank=True)
    commentaire_rh = models.TextField(blank=True)


    
    def calculer_duree(self):
        """Calcule la durée en tenant compte des timezones"""
        if not self.start_time:
            return timedelta(0)
            
        if self.end_time:
            return self.end_time - self.start_time
            
        return timezone.now() - self.start_time

    def save(self, *args, **kwargs):
        """Met à jour automatiquement la durée totale"""
        if self.end_time and self.start_time:
            self.duree_total = self.calculer_duree()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titre



class TacheSelectionnee(models.Model):
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_selection = models.DateField()
        # État propre à cette sélection
    is_done = models.BooleanField(default=False)
    is_started = models.BooleanField(default=False)
    is_paused = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    pause_time = models.DateTimeField(null=True, blank=True)
    
    commentaire_rh = models.TextField(blank=True, null=True)  
    commentaire_employe = models.TextField(blank=True, null=True) 
     
    def duree_pause_en_cours(self):
        if self.is_paused and self.pause_time:
            return timezone.now() - self.pause_time
        return timedelta(0)
    def duree_active(self):
        suivis = SuiviTache.objects.filter(
            tache=self.tache,
            user=self.user,
            start_time__date=self.date_selection 
        )
        total = timedelta()
        for s in suivis:
            total += s.duree()
        return total

    
    @property
    def duree_active_affichee(self):
        total = self.duree_active()
        heures, reste = divmod(total.seconds, 3600)
        minutes, secondes = divmod(reste, 60)
        return f"{heures:02d}:{minutes:02d}:{secondes:02d}"
    
    @property
    def etat_courant(self):
        if self.is_done:
            return "Terminée"
        elif self.is_paused:
            return "En pause"
        elif self.is_started:
            return "En cours"
        return "Non démarrée"
    
    def calculer_duree(self):
        """Calcule la durée en tenant compte des timezones"""
        if not self.start_time:
            return timedelta(0)
            
        if self.end_time:
            return self.end_time - self.start_time
            
        return timezone.now() - self.start_time
    def __str__(self):
        return f"{self.user.username} - {self.tache.titre} ({self.date_selection})"

class FichePoste(models.Model):
    titre = models.CharField(max_length=255)
    employe = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fiches", null=True, blank=True)
    is_modele = models.BooleanField(default=False)
    date_creation = models.DateTimeField(default=timezone.now)  # Exemple d'utilisation

    def __str__(self):
        if self.is_modele:
            return f"[Modèle] {self.titre}"
        return f"{self.titre} - {self.employe.get_full_name() if self.employe else 'Non assignée'}"