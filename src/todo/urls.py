from django.urls import path
from . import views

urlpatterns = [
   path('planning/', views.planning_hebdo, name='planning-hebdo'),
]
