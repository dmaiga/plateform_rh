from django.urls import path
from . import views

urlpatterns = [

   path('statistique/', views.statistique_globale, name='statistique-utilisateur'),
   path('historique/mois/', views.historique_par_mois, name='historique-par-mois'),
   path('historique/jour/<str:date_str>/', views.historique_jour, name='historique-jour'),
   path('export/journee/<date>/', views.export_statistiques, name='export-journee'),
   path('export-semaine/<str:format>/<str:start_date_str>/', views.export_semaine, name='export-semaine'),

]