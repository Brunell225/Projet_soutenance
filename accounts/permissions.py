from rest_framework.permissions import BasePermission


class IsPlatformAdmin(BasePermission):
    """
    Autorise uniquement les utilisateurs avec le rôle d'administrateur de la plateforme.
    """

    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.is_platform_admin
        )


class IsSuperAdmin(BasePermission):
    """
    Autorise uniquement les superutilisateurs Django (is_superuser=True).
    """

    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.is_superuser
        )


class IsVendeur(BasePermission):
    """
    Autorise uniquement les utilisateurs considérés comme vendeurs :
    - Authentifiés
    - Non superutilisateurs
    - Non admins plateforme
    """

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and not user.is_superuser
            and not getattr(user, 'is_platform_admin', False)
        )
