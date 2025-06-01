from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import ValidationError
from .models import User
import logging

logger = logging.getLogger(__name__)  # 🔍 Pour les logs

# ✅ Validation du numéro WhatsApp
def validate_whatsapp_number(value):
    if not value.startswith('+') or not value[1:].isdigit():
        raise ValidationError("Le numéro WhatsApp doit commencer par + et contenir uniquement des chiffres.")
    return value

class UserSerializer(serializers.ModelSerializer):
    """
    Affichage des infos de l'utilisateur.
    """
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'company_name',
            'whatsapp_number',
            'is_business_account',
            'whatsapp_api_token',
            'phone_number_id',
            'business_id',
        )
        read_only_fields = ('id', 'is_business_account')

class RegisterSerializer(serializers.ModelSerializer):
    """
    Inscription d'un utilisateur.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    whatsapp_number = serializers.CharField(validators=[validate_whatsapp_number])

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'company_name',
            'whatsapp_number',
            'password',
            'password2'
        )

    def validate(self, attrs):
        logger.info("🔍 [Register] Données reçues pour validation : %s", attrs)  # 🔍
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        logger.info("✅ [Register] Données validées pour création : %s", validated_data)  # 🔍
        validated_data.pop('password2')
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            company_name=validated_data['company_name'],
            whatsapp_number=validated_data['whatsapp_number']
        )
        user.set_password(validated_data['password'])
        user.save()
        logger.info("🎉 [Register] Utilisateur créé avec succès : %s", user.id)  # 🔍
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Mise à jour des infos liées à l'API WhatsApp.
    """
    whatsapp_number = serializers.CharField(validators=[validate_whatsapp_number], required=False)

    class Meta:
        model = User
        fields = (
            'company_name',
            'whatsapp_number',
            'whatsapp_api_token',
            'phone_number_id',
            'business_id'
        )
