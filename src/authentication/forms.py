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
            'telephone_pro',
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
        widget=forms.SelectMultiple(attrs={'class': 'select2 form-control'}),
        label="Compétences"
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'role', 'statut',
            'poste_occupe', 'department', 'start_date', 'end_date',
            'last_evaluation', 'contract_type', 'manager',
            'photo', 'cv', 'contract_file',
            'telephone_pro', 'telephone_perso',
            'quartier', 'rue', 'porte', 'ville',
            'contact_urgence', 'salary', 'remote_days',
            'working_hours', 'notes'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'last_evaluation': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialiser les compétences
        if self.instance.pk:
            self.fields['skills_list'].initial = self.instance.skills.all()

    def save(self, commit=True):
        user = super().save(commit)
        if commit:
            user.skills.set(self.cleaned_data.get('skills_list', []))
        return user


class RHUserBasicForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'role', 'statut', 'poste_occupe',
            'department', 'start_date', 'end_date'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
