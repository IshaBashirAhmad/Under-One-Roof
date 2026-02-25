from django.core.mail import send_mail
from django.conf import settings

def send_otp_email(email, otp_code, type):
    if type == 'signup':
        subject = 'Verify your email'
        message = f'Your signup OTP is: {otp_code}'
    else:
        subject = 'Reset your password'
        message = f'Your password reset OTP is: {otp_code}'

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )
