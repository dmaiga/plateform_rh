from django import forms
from .models import Tache

class TacheForm(forms.ModelForm):
    class Meta:
        model = Tache
        fields = ['titre', 'fiche_poste', 'date_planifiee', 'heure_debut', 'heure_fin', 'priorite']
        widgets = {
            'date_planifiee': forms.DateInput(attrs={'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time'}),
        }
