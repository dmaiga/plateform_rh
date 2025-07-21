from django.shortcuts import render, redirect


def home(request):
    return render(request, 'site_web/index.html')

def about(request):
    return render(request, 'site_web/about.html')

def services(request):
    return render(request, 'site_web/services.html')

def jobs(request):
    return render(request, 'site_web/jobs.html')

def contact(request):
    return render(request, 'site_web/contact.html')



def entreprise_info(request):
    return render(request, 'site_web/entreprise_info.html')

def login(request):
    # Si l'utilisateur vient de s'inscrire et est redirigé depuis entreprise_registry
    if request.method == 'GET' and 'from_registry' in request.GET:
        # Vous pouvez ajouter un message de bienvenue ici
        return render(request, 'site_web/login.html', {'registration_success': True})
    
    # Traitement normal de la connexion
    return render(request, 'site_web/login.html')

def entreprise_registry(request):
    # Si le formulaire est soumis
    if request.method == 'POST':
        
        return redirect('login?from_registry=true&type=company')
    
    # Affichage normal du formulaire d'inscription
    return render(request, 'site_web/entreprise_registry.html')

def candidat_register(request):
    if request.method == 'POST':
        # Traitement de l'inscription
        return redirect('login?type=candidate&from_registry=true')
    return render(request, 'site_web/candidate_registry.html')

def savoir_plus(request):
    return render(request, 'site_web/savoir_plus.html')

def recruteur_info(request):
    return render(request, 'site_web/recruteur_info.html')

def rejoindre_team(request):
    return render(request, 'site_web/rejoindre_team.html')