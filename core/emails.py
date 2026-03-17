from django.core.mail import send_mail
from django.conf import settings

def send_appointment_created(appointment):
    send_mail(
        subject="Agendamento confirmado!",
        message=f"""
Olá, {appointment.customer}!

Seu agendamento foi confirmado com sucesso.

Barbeiro: {appointment.barber}
Data: {appointment.date}
Hora: {appointment.time}
Serviços: {', '.join([s.title for s in appointment.services.all()])}
Pagamento: {appointment.get_payment_method_display()}

Até logo!
        """,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[appointment.customer.user.email],
    )

def send_appointment_cancelled(appointment):
    send_mail(
        subject="Agendamento cancelado",
        message=f"""
Olá, {appointment.customer}!

Seu agendamento foi cancelado.

Barbeiro: {appointment.barber}
Data: {appointment.date}
Hora: {appointment.time}

Se tiver dúvidas, entre em contato.
        """,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[appointment.customer.user.email],
    )