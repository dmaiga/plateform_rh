from django.shortcuts import render




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

def login(request):
    return render(request, 'site_web/login.html')

def entreprise_info(request):
    return render(request, 'site_web/entreprise_info.html')