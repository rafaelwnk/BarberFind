from django.contrib import admin
from django.urls import path

from core.views import account_view, history_view, home_view, login_view, register_view, search_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('home/', home_view, name='home'),
    path('search/', search_view, name='search'),
    path('history/', history_view, name='history'),
    path('account/', account_view, name='account')
]
