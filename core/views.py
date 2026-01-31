"""
API Views for Antygravity Backend.
"""

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import (
    ChildProfile,
    ParentalRule,
    RuleViolation,
    NetworkDevice,
    NetworkScanLog,
    PrivacyCheck,
)
from .serializers import (
    ChildProfileSerializer,
    ParentalRuleSerializer,
    RuleViolationSerializer,
    NetworkDeviceSerializer,
    NetworkScanLogSerializer,
    NetworkScanCreateSerializer,
    PrivacyCheckSerializer,
    PrivacyCheckRequestSerializer,
)
from .services.privacy_scoring import calculate_privacy_score


# =============================================================================
# Child Profile ViewSet
# =============================================================================

class ChildProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing child profiles.

    list: GET /api/children/
    create: POST /api/children/
    retrieve: GET /api/children/{id}/
    update: PUT /api/children/{id}/
    partial_update: PATCH /api/children/{id}/
    destroy: DELETE /api/children/{id}/
    """
    serializer_class = ChildProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChildProfile.objects.filter(user=self.request.user)


# =============================================================================
# Parental Control ViewSets
# =============================================================================

class ParentalRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing parental rules.

    Supports filtering by child_id query parameter.
    """
    serializer_class = ParentalRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ParentalRule.objects.filter(parent=self.request.user)

        # Optional filter by child
        child_id = self.request.query_params.get('child_id')
        if child_id:
            queryset = queryset.filter(child_id=child_id)

        return queryset


class RuleViolationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing rule violations.

    Supports filtering by:
    - child_id: Filter by child
    - start_date: Filter violations after this date (YYYY-MM-DD)
    - end_date: Filter violations before this date (YYYY-MM-DD)
    """
    serializer_class = RuleViolationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = RuleViolation.objects.filter(child__user=self.request.user)

        # Filter by child
        child_id = self.request.query_params.get('child_id')
        if child_id:
            queryset = queryset.filter(child_id=child_id)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(occurred_at__date__gte=start_date)

        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(occurred_at__date__lte=end_date)

        return queryset


# =============================================================================
# Network Monitoring ViewSets
# =============================================================================

class NetworkDeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing network devices.

    Custom actions:
    - POST /api/network/devices/{id}/mark_trusted/
    - POST /api/network/devices/{id}/mark_blocked/
    """
    serializer_class = NetworkDeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NetworkDevice.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_trusted(self, request, pk=None):
        """Mark a device as trusted."""
        device = self.get_object()
        device.is_trusted = True
        device.is_blocked = False
        device.save()
        return Response(NetworkDeviceSerializer(device).data)

    @action(detail=True, methods=['post'])
    def mark_blocked(self, request, pk=None):
        """Mark a device as blocked."""
        device = self.get_object()
        device.is_blocked = True
        device.is_trusted = False
        device.save()
        return Response(NetworkDeviceSerializer(device).data)

    @action(detail=True, methods=['post'])
    def unmark(self, request, pk=None):
        """Remove trusted/blocked status from a device."""
        device = self.get_object()
        device.is_trusted = False
        device.is_blocked = False
        device.save()
        return Response(NetworkDeviceSerializer(device).data)


class NetworkScanLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for network scan logs.

    Creating a scan will also create/update network devices.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return NetworkScanCreateSerializer
        return NetworkScanLogSerializer

    def get_queryset(self):
        return NetworkScanLog.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        devices_data = data.get('devices', [])
        now = timezone.now()

        # Create the scan log
        scan_log = NetworkScanLog.objects.create(
            owner=request.user,
            network_ssid=data.get('network_ssid', ''),
            network_bssid=data.get('network_bssid', ''),
            json_payload={'devices': devices_data},
        )

        # Process each device in the scan
        for device_info in devices_data:
            mac = device_info.get('mac_address', '')
            ip = device_info.get('ip_address', '')

            if not mac and not ip:
                continue

            # Try to find existing device by MAC address
            if mac:
                device, created = NetworkDevice.objects.get_or_create(
                    owner=request.user,
                    mac_address=mac,
                    defaults={
                        'ip_address': ip or '0.0.0.0',
                        'name': device_info.get('name', ''),
                        'device_type': device_info.get('device_type', 'UNKNOWN'),
                        'first_seen_at': now,
                        'last_seen_at': now,
                    }
                )
            else:
                # No MAC, use IP (less reliable)
                device, created = NetworkDevice.objects.get_or_create(
                    owner=request.user,
                    ip_address=ip,
                    mac_address='',
                    defaults={
                        'name': device_info.get('name', ''),
                        'device_type': device_info.get('device_type', 'UNKNOWN'),
                        'first_seen_at': now,
                        'last_seen_at': now,
                    }
                )

            if not created:
                # Update existing device
                device.ip_address = ip or device.ip_address
                device.name = device_info.get('name', '') or device.name
                device.last_seen_at = now
                if device_info.get('device_type'):
                    device.device_type = device_info['device_type']
                device.save()

        return Response(
            NetworkScanLogSerializer(scan_log).data,
            status=status.HTTP_201_CREATED
        )


# =============================================================================
# Privacy Check Views
# =============================================================================

class PrivacyCheckView(APIView):
    """
    POST /api/privacy/check/
    Perform a privacy check on an app.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PrivacyCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Calculate privacy score
        score, explanation, suggested_action = calculate_privacy_score(
            permissions=data.get('permissions', []),
            category=data.get('category', ''),
            network_usage_level=data.get('network_usage_level', 'MEDIUM'),
        )

        # Save the check
        privacy_check = PrivacyCheck.objects.create(
            user=request.user,
            app_package_name=data['package_name'],
            app_name=data['app_name'],
            permissions=data.get('permissions', []),
            network_usage_level=data.get('network_usage_level', 'MEDIUM'),
            calculated_privacy_score=score,
            explanation=explanation,
            suggested_action=suggested_action,
        )

        return Response(
            PrivacyCheckSerializer(privacy_check).data,
            status=status.HTTP_201_CREATED
        )


class PrivacyCheckListView(APIView):
    """
    GET /api/privacy/checks/
    List all privacy checks for the current user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        checks = PrivacyCheck.objects.filter(user=request.user)

        # Optional filter by package name
        package_name = request.query_params.get('package_name')
        if package_name:
            checks = checks.filter(app_package_name=package_name)

        serializer = PrivacyCheckSerializer(checks, many=True)
        return Response(serializer.data)
