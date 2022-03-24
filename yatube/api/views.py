from django.shortcuts import get_object_or_404
from rest_framework import filters, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated

from .mixins import CreateUpdateDeleteViewSet
from posts.models import Comment, Follow, Group, Post
from .serializers import (CommentSerializer,
                          FollowSerializer,
                          GroupSerializer,
                          PostSerializer)


class PostViewSet(CreateUpdateDeleteViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    pagination_class = LimitOffsetPagination


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class CommentViewSet(CreateUpdateDeleteViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        post = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        comments = Comment.objects.filter(post=post.id)
        return comments


class FollowViewSet(CreateUpdateDeleteViewSet):
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('=user__username', '=author__username')

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)
