from django.contrib import admin
from django.urls import path

from core.views import account_view, appointments_view, home_view, search_view, dashboard_view, barbers_view, create_barber_view, services_view, create_service_view
from accounts.views import login_view, register_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('home/', home_view, name='home'),
    path('search/', search_view, name='search'),
    path('appointments/', appointments_view, name='appointments'),
    path('account/', account_view, name='account'),
    path("dashboard", dashboard_view, name="dashboard"),
    path("barbers", barbers_view, name="barbers"),
    path("barbers/create/", create_barber_view, name="create_barber"),
    path("services", services_view, name="services"),
    path("services/create/", create_service_view, name="create_service")
]
