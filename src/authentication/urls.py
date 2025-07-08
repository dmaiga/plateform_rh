from django.urls import path
from . import views


urlpatterns = [
   
   
    path('logout', views.logout_user, name='logout'), 
    path('create_user', views.create_user_view, name='create-user'),   
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/user-detail', views.user_detail, name='user-detail'),
    path('mon_profil/', views.mon_profil, name='mon-profil'),
    path('dashboard_rh/', views.dashboard_rh, name='dashboard-rh'),
    path('edit/<int:user_id>/', views.edit_user_rh, name='edit-user-rh'),

]

