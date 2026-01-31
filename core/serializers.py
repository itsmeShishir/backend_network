"""
DRF Serializers for Antygravity Backend.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import (
    SocialAccount,
    ChildProfile,
    ParentalRule,
    RuleViolation,
    NetworkDevice,
    NetworkScanLog,
    AppPrivacyProfile,
    PrivacyCheck,
)

User = get_user_model()


# =============================================================================
# User & Auth Serializers
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile data."""

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'avatar_url', 'is_parent', 'date_joined']
        read_only_fields = ['id', 'email', 'date_joined']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ['full_name', 'avatar_url', 'is_parent']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'full_name', 'is_parent']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for email/password login."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class SocialLoginSerializer(serializers.Serializer):
    """Serializer for social login (Google/Apple)."""

    id_token = serializers.CharField(required=True)


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for JWT token response."""

    access = serializers.CharField()
    refresh = serializers.CharField()


# =============================================================================
# Child Profile Serializers
# =============================================================================

class ChildProfileSerializer(serializers.ModelSerializer):
    """Serializer for child profiles."""

    class Meta:
        model = ChildProfile
        fields = ['id', 'name', 'age', 'avatar_color', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        # Automatically set the parent user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# =============================================================================
# Parental Control Serializers
# =============================================================================

class ParentalRuleSerializer(serializers.ModelSerializer):
    """Serializer for parental rules."""

    child_name = serializers.CharField(source='child.name', read_only=True)

    class Meta:
        model = ParentalRule
        fields = [
            'id', 'child', 'child_name', 'rule_type',
            'app_package_name', 'category',
            'daily_limit_minutes', 'bedtime_start', 'bedtime_end',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_child(self, value):
        # Ensure child belongs to the current user
        request = self.context.get('request')
        if request and value.user != request.user:
            raise serializers.ValidationError('Child does not belong to you.')
        return value

    def create(self, validated_data):
        validated_data['parent'] = self.context['request'].user
        return super().create(validated_data)


class RuleViolationSerializer(serializers.ModelSerializer):
    """Serializer for rule violations."""

    child_name = serializers.CharField(source='child.name', read_only=True)
    rule_type = serializers.CharField(source='rule.rule_type', read_only=True)

    class Meta:
        model = RuleViolation
        fields = ['id', 'child', 'child_name', 'rule', 'rule_type', 'occurred_at', 'description']
        read_only_fields = ['id', 'occurred_at']

    def validate(self, attrs):
        request = self.context.get('request')
        child = attrs.get('child')
        rule = attrs.get('rule')

        if child and child.user != request.user:
            raise serializers.ValidationError({'child': 'Child does not belong to you.'})
        if rule and rule.parent != request.user:
            raise serializers.ValidationError({'rule': 'Rule does not belong to you.'})

        return attrs


# =============================================================================
# Network Monitoring Serializers
# =============================================================================

class NetworkDeviceSerializer(serializers.ModelSerializer):
    """Serializer for network devices."""

    class Meta:
        model = NetworkDevice
        fields = [
            'id', 'name', 'ip_address', 'mac_address', 'device_type',
            'is_trusted', 'is_blocked', 'first_seen_at', 'last_seen_at'
        ]
        read_only_fields = ['id', 'first_seen_at', 'last_seen_at']


class NetworkDeviceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating network devices from scan."""

    class Meta:
        model = NetworkDevice
        fields = ['name', 'ip_address', 'mac_address', 'device_type']


class NetworkScanLogSerializer(serializers.ModelSerializer):
    """Serializer for network scan logs."""

    devices_count = serializers.SerializerMethodField()

    class Meta:
        model = NetworkScanLog
        fields = ['id', 'created_at', 'network_ssid', 'network_bssid', 'devices_count']
        read_only_fields = ['id', 'created_at']

    def get_devices_count(self, obj):
        payload = obj.json_payload or {}
        devices = payload.get('devices', [])
        return len(devices) if isinstance(devices, list) else 0


class NetworkScanCreateSerializer(serializers.Serializer):
    """Serializer for creating a network scan with devices."""

    network_ssid = serializers.CharField(max_length=255, required=False, allow_blank=True)
    network_bssid = serializers.CharField(max_length=17, required=False, allow_blank=True)
    devices = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )


# =============================================================================
# Privacy Serializers
# =============================================================================

class AppPrivacyProfileSerializer(serializers.ModelSerializer):
    """Serializer for app privacy profiles."""

    class Meta:
        model = AppPrivacyProfile
        fields = [
            'id', 'package_name', 'app_name', 'category',
            'permissions', 'baseline_privacy_score', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PrivacyCheckSerializer(serializers.ModelSerializer):
    """Serializer for privacy check results."""

    class Meta:
        model = PrivacyCheck
        fields = [
            'id', 'app_package_name', 'app_name', 'permissions',
            'network_usage_level', 'calculated_privacy_score',
            'explanation', 'suggested_action', 'created_at'
        ]
        read_only_fields = [
            'id', 'calculated_privacy_score', 'explanation',
            'suggested_action', 'created_at'
        ]


class PrivacyCheckRequestSerializer(serializers.Serializer):
    """Serializer for privacy check request."""

    app_name = serializers.CharField(max_length=255)
    package_name = serializers.CharField(max_length=255)
    category = serializers.CharField(max_length=100, required=False, default='')
    permissions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    network_usage_level = serializers.ChoiceField(
        choices=['LOW', 'MEDIUM', 'HIGH'],
        default='MEDIUM'
    )
