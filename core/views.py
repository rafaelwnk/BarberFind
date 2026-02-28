from django.shortcuts import render

def login_view(request):
    return render(request, 'core/login.html')

def register_view(request):
    return render(request, 'core/register.html')

def home_view(request):
    return render(request, 'core/home.html')

def search_view(request):
    return render(request, 'core/search.html')

def history_view(request):
    return render(request, 'core/history.html')