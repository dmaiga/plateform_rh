# notes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('send_note/', views.send_note, name='send-note'),
    path('sent_note/', views.sent_notes, name='sent-note'),
    path('note/<int:note_id>/', views.note_detail, name='note-detail'),
    path('note/<int:note_id>/archiver/', views.archiver_note, name='archiver-note'),
    path('note_envoyee/<int:note_id>/', views.note_envoyee_detail, name='note-envoyee-detail'),

]
