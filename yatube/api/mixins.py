from rest_framework import viewsets

from .permissions import AuthorOrReadOnly


class CreateUpdateDeleteViewSet(viewsets.ModelViewSet):
    permission_classes = (AuthorOrReadOnly,)

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)
