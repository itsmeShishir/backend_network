"""
Core models for Antygravity Backend.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


# =============================================================================
# User & Authentication Models
# =============================================================================

class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model using email as the primary identifier."""

    email = models.EmailField(
        unique=True,
        max_length=255,
        verbose_name='email address'
    )
    full_name = models.CharField(max_length=255, blank=True, default='')
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    is_parent = models.BooleanField(default=True)

    # Django required fields
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.full_name or self.email

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email.split('@')[0]


class SocialAccount(models.Model):
    """Social login provider account linked to a user."""

    class Provider(models.TextChoices):
        GOOGLE = 'GOOGLE', 'Google'
        APPLE = 'APPLE', 'Apple'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='social_accounts'
    )
    provider = models.CharField(
        max_length=20,
        choices=Provider.choices
    )
    provider_user_id = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'social account'
        verbose_name_plural = 'social accounts'
        unique_together = [['provider', 'provider_user_id']]

    def __str__(self):
        return f"{self.user.email} - {self.provider}"


# =============================================================================
# Child Profile & Parental Control Models
# =============================================================================

class ChildProfile(models.Model):
    """Child profile managed by a parent user."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='children',
        help_text='Parent user who owns this child profile'
    )
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    avatar_color = models.CharField(
        max_length=7,
        blank=True,
        default='#6366F1',
        help_text='Hex color code for avatar'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'child profile'
        verbose_name_plural = 'child profiles'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (child of {self.user.email})"


class ParentalRule(models.Model):
    """Parental control rule for a child."""

    class RuleType(models.TextChoices):
        BLOCK_APP = 'BLOCK_APP', 'Block App'
        LIMIT_USAGE = 'LIMIT_USAGE', 'Limit Usage'
        BEDTIME = 'BEDTIME', 'Bedtime'

    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='parental_rules'
    )
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.CASCADE,
        related_name='rules'
    )
    rule_type = models.CharField(
        max_length=20,
        choices=RuleType.choices
    )
    app_package_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Package name for BLOCK_APP rule'
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='App category for LIMIT_USAGE rule'
    )
    daily_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Daily usage limit in minutes'
    )
    bedtime_start = models.TimeField(
        null=True,
        blank=True,
        help_text='Start of bedtime restriction'
    )
    bedtime_end = models.TimeField(
        null=True,
        blank=True,
        help_text='End of bedtime restriction'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'parental rule'
        verbose_name_plural = 'parental rules'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rule_type} for {self.child.name}"


class RuleViolation(models.Model):
    """Record of a parental rule being violated."""

    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.CASCADE,
        related_name='violations'
    )
    rule = models.ForeignKey(
        ParentalRule,
        on_delete=models.CASCADE,
        related_name='violations'
    )
    occurred_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'rule violation'
        verbose_name_plural = 'rule violations'
        ordering = ['-occurred_at']

    def __str__(self):
        return f"Violation of {self.rule.rule_type} by {self.child.name}"


# =============================================================================
# Network Monitoring Models
# =============================================================================

class NetworkDevice(models.Model):
    """Network device discovered during a scan."""

    class DeviceType(models.TextChoices):
        PHONE = 'PHONE', 'Phone'
        LAPTOP = 'LAPTOP', 'Laptop'
        TABLET = 'TABLET', 'Tablet'
        TV = 'TV', 'TV'
        CONSOLE = 'CONSOLE', 'Console'
        ROUTER = 'ROUTER', 'Router'
        IOT = 'IOT', 'IoT Device'
        OTHER = 'OTHER', 'Other'
        UNKNOWN = 'UNKNOWN', 'Unknown'

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='network_devices'
    )
    name = models.CharField(max_length=255, blank=True, default='')
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17, blank=True, default='')
    device_type = models.CharField(
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.UNKNOWN
    )
    is_trusted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'network device'
        verbose_name_plural = 'network devices'
        ordering = ['-last_seen_at']
        unique_together = [['owner', 'mac_address']]

    def __str__(self):
        return f"{self.name or self.ip_address} ({self.device_type})"


class NetworkScanLog(models.Model):
    """Log of a network scan performed by the client."""

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='network_scans'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    network_ssid = models.CharField(max_length=255, blank=True, null=True)
    network_bssid = models.CharField(max_length=17, blank=True, null=True)
    json_payload = models.JSONField(default=dict)

    class Meta:
        verbose_name = 'network scan log'
        verbose_name_plural = 'network scan logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Scan by {self.owner.email} at {self.created_at}"


# =============================================================================
# App Privacy Models
# =============================================================================

class AppPrivacyProfile(models.Model):
    """Baseline privacy profile for an app (can be extended later)."""

    created_at = models.DateTimeField(auto_now_add=True)
    package_name = models.CharField(max_length=255, db_index=True, unique=True)
    app_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, default='')
    permissions = models.JSONField(default=list)
    baseline_privacy_score = models.PositiveIntegerField(default=80)

    class Meta:
        verbose_name = 'app privacy profile'
        verbose_name_plural = 'app privacy profiles'
        ordering = ['app_name']

    def __str__(self):
        return f"{self.app_name} ({self.package_name})"


class PrivacyCheck(models.Model):
    """User-initiated privacy check for an app."""

    class SuggestedAction(models.TextChoices):
        KEEP = 'KEEP', 'Keep'
        REVIEW = 'REVIEW', 'Review Permissions'
        CONSIDER_UNINSTALL = 'CONSIDER_UNINSTALL', 'Consider Uninstalling'

    class NetworkUsageLevel(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='privacy_checks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    app_package_name = models.CharField(max_length=255)
    app_name = models.CharField(max_length=255)
    permissions = models.JSONField(default=list)
    network_usage_level = models.CharField(
        max_length=10,
        choices=NetworkUsageLevel.choices,
        default=NetworkUsageLevel.MEDIUM
    )
    calculated_privacy_score = models.PositiveIntegerField()
    explanation = models.TextField()
    suggested_action = models.CharField(
        max_length=20,
        choices=SuggestedAction.choices
    )

    class Meta:
        verbose_name = 'privacy check'
        verbose_name_plural = 'privacy checks'
        ordering = ['-created_at']

    def __str__(self):
        return f"Check for {self.app_name} by {self.user.email}"
