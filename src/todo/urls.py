from django.urls import path
from . import views

urlpatterns = [
   path('planning/', views.planning_hebdo, name='planning-hebdo'),
   path('mes_taches/selection/', views.selection_taches, name='selection-taches'),
   path('mes_taches/', views.mes_taches, name='mes-taches'),
   path('mes_taches/<int:sel_id>/', views.detail_tache, name='detail-tache'),
   path('mes_taches/<int:sel_id>/supprimer/', views.supprimer_tache_selectionnee, name='supprimer-tache-selectionnee'),
   path('programmer/', views.programmer_semaine, name='programmer-semaine'),
   path('tache_selectionnee/<int:sel_id>/etat/', views.changer_etat_tache_selectionnee, name='changer-etat-tache-selectionnee'),

]