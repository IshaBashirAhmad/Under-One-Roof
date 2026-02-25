from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

from accounts.serializers import EmailOTPRequestSerializer, OTPVerifySerializer, RegisterSerializer
from accounts.utils.otp import generate_otp
from accounts.utils.email import send_otp_email
from accounts.models import OTP
from django.utils import timezone

User = get_user_model()

class SendOTPView(APIView):
    def post(self, request):
        serializer = EmailOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        type = request.query_params.get('type')

        if type not in ['signup', 'reset']:
            return Response(
                {'detail': 'Invalid type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "is_active": False,
                "is_verified": False
            }
        )

        otp_code = generate_otp(user, type)
        send_otp_email(email, otp_code, type)

        return Response(
            {'detail': 'OTP sent successfully'},
            status=status.HTTP_200_OK
        )


class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        type = serializer.validated_data['type']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            otp = OTP.objects.get(
                user=user,
                otp_code=otp_code,
                type=type,
                is_used=False
            )
        except OTP.DoesNotExist:
            return Response(
                {'detail': 'Invalid OTP'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp.expires_at < timezone.now():
            return Response(
                {'detail': 'OTP expired'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark OTP as used
        otp.is_used = True
        otp.save()

        # Signup case
        if type == 'signup':
            user.is_verified = True
            user.save()

        return Response(
            {'detail': 'OTP verified successfully'},
            status=status.HTTP_200_OK
        )
    

class RegisterView(APIView):

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Registration successful. Please login."},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)