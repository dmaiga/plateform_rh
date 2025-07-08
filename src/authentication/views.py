# authentication/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate ,logout
from . import forms 
from .forms import CreateUserForm, PersonalUserUpdateForm
from django.contrib.auth.decorators import login_required, user_passes_test

from django.db.models import Q
from .models import User
def is_rh_or_admin(user):
    return user.is_authenticated and user.role in ['admin', 'rh']

@login_required
@user_passes_test(is_rh_or_admin)
def dashboard_rh(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).order_by('last_name') if query else User.objects.all()

    return render(request, 'authentication/dashboard_rh.html', {
        'users': users,
        'query': query,
    })





@login_required
def mon_profil(request):
    user = request.user
    if request.method == 'POST':
        form = PersonalUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('mon-profil') 
    else:
        form = PersonalUserUpdateForm(instance=user)
    
    return render(request, 'authentication/mon_profil.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'authentication/dashboard.html')



@login_required
@user_passes_test(is_rh_or_admin)
def create_user_view(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password('AntaresTemp123') 
            user.save()
            print(f"Utilisateur {user.username} créé avec succès.")
            return redirect('dashboard')
        else:
            print("Formulaire invalide :", form.errors)
    else:
        form = CreateUserForm()
    return render(request, 'authentication/create_user.html', {'form': form})


def logout_user(request):
    
    logout(request)
    return redirect('login')

def login_page(request):
    form = forms.LoginForm()
    message = ''
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                if user.role in ['admin', 'rh']:
                    return redirect('dashboard')
                else:
                    return redirect('dashboard')
            else:
                message = 'Identifiants invalides.'
    return render(
        request, 'authentication/login.html', context={'form': form, 'message': message})