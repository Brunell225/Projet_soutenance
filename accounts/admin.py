from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User  # Ton modèle utilisateur personnalisé

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'company_name', 'whatsapp_number',
        'is_business_account', 'is_platform_admin', 'is_active', 'is_staff'
    )
    list_filter = ('is_active', 'is_business_account', 'is_platform_admin', 'is_staff')
    search_fields = ('username', 'email', 'company_name', 'whatsapp_number')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Informations professionnelles'), {
            'fields': (
                'company_name',
                'whatsapp_number',
                'whatsapp_api_token',
                'phone_number_id',
                'business_id',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'is_business_account', 'is_platform_admin',
                'groups', 'user_permissions',
            )
        }),
        (_('Autres infos'), {'fields': ('last_login', 'has_completed_tutorial', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'company_name', 'whatsapp_number',
                'whatsapp_api_token', 'phone_number_id', 'business_id',
                'is_business_account', 'is_platform_admin',
            ),
        }),
    )
