from rest_framework import permissions

class IsOwnerOrDeveloper(permissions.BasePermission):
    """
    Permission class that allows only owners and developers to access.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['owner', 'developer']