"""
Privacy Scoring Service for Antygravity.

Calculates privacy risk scores based on app permissions, category, and network usage.
"""

from typing import Tuple

# Permission risk levels (higher = more risky)
DANGEROUS_PERMISSIONS = {
    # Location
    'android.permission.ACCESS_FINE_LOCATION': 15,
    'android.permission.ACCESS_COARSE_LOCATION': 10,
    'android.permission.ACCESS_BACKGROUND_LOCATION': 20,
    # Camera & Microphone
    'android.permission.CAMERA': 15,
    'android.permission.RECORD_AUDIO': 15,
    # Contacts & Calendar
    'android.permission.READ_CONTACTS': 12,
    'android.permission.WRITE_CONTACTS': 15,
    'android.permission.READ_CALENDAR': 8,
    'android.permission.WRITE_CALENDAR': 10,
    # Phone & SMS
    'android.permission.READ_PHONE_STATE': 10,
    'android.permission.CALL_PHONE': 12,
    'android.permission.READ_CALL_LOG': 15,
    'android.permission.READ_SMS': 15,
    'android.permission.SEND_SMS': 18,
    'android.permission.RECEIVE_SMS': 15,
    # Storage
    'android.permission.READ_EXTERNAL_STORAGE': 8,
    'android.permission.WRITE_EXTERNAL_STORAGE': 10,
    'android.permission.MANAGE_EXTERNAL_STORAGE': 15,
    # Body Sensors
    'android.permission.BODY_SENSORS': 12,
    'android.permission.ACTIVITY_RECOGNITION': 8,
    # Other sensitive
    'android.permission.READ_MEDIA_IMAGES': 8,
    'android.permission.READ_MEDIA_VIDEO': 8,
    'android.permission.READ_MEDIA_AUDIO': 5,
    'android.permission.POST_NOTIFICATIONS': 3,
    'android.permission.BLUETOOTH_CONNECT': 5,
    'android.permission.NEARBY_WIFI_DEVICES': 8,
}

# Network usage level penalties
NETWORK_USAGE_PENALTIES = {
    'LOW': 0,
    'MEDIUM': 5,
    'HIGH': 15,
}

# Category risk adjustments (some categories are expected to use certain permissions)
CATEGORY_ADJUSTMENTS = {
    'social': {'expected_permissions': ['CAMERA', 'CONTACTS'], 'base_penalty': 5},
    'communication': {'expected_permissions': ['CONTACTS', 'MICROPHONE'], 'base_penalty': 0},
    'navigation': {'expected_permissions': ['LOCATION'], 'base_penalty': 0},
    'photography': {'expected_permissions': ['CAMERA', 'STORAGE'], 'base_penalty': 0},
    'health_fitness': {'expected_permissions': ['BODY_SENSORS', 'ACTIVITY'], 'base_penalty': 0},
    'finance': {'expected_permissions': [], 'base_penalty': -5},  # Stricter expectations
    'games': {'expected_permissions': [], 'base_penalty': 5},
    'productivity': {'expected_permissions': [], 'base_penalty': 0},
    'entertainment': {'expected_permissions': [], 'base_penalty': 3},
    'shopping': {'expected_permissions': [], 'base_penalty': 0},
    'education': {'expected_permissions': [], 'base_penalty': 0},
    'utilities': {'expected_permissions': [], 'base_penalty': 0},
}


def calculate_privacy_score(
    permissions: list[str],
    category: str,
    network_usage_level: str
) -> Tuple[int, str, str]:
    """
    Calculate privacy score for an app based on its permissions, category, and network usage.

    Args:
        permissions: List of Android permission strings
        category: App category (lowercase)
        network_usage_level: 'LOW', 'MEDIUM', or 'HIGH'

    Returns:
        Tuple of (score: int, explanation: str, suggested_action: str)
        - score: 0-100 where 100 is most private
        - explanation: Human-readable explanation of the score
        - suggested_action: 'KEEP', 'REVIEW', or 'CONSIDER_UNINSTALL'
    """
    base_score = 100
    deductions = []
    concerns = []
    positives = []

    # Calculate permission-based deductions
    permission_penalty = 0
    high_risk_permissions = []
    medium_risk_permissions = []

    for perm in permissions:
        perm_upper = perm.upper()
        if perm in DANGEROUS_PERMISSIONS:
            penalty = DANGEROUS_PERMISSIONS[perm]
            permission_penalty += penalty
            if penalty >= 15:
                high_risk_permissions.append(_simplify_permission_name(perm))
            elif penalty >= 8:
                medium_risk_permissions.append(_simplify_permission_name(perm))

    # Cap permission penalty at 60 points
    permission_penalty = min(permission_penalty, 60)
    if permission_penalty > 0:
        deductions.append(f"Permissions: -{permission_penalty} points")

    # Network usage penalty
    network_penalty = NETWORK_USAGE_PENALTIES.get(network_usage_level.upper(), 5)
    if network_penalty > 0:
        deductions.append(f"Network usage ({network_usage_level}): -{network_penalty} points")

    # Category adjustment
    category_lower = category.lower().replace(' ', '_').replace('&', '_')
    category_info = CATEGORY_ADJUSTMENTS.get(category_lower, {'expected_permissions': [], 'base_penalty': 0})
    category_penalty = category_info['base_penalty']
    if category_penalty != 0:
        if category_penalty > 0:
            deductions.append(f"Category risk ({category}): -{category_penalty} points")
        else:
            positives.append(f"Trusted category ({category}): +{abs(category_penalty)} points")

    # Calculate final score
    total_penalty = permission_penalty + network_penalty + category_penalty
    final_score = max(0, min(100, base_score - total_penalty))

    # Build explanation
    if high_risk_permissions:
        concerns.append(f"High-risk permissions: {', '.join(high_risk_permissions)}")
    if medium_risk_permissions:
        concerns.append(f"Sensitive permissions: {', '.join(medium_risk_permissions[:5])}")
    if network_usage_level.upper() == 'HIGH':
        concerns.append("High network activity may indicate data sharing")

    if final_score >= 80:
        positives.append("Low privacy risk overall")
    elif len(permissions) == 0:
        positives.append("No dangerous permissions requested")

    # Construct explanation text
    explanation_parts = []
    if concerns:
        explanation_parts.append("Concerns: " + "; ".join(concerns))
    if positives:
        explanation_parts.append("Positives: " + "; ".join(positives))
    if not explanation_parts:
        explanation_parts.append("This app has moderate privacy characteristics.")

    explanation = " | ".join(explanation_parts)

    # Determine suggested action
    if final_score >= 70:
        suggested_action = 'KEEP'
    elif final_score >= 40:
        suggested_action = 'REVIEW'
    else:
        suggested_action = 'CONSIDER_UNINSTALL'

    return final_score, explanation, suggested_action


def _simplify_permission_name(permission: str) -> str:
    """Convert Android permission to a human-readable name."""
    # Remove android.permission. prefix
    simple = permission.replace('android.permission.', '')
    # Convert to title case with spaces
    simple = simple.replace('_', ' ').title()
    return simple
