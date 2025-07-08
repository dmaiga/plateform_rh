from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class NoteInterne(models.Model):
    NIVEAU_URGENCE = [
        ('low', 'Basse'),
        ('medium', 'Moyenne'), 
        ('high', 'Haute'),
        ('critical', 'Critique')
    ]

    expediteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notes_envoyees'
    )
    destinataires = models.ManyToManyField(
        User,
        through='NoteReception',
        related_name='notes_recues'
    )

    sujet = models.CharField(max_length=100)
    contenu = models.TextField()
    niveau_urgence = models.CharField(
        max_length=10,
        choices=NIVEAU_URGENCE,
        default='medium'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_limite = models.DateTimeField(null=True, blank=True)
    pieces_jointes = models.FileField(
        upload_to='notes_pieces_jointes/',
        null=True,
        blank=True
    )
    notification_envoyee = models.BooleanField(default=False)

    class Meta:
        ordering = ['-niveau_urgence', '-date_creation']
        verbose_name = "Note Flash"
        verbose_name_plural = "Notes Flash"

    def __str__(self):
        return f"{self.sujet} ({self.get_niveau_urgence_display()})"

    def badge_urgence(self):
        badges = {
            'low': '🟢 Basse',
            'medium': '🟡 Moyenne',
            'high': '🟠 Haute',
            'critical': '🔴 Critique',
        }
        return badges.get(self.niveau_urgence, self.niveau_urgence)


class NoteReception(models.Model):
    note = models.ForeignKey(
        NoteInterne,
        on_delete=models.CASCADE,
        related_name='receptions'
    )
    destinataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='receptions_notes'
    )
    est_lue = models.BooleanField(default=False)
    est_archivee = models.BooleanField(default=False)
    date_lecture = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('note', 'destinataire')

    def marquer_comme_lue(self):
        if not self.lue:
            self.lue = True
            self.date_lecture = timezone.now()
            self.save()

    def __str__(self):
        return f"{self.destinataire} - {self.note.sujet} ({'Lu' if self.lue else 'Non lu'})"
