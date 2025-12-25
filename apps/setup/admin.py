from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, Team


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    ordering = ('username',)
    list_display = (
        'username',
        'first_name',
        'last_name',
        'role',
        'contract_type',
        'is_active',
        'is_staff',
    )
    list_filter = ('role', 'contract_type', 'is_active', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'phone')
    filter_horizontal = ('teams', 'groups', 'user_permissions')

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('username', 'password')
        }),
        ('اطلاعات شخصی', {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        ('سازمانی', {
            'fields': ('role', 'contract_type', 'teams')
        }),
        ('دسترسی‌ها', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    readonly_fields = ()

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)
    search_fields = ('name',)
