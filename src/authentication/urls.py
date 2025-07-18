from django.urls import path
from . import views


urlpatterns = [
   
   
    path('logout', views.logout_user, name='logout'), 
    path('create_user', views.create_user_view, name='create-user'),   
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-rh/', views.dashboard_rh, name='dashboard-rh'),
    path('dashboard/user-detail', views.user_detail, name='user-detail'),
    path('mon_profil/', views.mon_profil, name='mon-profil'),
    path('employees-view/', views.employees_view, name='employees-view'),
    path('edit/<int:user_id>/', views.edit_user_rh, name='edit-user-rh'),
    path('create_fiche_poste',views.create_modele_fiche_poste,name='create-fiche-poste'),
    path('liste_modeles_fiches',views.liste_modeles_fiches,name='liste-modeles-fiches'),
    path('supprimer_fiche_poste/<int:fiche_id>/', views.supprimer_modele_fiche, name='supprimer-fiche-poste'),
    path('ajouter_taches_modele/<int:fiche_id>/',views.ajouter_taches_modele,name='ajouter-taches-modele'),
    path('modifier_tache/<int:tache_id>/', views.modifier_tache, name='modifier-tache'),
    path('supprimer_tache/<int:tache_id>/', views.supprimer_tache, name='supprimer-tache'),
    path('detail_fiche_poste/<int:fiche_id>/', views.detail_fiche_poste, name='detail-fiche-poste'),
    path('assign_fiche_poste/<int:user_id>/<int:fiche_id>/', views.assign_fiche_poste, name='assign-fiche-poste'),
    path('changer-mot-de-passe/', views.change_password, name='change-password'),
]

