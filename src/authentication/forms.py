# authentication/forms.py
from django import forms
from .models import User

class LoginForm(forms.Form):
    username = forms.CharField(max_length=63, label='Nom d’utilisateur')
    password = forms.CharField(max_length=63, widget=forms.PasswordInput, label='Mot de passe')

class CreateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
                    'username', 
                    'first_name',
                    'last_name', 
                    'email', 
                    'role', 
                    'start_date', 
                    'statut', 
                    'telephone_pro'
                ]


class PersonalUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'photo',
            'telephone_perso',
            'adresse',
            'date_naissance',
            'contact_urgence',
            'formation',
        ]
