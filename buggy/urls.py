from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from . import views


app_name = 'buggy'
urlpatterns = [
    url(r'^$', views.BugListView.as_view(), name='bug_list'),
    url(r'^(?P<bug_number>\d+)/$', views.BugDetailView.as_view(), name='bug_detail'),
    url(r'^add-preset/$', views.AddPresetView.as_view(), name='add_preset'),
    url(r'^remove-preset/(?P<pk>\d+)/$', views.RemovePresetView.as_view(), name='remove_preset'),
    url(r'^create/$', views.BugCreateView.as_view(), name='bug_create'),
    url(r'^markdown-preview/$',
        csrf_exempt(views.MarkdownPreviewView.as_view()),
        name='markdown_preview'),
    url(r'^git-commit-webhook/$',
        csrf_exempt(views.GitCommitWebhookView.as_view()),
        name='git_commit_webhook')
]
