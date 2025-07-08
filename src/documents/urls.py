from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_list, name='document-list'),
    path('upload/', views.upload_document, name='upload-document'),
    path('<int:pk>/', views.document_detail, name='document-detail'),
]
