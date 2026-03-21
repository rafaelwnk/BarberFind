from django.contrib import admin
from django.urls import path

from core.views import account_view, appointments_view, barber_services_view, cancel_appointment_view, delete_barber_view, delete_service_view, edit_barber_view, edit_service_view, home_barber_view, home_view, index_view, payment_failure_view, payment_pix_confirm_view, payment_pix_view, payment_success_view, payment_view, reports_view, search_view, dashboard_view, barbers_view, create_barber_view, services_view, create_service_view
from accounts.views import login_view, register_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_view, name='index'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('home/', home_view, name='home'),
    path("home/barber/", home_barber_view, name="home_barber"),
    path('search/', search_view, name='search'),
    path('appointments/', appointments_view, name='appointments'),
    path("appointments/cancel/", cancel_appointment_view, name="cancel_appointment"),
    path('account/', account_view, name='account'),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("barbers/", barbers_view, name="barbers"),
    path("barbers/create/", create_barber_view, name="create_barber"),
    path("barbers/edit/", edit_barber_view, name="edit_barber"),
    path("barbers/delete/", delete_barber_view, name="delete_barber"),
    path("services/", services_view, name="services"),
    path("services/me", barber_services_view, name="barber_services"),
    path("services/create/", create_service_view, name="create_service"),
    path("services/edit/", edit_service_view, name="edit_service"),
    path("services/delete/", delete_service_view, name="delete_service"),
    path("reports/", reports_view, name="reports"),
    path("payment/<int:appointment_id>/", payment_view, name="payment"),
    path("payment/pix/<int:appointment_id>/", payment_pix_view, name="payment_pix"),
    path("payment/pix/confirm/<int:appointment_id>/", payment_pix_confirm_view, name="payment_pix_confirm"),
    path("payment/success/<int:appointment_id>/", payment_success_view, name="payment_success"),
    path("payment/failure/<int:appointment_id>/", payment_failure_view, name="payment_failure"),
]
