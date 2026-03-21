from django.utils import timezone
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from core.models import Appointment, Barber, Service
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from core.forms import AccountForm, BarberForm, ServiceForm
from core.emails import send_appointment_created, send_appointment_cancelled
from django.conf import settings
from urllib.parse import quote
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import TruncMonth
import json
import mercadopago

def is_admin(user):
    return user.is_staff

def is_barber(user):
    return hasattr(user, "barber")

def is_admin_or_barber(user):
    return is_admin(user) or is_barber(user)

def index_view(request):
    if not request.user.is_authenticated:
        return redirect("/login")

    user = request.user

    if user.is_staff:
        return redirect("/dashboard")
    elif hasattr(user, "barber"):
        return redirect("home_barber")
    elif hasattr(user, "customer"):
        return redirect("home")
    else:
        return redirect("/login")

@login_required
def home_view(request):
    user = request.user

    if not hasattr(user, "customer"):
        return index_view(request)

    next_appointment = Appointment.objects.filter(
        customer=user.customer,
        status="scheduled",
        date__gte=timezone.now().date()
    ).order_by("date", "time").first()

    total_appointments = Appointment.objects.filter(
        customer=user.customer,
        status="completed"
    ).count()

    return render(request, "core/home.html", {
        "next_appointment": next_appointment,
        "total_appointments": total_appointments,
    })

@login_required
@user_passes_test(is_barber)
def home_barber_view(request):
    barber = request.user.barber
    today = timezone.now().date()

    next_appointment = Appointment.objects.filter(
        barber=barber,
        status="scheduled",
        date=today
    ).order_by("time").first()

    total_today = Appointment.objects.filter(
        barber=barber,
        status="scheduled",
        date=today
    ).count()

    return render(request, "core/barber/home.html", {
        "next_appointment": next_appointment,
        "total_today": total_today,
    })

@login_required
def search_view(request):
    query = request.GET.get("q")
    services_qs = Service.objects.filter(title__icontains=query) if query else Service.objects.all()

    if request.method == "POST":
        service_id = request.POST.get("service_id")
        barber_id = request.POST.get("barber")
        date = request.POST.get("date")
        time = request.POST.get("time")
        payment_method = request.POST.get("payment_method")

        appointment = Appointment.objects.create(
            customer=request.user.customer,
            barber=Barber.objects.get(id=barber_id),
            date=date,
            time=time,
            payment_method=payment_method,
            status="pending"
        )
        appointment.services.add(service_id)

        if payment_method == "cash":
            appointment.status = "scheduled"
            appointment.save()
            send_appointment_created(appointment)
            return redirect("appointments")
        elif payment_method == "pix":
            return redirect("payment_pix", appointment_id=appointment.id)
        elif payment_method == "card":
            return redirect("payment", appointment_id=appointment.id)

    paginator = Paginator(services_qs, 9)
    page = request.GET.get("page")
    services = paginator.get_page(page)

    return render(request, "core/search.html", {
        "services": services,
        "query": query
    })

@login_required
def appointments_view(request):
    user = request.user
    barbers = Barber.objects.all()

    if user.is_staff:
        appointments = Appointment.objects.all()
    elif hasattr(user, "barber"):
        appointments = Appointment.objects.filter(barber=request.user.barber)
    elif hasattr(user, "customer"):
        appointments = Appointment.objects.filter(customer=request.user.customer)

    paginator = Paginator(appointments.order_by("-date"), 9)
    page = request.GET.get("page")
    appointments_page = paginator.get_page(page)

    return render(request, "core/appointments.html", {
        "appointments": appointments_page,
        "barbers": barbers
    })

@login_required
def confirm_appointment_view(request):
    if request.method == "POST":
        appointment_id = request.POST.get("appointment_id")
        appointment = Appointment.objects.get(id=appointment_id, customer=request.user.customer)
        appointment.barber = Barber.objects.get(id=request.POST.get("barber"))
        appointment.date = request.POST.get("date")
        appointment.time = request.POST.get("time")
        appointment.payment_method = request.POST.get("payment_method")
        appointment.status = "scheduled"
        appointment.save()
    return redirect("appointments")

