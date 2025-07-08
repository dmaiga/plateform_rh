# journal/views.py
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render
from .models import JournalAction

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
@user_passes_test(is_admin)
def liste_logs(request):
    logs = JournalAction.objects.select_related('user').order_by('-date_action')[:200]
    return render(request, 'logs/liste_logs.html', {'logs': logs})
