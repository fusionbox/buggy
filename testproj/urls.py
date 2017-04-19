from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

import buggy.urls
import buggy_accounts.urls


urlpatterns = [
    url(r'^', include(buggy.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include(buggy_accounts.urls)),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
