from django.contrib import admin

from .models import Project, Bug


class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['is_active']


class BugAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'title', 'project']
    readonly_fields = fields = [
        'created_at', 'title', 'project', 'assigned_to', 'created_by',
        'priority', 'state',
    ]
    date_hierarchy = 'created_at'

admin.site.register(Project, ProjectAdmin)
admin.site.register(Bug, BugAdmin)
