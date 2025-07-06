from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('rh', 'Ressources Humaines'),
        ('employe', 'Employé'),
        ('stagiaire', 'Stagiaire'),
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('pause', 'En pause'),
        ('termine', 'Terminé'),
    ]
    # Champs RH
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    start_date = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='actif')
    telephone_pro = models.CharField(max_length=20, blank=True)

    # Champs personnels complétés par l'utilisateur
    photo = models.ImageField(upload_to='avatars/', blank=True, null=True)
    telephone_perso = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    contact_urgence = models.CharField(max_length=100, blank=True)
    formation = models.TextField(blank=True)


    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"