@login_required
def cancel_appointment_view(request):
    if request.method == "POST":
        appointment_id = request.POST.get("appointment_id")
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.status = "cancelled"
        appointment.save()
        send_appointment_cancelled(appointment)
    return redirect("appointments")

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
    STATUS_MAP = {
        "scheduled": "Agendado",
        "completed": "Concluído",
        "cancelled": "Cancelado",
        "pending": "Pendente",
    }

    status_data = Appointment.objects.values("status").annotate(total=Count("id"))
    status_labels = [STATUS_MAP.get(d["status"], d["status"]) for d in status_data]
    status_values = [d["total"] for d in status_data]

    barber_data = (
        Appointment.objects
        .values("barber__user__username")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )
    barber_labels = [d["barber__user__username"] for d in barber_data]
    barber_values = [d["total"] for d in barber_data]

    month_data = (
        Appointment.objects
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    month_labels = [d["month"].strftime("%b/%Y") for d in month_data]
    month_values = [d["total"] for d in month_data]

    return render(request, 'core/admin/dashboard.html', {
        "total_barbers": Barber.objects.count(),
        "total_services": Service.objects.count(),
        "total_appointments": Appointment.objects.count(),
        "recent_appointments": Appointment.objects.order_by("-created_at")[:5],
        "status_labels": json.dumps(status_labels),
        "status_values": json.dumps(status_values),
        "barber_labels": json.dumps(barber_labels),
        "barber_values": json.dumps(barber_values),
        "month_labels": json.dumps(month_labels),
        "month_values": json.dumps(month_values),
    })

@login_required
@user_passes_test(is_admin)
def barbers_view(request):
    query = request.GET.get("q")
    edit_id = request.GET.get("edit")
    delete_id = request.GET.get("delete")
    services_id = request.GET.get("services")

    barbers_qs = Barber.objects.filter(user__username__icontains=query) if query else Barber.objects.all()

    paginator = Paginator(barbers_qs, 9)
    page = request.GET.get("page")
    barbers = paginator.get_page(page)

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

    barber_services = None
    if services_id:
        barber_services = Barber.objects.get(id=services_id)

    return render(request, "core/admin/barbers.html", {
        "barbers": barbers,
        "form": form,
        "user_data": user_data,
        "delete_data": delete_data,
        "barber_services": barber_services
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

    services_qs = Service.objects.filter(title__icontains=query) if query else Service.objects.all()

    paginator = Paginator(services_qs, 9)
    page = request.GET.get("page")
    services = paginator.get_page(page)

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

@login_required
@user_passes_test(is_barber)
def barber_services_view(request):
    barber = request.user.barber
    all_services = Service.objects.all()

    if request.method == "POST":
        selected_ids = request.POST.getlist("services")
        barber.services.set(selected_ids)
        return redirect("barber_services")

    barber_services = barber.services.all()

    paginator = Paginator(barber_services, 9)
    page = request.GET.get("page")
    barber_services_page = paginator.get_page(page)

    return render(request, "core/barber/barber_services.html", {
        "all_services": all_services,
        "barber_services": barber_services_page,
        "barber_service_ids": list(barber.services.values_list("id", flat=True))
    })

@login_required
@user_passes_test(is_admin_or_barber)
def reports_view(request):
    user = request.user

    appointments = Appointment.objects.all()

    if hasattr(user, "barber"):
        appointments = appointments.filter(barber=user.barber)

    status = request.GET.get("status")
    barber_id = request.GET.get("barber")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    if status:
        appointments = appointments.filter(status=status)
    if barber_id and user.is_staff:
        appointments = appointments.filter(barber__id=barber_id)
    if date_from:
        appointments = appointments.filter(date__gte=date_from)
    if date_to:
        appointments = appointments.filter(date__lte=date_to)

    total = appointments.count()
    total_scheduled = appointments.filter(status="scheduled").count()
    total_completed = appointments.filter(status="completed").count()
    total_cancelled = appointments.filter(status="cancelled").count()

    paginator = Paginator(appointments.order_by("-date"), 10)
    page = request.GET.get("page")
    appointments_page = paginator.get_page(page)

    return render(request, "core/barber/reports.html", {
        "appointments": appointments_page,
        "barbers": Barber.objects.all(),
        "total": total,
        "total_scheduled": total_scheduled,
        "total_completed": total_completed,
        "total_cancelled": total_cancelled,
        "filters": {
            "status": status,
            "barber": int(barber_id) if barber_id else None,
            "date_from": date_from,
            "date_to": date_to,
        }
    })

@login_required
def payment_pix_view(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id, customer=request.user.customer)

    total = sum(s.price for s in appointment.services.all())
    amount = f"{float(total):.2f}"

    pix_key = settings.PIX_KEY
    receiver_name = settings.PIX_RECEIVER_NAME
    city = settings.PIX_CITY

    def pix_field(id, value):
        return f"{id:02d}{len(value):02d}{value}"

    merchant_account = pix_field(0, "BR.GOV.BCB.PIX") + pix_field(1, pix_key)
    merchant_account_info = pix_field(26, merchant_account)

    payload = (
        pix_field(0, "01") +
        pix_field(1, "12") +
        merchant_account_info +
        pix_field(52, "0000") +
        pix_field(53, "986") +
        pix_field(54, amount) +
        pix_field(58, "BR") +
        pix_field(59, receiver_name[:25]) +
        pix_field(60, city[:15]) +
        pix_field(62, pix_field(5, "***"))
    )

    def crc16(data):
        crc = 0xFFFF
        for char in data:
            crc ^= ord(char) << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return crc

    payload_with_crc = payload + "6304"
    crc = crc16(payload_with_crc)
    pix_payload = payload_with_crc + f"{crc:04X}"

    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={quote(pix_payload)}"

    return render(request, "core/pix_payment.html", {
        "appointment": appointment,
        "qr_url": qr_url,
        "pix_key": pix_key,
        "total": amount,
    })


@login_required
def payment_pix_confirm_view(request, appointment_id):
    if request.method == "POST":
        appointment = Appointment.objects.get(id=appointment_id, customer=request.user.customer)
        appointment.status = "scheduled"
        appointment.save()
        send_appointment_created(appointment)
        return redirect("appointments")
    return redirect("search")

@login_required
def payment_view(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id, customer=request.user.customer)

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    total = sum(s.price for s in appointment.services.all())

    preference_data = {
        "items": [
            {
                "title": f"Agendamento - {appointment.barber}",
                "quantity": 1,
                "unit_price": float(total),
            }
        ],
        "back_urls": {
            "success": request.build_absolute_uri(f"/payment/success/{appointment.id}/"),
            "failure": request.build_absolute_uri(f"/payment/failure/{appointment.id}/"),
            "pending": request.build_absolute_uri(f"/payment/failure/{appointment.id}/"),
        },
    }

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    return redirect(preference["init_point"])

@login_required
def payment_success_view(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.status = "scheduled"
    appointment.save()
    send_appointment_created(appointment)
    return redirect("appointments")


@login_required
def payment_failure_view(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.delete()
    return redirect("search")