from django.utils import timezone
from rest_framework import serializers

from accounts.models import OTP, User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class EmailOTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()



class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    type = serializers.ChoiceField(choices=['signup', 'reset'])



class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email").lower()
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        # 1️⃣ Password match check
        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")

        # 2️⃣ User existence check
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found. Please verify OTP first.")

        # 3️⃣ OTP verified check
        otp_exists = OTP.objects.filter(
            user=user,
            type="signup",
            is_used=True,
            expires_at__gt=timezone.now()
        ).exists()

        if not otp_exists:
            raise serializers.ValidationError("Email is not verified.")

        # 4️⃣ Already registered check
        if user.is_active:
            raise serializers.ValidationError("User already registered.")

        data["user"] = user
        return data

    def create(self, validated_data):
        user = validated_data["user"]
        user.phone_number = validated_data["phone_number"]
        user.set_password(validated_data["password"])  # Hashing
        user.is_active = True
        user.is_verified = True
        user.role = "buyer"  # default role
        user.save()

        return user
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        data = super().validate(attrs)

        # Extra security checks
        if not self.user.is_verified:
            raise serializers.ValidationError("Email not verified.")

        if not self.user.is_active:
            raise serializers.ValidationError("Account inactive.")

        # Optional: Add extra user data in response
        data.update({
            "email": self.user.email,
            "role": self.user.role,
        })

        return data