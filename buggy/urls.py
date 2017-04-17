from django.conf.urls import url

from . import views


app_name = 'buggy'
urlpatterns = [
    url(r'^$', views.BugListView.as_view(), name='bug_list'),
    url(r'^(?P<bug_number>\d+)/$', views.BugDetailView.as_view(), name='bug_detail'),
    url(r'^add-preset/$', views.AddPresetView.as_view(), name='add_preset'),
    url(r'^remove-preset/(?P<pk>\d+)/$', views.RemovePresetView.as_view(), name='remove_preset'),
]
