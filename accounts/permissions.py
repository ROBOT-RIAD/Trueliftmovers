from rest_framework.permissions import BasePermission,SAFE_METHODS



class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        print("Role:", getattr(request.user, 'role', None))
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'admin'
    


class IsOwnerRole(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'user'
    