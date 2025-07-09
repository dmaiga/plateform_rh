from django import forms
from django.contrib.auth import get_user_model
from .models import NoteInterne

User = get_user_model()

class NoteForm(forms.ModelForm):
    destinataires = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2',
            'data-placeholder': 'Choisissez les destinataires',
        })
    )

    class Meta:
        model = NoteInterne
        fields = [
            'destinataires',
            'sujet',
            'contenu',
            'niveau_urgence',
            'date_limite',
            'pieces_jointes'
        ]

        widgets = {
            'sujet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sujet de la note...'
            }),
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Contenu de la note...'
            }),
            'niveau_urgence': forms.Select(attrs={
                'class': 'form-select urgency-select',
            }),
            'date_limite': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
            }),
            'pieces_jointes': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        super(NoteForm, self).__init__(*args, **kwargs)
        self.fields['destinataires'].label = "📬 Destinataires"
        self.fields['niveau_urgence'].label = "⏱ Niveau d’urgence"
        self.fields['date_limite'].label = "🗓 Date limite"
        self.fields['pieces_jointes'].label = "📎 Pièce jointe (facultatif)"
