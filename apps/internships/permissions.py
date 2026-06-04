from rest_framework.permissions import BasePermission


class IsCompanyUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'company'


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and obj.company.user == request.user
