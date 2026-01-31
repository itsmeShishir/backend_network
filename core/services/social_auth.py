"""
Social Authentication Service for Antygravity.

Handles verification of Google and Apple OAuth tokens.
"""

from typing import Optional, Dict, Any
from django.conf import settings

# Google Auth
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Apple Auth (using python-jose for JWT verification)
from jose import jwt, JWTError
import requests


class SocialAuthError(Exception):
    """Custom exception for social auth failures."""
    pass


def verify_google_token(token: str) -> Dict[str, Any]:
    """
    Verify a Google ID token and extract user information.

    Args:
        token: The Google ID token from the client

    Returns:
        Dict containing:
            - sub: Google user ID
            - email: User's email
            - email_verified: Whether email is verified
            - name: User's full name (optional)
            - picture: Profile picture URL (optional)

    Raises:
        SocialAuthError: If token verification fails
    """
    try:
        # Verify the token with Google's servers
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise SocialAuthError('Invalid token issuer')

        return {
            'sub': idinfo['sub'],
            'email': idinfo.get('email', ''),
            'email_verified': idinfo.get('email_verified', False),
            'name': idinfo.get('name', ''),
            'picture': idinfo.get('picture', ''),
        }

    except ValueError as e:
        raise SocialAuthError(f'Invalid Google token: {str(e)}')
    except Exception as e:
        raise SocialAuthError(f'Google token verification failed: {str(e)}')


# Apple's public key URL
APPLE_PUBLIC_KEY_URL = 'https://appleid.apple.com/auth/keys'

# Cache for Apple's public keys
_apple_public_keys_cache: Optional[Dict] = None


def _get_apple_public_keys() -> Dict:
    """Fetch Apple's public keys for token verification."""
    global _apple_public_keys_cache

    if _apple_public_keys_cache is not None:
        return _apple_public_keys_cache

    try:
        response = requests.get(APPLE_PUBLIC_KEY_URL, timeout=10)
        response.raise_for_status()
        _apple_public_keys_cache = response.json()
        return _apple_public_keys_cache
    except requests.RequestException as e:
        raise SocialAuthError(f'Failed to fetch Apple public keys: {str(e)}')


def verify_apple_token(token: str) -> Dict[str, Any]:
    """
    Verify an Apple ID token and extract user information.

    Args:
        token: The Apple ID token from the client

    Returns:
        Dict containing:
            - sub: Apple user ID
            - email: User's email (if provided)
            - email_verified: Whether email is verified (if provided)

    Raises:
        SocialAuthError: If token verification fails
    """
    try:
        # Get unverified header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')

        if not kid:
            raise SocialAuthError('No key ID in token header')

        # Fetch Apple's public keys
        apple_keys = _get_apple_public_keys()

        # Find the matching key
        matching_key = None
        for key in apple_keys.get('keys', []):
            if key.get('kid') == kid:
                matching_key = key
                break

        if not matching_key:
            # Invalidate cache and retry once
            global _apple_public_keys_cache
            _apple_public_keys_cache = None
            apple_keys = _get_apple_public_keys()

            for key in apple_keys.get('keys', []):
                if key.get('kid') == kid:
                    matching_key = key
                    break

        if not matching_key:
            raise SocialAuthError('Unable to find matching Apple public key')

        # Verify the token
        payload = jwt.decode(
            token,
            matching_key,
            algorithms=['RS256'],
            audience=settings.APPLE_CLIENT_ID,
            issuer='https://appleid.apple.com'
        )

        return {
            'sub': payload['sub'],
            'email': payload.get('email', ''),
            'email_verified': payload.get('email_verified', False),
        }

    except JWTError as e:
        raise SocialAuthError(f'Invalid Apple token: {str(e)}')
    except Exception as e:
        raise SocialAuthError(f'Apple token verification failed: {str(e)}')
