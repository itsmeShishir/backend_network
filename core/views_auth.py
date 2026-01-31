"""
Authentication Views for Antygravity Backend.
"""

from django.contrib.auth import get_user_model, authenticate
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    SocialLoginSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .models import SocialAccount
from .services.social_auth import verify_google_token, verify_apple_token, SocialAuthError

User = get_user_model()


def get_tokens_for_user(user):
    """Generate JWT tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Register a new user with email and password.
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user).data

        return Response({
            'user': user_data,
            'tokens': tokens,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/auth/login/
    Login with email and password.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {'detail': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'detail': 'User account is disabled.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user).data

        return Response({
            'user': user_data,
            'tokens': tokens,
        })


class SocialLoginGoogleView(APIView):
    """
    POST /api/auth/social/google/
    Login or register with Google ID token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        id_token = serializer.validated_data['id_token']

        try:
            google_data = verify_google_token(id_token)
        except SocialAuthError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if social account exists
        try:
            social_account = SocialAccount.objects.get(
                provider=SocialAccount.Provider.GOOGLE,
                provider_user_id=google_data['sub']
            )
            user = social_account.user
        except SocialAccount.DoesNotExist:
            # Check if user with this email exists
            email = google_data.get('email', '')
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    # Create new user
                    user = User.objects.create_user(
                        email=email,
                        full_name=google_data.get('name', ''),
                        avatar_url=google_data.get('picture', ''),
                    )
            else:
                # No email provided, create with Google sub as identifier
                fake_email = f"{google_data['sub']}@google.antygravity.local"
                user = User.objects.create_user(
                    email=fake_email,
                    full_name=google_data.get('name', ''),
                    avatar_url=google_data.get('picture', ''),
                )

            # Create social account link
            SocialAccount.objects.create(
                user=user,
                provider=SocialAccount.Provider.GOOGLE,
                provider_user_id=google_data['sub'],
                email=email,
            )

        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user).data

        return Response({
            'user': user_data,
            'tokens': tokens,
        })


class SocialLoginAppleView(APIView):
    """
    POST /api/auth/social/apple/
    Login or register with Apple ID token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        id_token = serializer.validated_data['id_token']

        try:
            apple_data = verify_apple_token(id_token)
        except SocialAuthError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if social account exists
        try:
            social_account = SocialAccount.objects.get(
                provider=SocialAccount.Provider.APPLE,
                provider_user_id=apple_data['sub']
            )
            user = social_account.user
        except SocialAccount.DoesNotExist:
            # Check if user with this email exists
            email = apple_data.get('email', '')
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    user = User.objects.create_user(
                        email=email,
                        full_name='',  # Apple doesn't always provide name
                    )
            else:
                # No email provided, create with Apple sub as identifier
                fake_email = f"{apple_data['sub']}@apple.antygravity.local"
                user = User.objects.create_user(email=fake_email)

            # Create social account link
            SocialAccount.objects.create(
                user=user,
                provider=SocialAccount.Provider.APPLE,
                provider_user_id=apple_data['sub'],
                email=email,
            )

        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user).data

        return Response({
            'user': user_data,
            'tokens': tokens,
        })


class MeView(APIView):
    """
    GET /api/auth/me/
    PATCH /api/auth/me/
    Get or update the current user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserSerializer(request.user).data)
