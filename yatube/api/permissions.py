from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

ERROR_MESSAGES = {
    'update_denied': 'Изменение чужого контента запрещено!',
    'delete_denied': 'Удаление чужого контента запрещено!'
}


class AuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        if obj.author != request.user:
            if request.method in ['PUT', 'PATCH']:
                raise PermissionDenied(ERROR_MESSAGES['update_denied'])
            if request.method in ['DELETE']:
                raise PermissionDenied(ERROR_MESSAGES['delete_denied'])
        return True
