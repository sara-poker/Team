from django.contrib import admin
from .models import Project, Task, TaskComment


# ==========================
# Inline برای Task داخل Project
# ==========================
class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ('title', 'status', 'percent', 'deadline')
    show_change_link = True


# ==========================
# Inline برای TaskComment داخل Task
# ==========================
class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    readonly_fields = ('created_at',)
    show_change_link = True


# ==========================
# Project Admin
# ==========================
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'title',
        'status',
        'get_progress',
        'start_date',
        'end_date',
    )
    list_filter = ('status', 'teams')
    search_fields = ('code', 'title', 'description')
    filter_horizontal = ('members', 'teams')
    inlines = (TaskInline,)
    list_per_page = 25

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('code', 'title', 'description', 'status')
        }),
        ('زمان‌بندی', {
            'fields': ('start_date', 'end_date')
        }),
        ('اعضا و تیم‌ها', {
            'fields': ('members', 'teams','created_by')
        })
    )

    def get_progress(self, obj):
        return f"{obj.get_project_progress():.1f}%"
    get_progress.short_description = 'پیشرفت پروژه'


# ==========================
# Task Admin
# ==========================
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'project',
        'status',
        'percent',
        'deadline',
        'weight',
        'approval_status',
        'created_by',
    )
    list_filter = (
        'status',
        'approval_status',
        'project',
    )
    search_fields = ('title', 'description')
    filter_horizontal = ('assignees',)
    autocomplete_fields = ('project', 'created_by')
    inlines = (TaskCommentInline,)  # حتما کاما داشته باشد
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'description', 'project')
        }),
        ('وضعیت', {
            'fields': ('status', 'percent', 'approval_status', 'weight')
        }),
        ('زمان‌بندی', {
            'fields': ('start_date', 'end_date', 'deadline')
        }),
        ('اعضا', {
            'fields': ('assignees', 'created_by')
        }),
        ('سیستمی', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# ==========================
# TaskComment Admin
# ==========================
@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'created_at')
    search_fields = ('text',)
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
