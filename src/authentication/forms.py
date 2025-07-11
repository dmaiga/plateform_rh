# authentication/forms.py
from django import forms
from .models import User
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
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'role', 'statut', 'start_date', 'end_date', 'telephone_pro',
            'fiche_poste'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fiche_poste'].queryset = FichePoste.objects.filter(is_modele=True)
