from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CommentViewSet,
                    FollowViewSet,
                    GroupViewSet,
                    PostViewSet)

app_name = 'api'

router = DefaultRouter()
router.register(r'posts', PostViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'posts/(?P<post_id>[0-9]+)/comments',
                CommentViewSet,
                basename='comments')
router.register(r'follow', FollowViewSet, basename='follow')

urlpatterns = [
    path('v1/', include('djoser.urls')),
    path('v1/', include('djoser.urls.jwt')),
    path('v1/', include(router.urls))
]
