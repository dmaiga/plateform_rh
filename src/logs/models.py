
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now

User = get_user_model()

class JournalAction(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
        ('CREATE_USER', 'Création user'),
        ('UPLOAD_DOCUMENT', 'Téléversement document'),
        ('DELETE_DOCUMENT', 'Suppression document'),
        ('VIEW_DOCUMENT', 'Consultation document'),
        # ... ajoute au besoin
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    date_action = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.date_action.strftime('%Y-%m-%d %H:%M')}"
