"""
Django Admin Configuration for Core App.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    User,
    SocialAccount,
    ChildProfile,
    ParentalRule,
    RuleViolation,
    NetworkDevice,
    NetworkScanLog,
    AppPrivacyProfile,
    PrivacyCheck,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""

    list_display = ['email', 'full_name', 'is_parent', 'is_staff', 'date_joined']
    list_filter = ['is_parent', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'full_name']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'avatar_url', 'is_parent')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'is_parent'),
        }),
    )


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'provider', 'provider_user_id', 'created_at']
    list_filter = ['provider']
    search_fields = ['user__email', 'provider_user_id']


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'age', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'user__email']


@admin.register(ParentalRule)
class ParentalRuleAdmin(admin.ModelAdmin):
    list_display = ['rule_type', 'child', 'parent', 'is_active', 'created_at']
    list_filter = ['rule_type', 'is_active']
    search_fields = ['child__name', 'parent__email', 'app_package_name']


@admin.register(RuleViolation)
class RuleViolationAdmin(admin.ModelAdmin):
    list_display = ['child', 'rule', 'occurred_at']
    list_filter = ['occurred_at']
    search_fields = ['child__name', 'description']


@admin.register(NetworkDevice)
class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'ip_address', 'mac_address', 'device_type', 'is_trusted', 'is_blocked', 'owner']
    list_filter = ['device_type', 'is_trusted', 'is_blocked']
    search_fields = ['name', 'ip_address', 'mac_address', 'owner__email']


@admin.register(NetworkScanLog)
class NetworkScanLogAdmin(admin.ModelAdmin):
    list_display = ['owner', 'network_ssid', 'created_at']
    list_filter = ['created_at']
    search_fields = ['owner__email', 'network_ssid']


@admin.register(AppPrivacyProfile)
class AppPrivacyProfileAdmin(admin.ModelAdmin):
    list_display = ['app_name', 'package_name', 'category', 'baseline_privacy_score']
    list_filter = ['category']
    search_fields = ['app_name', 'package_name']


@admin.register(PrivacyCheck)
class PrivacyCheckAdmin(admin.ModelAdmin):
    list_display = ['app_name', 'user', 'calculated_privacy_score', 'suggested_action', 'created_at']
    list_filter = ['suggested_action', 'network_usage_level', 'created_at']
    search_fields = ['app_name', 'app_package_name', 'user__email']
