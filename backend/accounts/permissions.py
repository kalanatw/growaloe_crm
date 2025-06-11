from rest_framework import permissions


class IsOwnerOrDeveloper(permissions.BasePermission):
    """
    Permission class that allows access only to owners and developers
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['owner', 'developer']
        )


class IsAuthenticated(permissions.BasePermission):
    """
    Permission class that allows access to authenticated users
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows owners to do anything, others to read only
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.role in ['owner', 'developer']:
            return True
        
        # Read permissions for all authenticated users
        return request.method in permissions.SAFE_METHODS


class IsSalesmanOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows salesmen to modify their own data, others to read only
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.role in ['owner', 'developer']:
            return True
        
        if request.user.role == 'salesman':
            return True
        
        # Read permissions for shops
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions for owners and developers
        if request.user.role in ['owner', 'developer']:
            return True
        
        # Salesmen can only modify their own data
        if request.user.role == 'salesman':
            return hasattr(obj, 'user') and obj.user == request.user
        
        return False


class IsShopOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows shops to modify their own data, others to read only
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.role in ['owner', 'developer']:
            return True
        
        if request.user.role == 'shop':
            return True
        
        # Read permissions for salesmen
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions for owners and developers
        if request.user.role in ['owner', 'developer']:
            return True
        
        # Shops can only modify their own data
        if request.user.role == 'shop':
            return hasattr(obj, 'user') and obj.user == request.user
        
        return False


class IsSameUserOrOwner(permissions.BasePermission):
    """
    Permission class that allows users to modify their own data or owners to modify anyone's
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions for owners and developers
        if request.user.role in ['owner', 'developer']:
            return True
        
        # Users can modify their own data
        return obj == request.user or (hasattr(obj, 'user') and obj.user == request.user)


class IsOwnerOrSameUser(permissions.BasePermission):
    """
    Permission class that allows access to owners or the same user
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Owners and developers can access everything
        if request.user.role in ['owner', 'developer']:
            return True
        
        # Users can access their own data
        return obj == request.user or (hasattr(obj, 'user') and obj.user == request.user)


class CanManageStock(permissions.BasePermission):
    """
    Permission class for stock management operations
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Owners and developers can manage all stock
        if request.user.role in ['owner', 'developer']:
            return True
        
        # Salesmen can view their own stock
        if request.user.role == 'salesman' and request.method in permissions.SAFE_METHODS:
            return True
        
        return False


class CanCreateInvoices(permissions.BasePermission):
    """
    Permission class for invoice creation
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # All authenticated users can view invoices (filtered by their role)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Owners, developers, and salesmen can create invoices
        return request.user.role in ['OWNER', 'DEVELOPER', 'SALESMAN']


class CanProcessPayments(permissions.BasePermission):
    """
    Permission class for payment processing
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # All authenticated users can view transactions (filtered by their role)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Owners, developers, salesmen, and shops can process payments
        return request.user.role in ['OWNER', 'DEVELOPER', 'SALESMAN', 'SHOP']


class CanViewReports(permissions.BasePermission):
    """
    Permission class for viewing reports
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # All authenticated users can view reports (filtered by their role)
        return True


class CanGenerateReports(permissions.BasePermission):
    """
    Permission class for generating reports
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Only owners and developers can generate reports
        return request.user.role in ['OWNER', 'DEVELOPER']
