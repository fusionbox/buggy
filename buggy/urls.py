from django.conf.urls import url

from . import views


app_name = 'buggy'
urlpatterns = [
    url(r'^$', views.BugListView.as_view(), name='bug_list'),
    url(r'^(?P<bug_number>\d+)/$', views.BugDetailView.as_view(), name='bug_detail'),
]
