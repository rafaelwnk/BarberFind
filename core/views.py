from decimal import Decimal
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from core.models import Appointment, Barber, Service
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from core.forms import AccountForm, BarberForm, ServiceForm, AppointmentForm

def is_admin(user):
    return user.is_staff

def index_view(request):
    if not request.user.is_authenticated:
        return redirect("/login")

    user = request.user

    if user.is_staff:
        return redirect("/dashboard")
    elif hasattr(user, "barber"):
        return render(request, "core/home_barber.html")
    elif hasattr(user, "customer"):
        return render(request, "core/home.html")
    else:
        return redirect("/login")

@login_required
def home_view(request):
    return index_view(request)
    
@login_required
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

@login_required
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

@login_required
def account_view(request):
    user = request.user
    form = AccountForm(request.POST or None, user=user, initial={
        "name": user.username,
        "email": user.email
    })

    if request.method == "POST" and form.is_valid():
        user.username = form.cleaned_data["name"]
        user.email = form.cleaned_data["email"]
        if form.cleaned_data["password"]:
            user.set_password(form.cleaned_data["password"])
            update_session_auth_hash(request, user)
        user.save()
        return redirect("account")

    return render(request, "core/account.html", {"form": form})

@login_required
@user_passes_test(is_admin)
def dashboard_view(request):
    return render(request, 'core/admin/dashboard.html')

@login_required
@user_passes_test(is_admin)
def barbers_view(request):
    query = request.GET.get("q")
    edit_id = request.GET.get("edit")
    delete_id = request.GET.get("delete")

    barbers = Barber.objects.filter(user__username__icontains=query) if query else Barber.objects.all()

    user_data = None
    form = BarberForm()

    if edit_id:
        barber = Barber.objects.get(id=edit_id)
        user_data = {"id": barber.id, "name": barber.user.username, "email": barber.user.email}
        form = BarberForm(initial={"name": barber.user.username, "email": barber.user.email}, barber=barber)

    delete_data = None
    if delete_id:
        barber = Barber.objects.get(id=delete_id)
        delete_data = {"id": barber.id, "name": barber.user.username}

    return render(request, "core/admin/barbers.html", {
        "barbers": barbers,
        "form": form,
        "user_data": user_data,
        "delete_data": delete_data
    })

@login_required
@user_passes_test(is_admin)
def create_barber_view(request):
    form = BarberForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"]
            )
            Barber.objects.create(user=user)
            return redirect("barbers")

        barbers = Barber.objects.all()
        return render(request, "core/admin/barbers.html", {
            "barbers": barbers,
            "form": form,
            "open_modal": True
        })

    return redirect("barbers")

@login_required
@user_passes_test(is_admin)
def edit_barber_view(request):
    if request.method == "POST":
        barber_id = request.POST.get("barber_id")
        barber = Barber.objects.get(id=barber_id)
        form = BarberForm(request.POST, barber=barber)

        if form.is_valid():
            barber.user.username = form.cleaned_data["name"]
            barber.user.email = form.cleaned_data["email"]
            if form.cleaned_data["password"]:
                barber.user.set_password(form.cleaned_data["password"])
            barber.user.save()
            return redirect("barbers")

        barbers = Barber.objects.all()
        return render(request, "core/admin/barbers.html", {
            "barbers": barbers,
            "form": form,
            "user_data": {"id": barber.id, "name": barber.user.username, "email": barber.user.email},
            "open_modal": True
        })

    return redirect("barbers")

@login_required
@user_passes_test(is_admin)
def delete_barber_view(request):
    if request.method == "POST":
        barber_id = request.POST.get("barber_id")
        barber = Barber.objects.get(id=barber_id)
        barber.user.delete()

    return redirect("barbers")

@login_required
@user_passes_test(is_admin)
def services_view(request):
    query = request.GET.get("q")
    edit_id = request.GET.get("edit")
    delete_id = request.GET.get("delete")

    services = Service.objects.filter(title__icontains=query) if query else Service.objects.all()

    service_data = None
    form = ServiceForm()

    if edit_id:
        service = Service.objects.get(id=edit_id)
        service_data = {"id": service.id, "title": service.title}
        form = ServiceForm(instance=service)

    delete_data = None
    if delete_id:
        service = Service.objects.get(id=delete_id)
        delete_data = {"id": service.id, "name": service.title}

    return render(request, "core/admin/services.html", {
        "services": services,
        "form": form,
        "service_data": service_data,
        "delete_data": delete_data
    })


@login_required
@user_passes_test(is_admin)
def create_service_view(request):
    form = ServiceForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("services")

        services = Service.objects.all()
        return render(request, "core/admin/services.html", {
            "services": services,
            "form": form,
            "open_modal": True
        })

    return redirect("services")


@login_required
@user_passes_test(is_admin)
def edit_service_view(request):
    if request.method == "POST":
        service_id = request.POST.get("service_id")
        service = Service.objects.get(id=service_id)
        form = ServiceForm(request.POST, instance=service)

        if form.is_valid():
            form.save()
            return redirect("services")

        services = Service.objects.all()
        return render(request, "core/admin/services.html", {
            "services": services,
            "form": form,
            "service_data": {"id": service.id, "title": service.title},
            "open_modal": True
        })

    return redirect("services")


@login_required
@user_passes_test(is_admin)
def delete_service_view(request):
    if request.method == "POST":
        service_id = request.POST.get("service_id")
        Service.objects.get(id=service_id).delete()

    return redirect("services")