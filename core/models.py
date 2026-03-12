from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Barber(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="barber"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Service(models.Model):
    title = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    duration = models.PositiveIntegerField(
        help_text="Duration in minutes"
    )

    barbers = models.ManyToManyField(Barber, blank=True)

    def __str__(self):
        return self.title


class Appointment(models.Model):

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    barber = models.ForeignKey(Barber, on_delete=models.CASCADE)

    date = models.DateField()
    time = models.TimeField()

    services = models.ManyToManyField(Service)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} - {self.date} {self.time}"