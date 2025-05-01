from django.contrib import admin
from .models import *

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('full_name', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('full_name', 'role')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'hod')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

# admin.site.register(Task)
admin.site.register(Report)
# admin.site.register(ReportTemplate)
# # admin.site.unregister(Comment)
# admin.site.register(Comment)
# admin.site.register(ApprovalFlow)
# admin.site.register(ApprovalFlowHistory)
# # admin.site.register(Analytics)
admin.site.register(AcademicYear)