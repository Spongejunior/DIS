from django.urls import include, path, re_path

from core import bridge

urlpatterns = [
    # JSON bridge for the Next.js frontend: /api/v1/page/<path> runs the view for <path>
    path('api/v1/page', bridge.api_page, name='api_page'),
    re_path(r'^api/v1/page/(?P<subpath>.*)$', bridge.api_page, name='api_page'),
    path('', include('core.urls')),
]

handler403 = 'core.bridge.forbidden'
handler404 = 'core.bridge.page_not_found'
handler500 = 'core.bridge.internal_server_error'
