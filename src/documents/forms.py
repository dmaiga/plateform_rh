from django import forms
from .models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            'titre',
            'description',
            'type',
            'fichier',
            'visibilite',
            'affectations',
            'date_expiration_acces'
        ]
        widgets = {
            'date_expiration_acces': forms.DateInput(attrs={'type': 'date'}),
            'affectations': forms.CheckboxSelectMultiple
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(DocumentForm, self).__init__(*args, **kwargs)
        
        if user:
            if user.role == 'stagiaire':
                self.fields['affectations'].disabled = True
                self.fields['date_expiration_acces'].disabled = True
                self.fields['visibilite'].choices = [
                    ('prive', 'Privé'),
                    ('stagiaire', 'Tout le monde') 
                ]
            elif user.role == 'employe':
                self.fields['date_expiration_acces'].disabled = True
                self.fields['visibilite'].choices = [
                    ('prive', 'Privé'),
                    ('employe', 'Employés uniquement'),
                    ('stagiaire', 'Tout le monde') 
                ]
            elif user.role in ['rh', 'admin']:
                self.fields['visibilite'].choices = [
                    ('prive', 'Privé'),
                    ('stagiaire', 'Tout le monde'),
                    ('employe', 'Employés uniquement'),
                    ('rh', 'RH uniquement'),
                    ('admin', 'Administrateur uniquement'),
                    ('temporaire', 'Accès temporaire')
                ]
        