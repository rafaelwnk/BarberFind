from django import forms
from django.contrib.auth.models import User
from core.models import Barber, Service, Appointment

FORM_CONTROL = {"class": "form-control"}
FORM_SELECT = {"class": "form-select"}


class BarberForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs=FORM_CONTROL)
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs=FORM_CONTROL)
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs=FORM_CONTROL)
    )

    def __init__(self, *args, barber=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.barber = barber

        if barber:
            self.fields["password"].required = False

    def clean_name(self):
        name = self.cleaned_data.get("name")
        qs = User.objects.filter(username=name)
        if self.barber:
            qs = qs.exclude(id=self.barber.user.id)
        if qs.exists():
            raise forms.ValidationError("Este nome já está em uso.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get("email")
        qs = User.objects.filter(email=email)
        if self.barber:
            qs = qs.exclude(id=self.barber.user.id)
        if qs.exists():
            raise forms.ValidationError("Este email já está em uso.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not self.barber and not password:
            raise forms.ValidationError("A senha é obrigatória.")
        return password


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["title", "price", "duration"]
        widgets = {
            "title": forms.TextInput(attrs=FORM_CONTROL),
            "price": forms.NumberInput(attrs={**FORM_CONTROL, "step": "0.01"}),
            "duration": forms.NumberInput(attrs=FORM_CONTROL),
        }
        labels = {
            "title": "Título",
            "price": "Preço",
            "duration": "Duração (minutos)",
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["customer", "barber", "date", "time", "services", "status"]
        widgets = {
            "customer": forms.Select(attrs=FORM_SELECT),
            "barber": forms.Select(attrs=FORM_SELECT),
            "date": forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
            "time": forms.TimeInput(attrs={**FORM_CONTROL, "type": "time"}),
            "services": forms.SelectMultiple(attrs=FORM_SELECT),
            "status": forms.Select(attrs=FORM_SELECT),
        }
        labels = {
            "customer": "Cliente",
            "barber": "Barbeiro",
            "date": "Data",
            "time": "Hora",
            "services": "Serviços",
            "status": "Status",
        }


class AccountForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs=FORM_CONTROL)
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs=FORM_CONTROL)
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs=FORM_CONTROL)
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_name(self):
        name = self.cleaned_data.get("name")
        qs = User.objects.filter(username=name)
        if self.user:
            qs = qs.exclude(id=self.user.id)
        if qs.exists():
            raise forms.ValidationError("Este nome já está em uso.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get("email")
        qs = User.objects.filter(email=email)
        if self.user:
            qs = qs.exclude(id=self.user.id)
        if qs.exists():
            raise forms.ValidationError("Este email já está em uso.")
        return email