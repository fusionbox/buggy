"""buggy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.conf import settings
from django.contrib import admin
import authtools.views

import buggy.urls


urlpatterns = [
    url(r'^', include(buggy.urls)),
    url(r'^admin/', admin.site.urls),

    url(r'^login/$', authtools.views.LoginView.as_view(), name='login'),
    url(r'^logout/$', authtools.views.LogoutView.as_view(pattern_name='login'), name='logout'),
    url(r'^password_change/$', authtools.views.PasswordChangeView.as_view(), name='password_change'),
    url(r'^password_change/done/$', authtools.views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    url(r'^password_reset/$', authtools.views.PasswordResetView.as_view(), name='password_reset'),
    url(r'^password_reset/done/$', authtools.views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    url(r'^reset/done/$', authtools.views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        authtools.views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
