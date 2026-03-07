from decimal import Decimal

from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from core.models import Appointment, Barber, Service
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_staff

def home_view(request):
    user = request.user

    if user.is_staff:
        return render(request, "core/admin/dashboard.html")

    elif hasattr(user, "barber"):
        return render(request, "core/home_barber.html")

    elif hasattr(user, "customer"):
        return render(request, "core/home.html")
    

def search_view(request):
    query = request.GET.get("q")

    services = []

    if query:
        services = Service.objects.filter(title__icontains=query)
    else:
        services = Service.objects.all()

    return render(request, "core/search.html", {
        "services": services,
        "query": query
    })

def appointments_view(request):
    user = request.user

    if user.is_staff:
        appointments = Appointment.objects.all()

        return render(request, "core/appointments.html", {
            "appointments": appointments
        })
    
    elif hasattr(user, "barber"):
        appointments = Appointment.objects.filter(
            barber=request.user.barber
        )

        return render(request, "core/appointments.html", {
            "appointments": appointments
        })

    elif hasattr(user, "customer"):
        appointments = Appointment.objects.filter(
            customer=request.user.customer
        )

        return render(request, "core/appointments.html", {
            "appointments": appointments
        })

def account_view(request):
    return render(request, 'core/account.html')

@user_passes_test(is_admin)
def dashboard_view(request):
    return render(request, 'core/admin/dashboard.html')

@user_passes_test(is_admin)
def barbers_view(request):
    query = request.GET.get("q")

    barbers = []

    if query:
        barbers = Barber.objects.filter(user__username__icontains=query)
    else:
        barbers = Barber.objects.all()

    return render(request, 'core/admin/barbers.html', {
        "barbers": barbers
    })

@user_passes_test(is_admin)
def create_barber_view(request):

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = User.objects.create_user(
            username=name,
            email=email,
            password=password
        )

        Barber.objects.create(
            user=user
        )

    return redirect("barbers")

@user_passes_test(is_admin)
def services_view(request):
    query = request.GET.get("q")

    services = []

    if query:
        services = Service.objects.filter(title__icontains=query)
    else:
        services = Service.objects.all()

    return render(request, 'core/admin/services.html', {
        "services": services
    })

@user_passes_test(is_admin)
def create_service_view(request):

    if request.method == "POST":

        title = request.POST.get("title")
        price = request.POST.get("price")
        duration = request.POST.get("duration")

        if title and price and duration:
            Service.objects.create(
                title=title,
                price=Decimal(price),
                duration=int(duration)
            )

    return redirect("services")