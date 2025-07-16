# authentication/forms.py
from django import forms
from .models import User, Skill
from todo.models import FichePoste


class FichePosteForm(forms.ModelForm):
    class Meta:
        model = FichePoste
        fields = ['titre']
        labels = {
            'titre': 'Nom du modèle de fiche',
        }



class LoginForm(forms.Form):
    username = forms.CharField(max_length=63, label='Nom d’utilisateur')
    password = forms.CharField(max_length=63, widget=forms.PasswordInput, label='Mot de passe')

class CreateUserForm(forms.ModelForm):
    fiche_poste_modele = forms.ModelChoiceField(
        queryset=FichePoste.objects.filter(is_modele=True),
        required=False,
        label="Modèle de fiche de poste"
    )

    class Meta:
        model = User
        fields = [
            'username', 'poste_occupe','fiche_poste_modele', 'role', 'start_date', 'telephone_pro'
        ]


class PersonalUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name', 
            'email', 
            'photo',
            'telephone_perso',
            'ville',
            'quartier',
            'porte',
            'rue',
            'date_naissance',
            'contact_urgence',
            'poste_occupe',
        ]
 


class RHUserUpdateForm(forms.ModelForm):
    skills_list = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        label="Compétences"
    )
    
    class Meta:
        model = User
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['skills_list'].initial = self.instance.skills.all()
        
        # Réorganisation des champs
        self.field_groups = {
            'informations_principales': [
                'username', 'first_name', 'last_name', 'email',
                'role', 'statut', 'poste_occupe', 'department',
                'contract_type', 'start_date', 'end_date'
            ],
            'coordonnees': [
                'telephone_pro', 'telephone_perso',
                'ville', 'quartier', 'rue', 'porte'
            ],
            'relations': [
                'manager', 'skills_list'
            ],
            'details': [
                'date_naissance', 'contact_urgence',
                'last_evaluation', 'salary', 'remote_days',
                'working_hours', 'notes'
            ],
            'fichiers': [
                'photo', 'cv', 'contract_file'
            ]
        }

        # Suppression du doublon fiche_poste si nécessaire
        if 'fiche_poste' in self.fields and hasattr(self.instance, 'fiche_poste'):
            self.fields['fiche_poste'].initial = self.instance.fiche_poste

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.skills.set(self.cleaned_data['skills_list'])
        return user



