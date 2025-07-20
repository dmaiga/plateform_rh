from django.urls import path
from . import views

urlpatterns = [
    path('home', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('jobs/', views.jobs, name='jobs'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login, name='login'),
     path('entreprise-info/', views.entreprise_info, name='entreprise-info'),
]