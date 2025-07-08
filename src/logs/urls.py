# journal/urls.py
from django.urls import path
from .views import liste_logs

urlpatterns = [
    path('', liste_logs, name='liste-logs'),
]
