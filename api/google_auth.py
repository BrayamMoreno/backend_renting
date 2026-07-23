import os
import requests as http_requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import Profile
from django.conf import settings
from .utils import find_user_by_email


class GoogleLoginView(APIView):
    """
    POST /api/auth/google/
    Acepta dos modos:
      - id_token: flujo clásico GSI (Google Sign-In con One Tap)
      - access_token: flujo OAuth2 Token (google.accounts.oauth2.initTokenClient con prompt=select_account)

    En ambos casos:
    - Si el usuario no existe: lo crea con is_approved=False (pendiente)
    - Si existe y está aprobado: devuelve JWT propios
    - Si existe y NO está aprobado: devuelve 403 pending_approval
    """
    permission_classes = [AllowAny]

    def post(self, request):
        id_token_str = request.data.get('id_token')
        access_token_str = request.data.get('access_token')

        if not id_token_str and not access_token_str:
            return Response(
                {'error': 'Se requiere id_token o access_token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client_id = getattr(settings, 'GOOGLE_CLIENT_ID', os.environ.get('GOOGLE_CLIENT_ID', ''))

            if id_token_str:
                # --- Flujo clásico: verificar ID token ---
                idinfo = id_token.verify_oauth2_token(
                    id_token_str,
                    google_requests.Request(),
                    client_id
                )
            else:
                # --- Flujo OAuth2 Token: obtener info del usuario con access_token ---
                userinfo_resp = http_requests.get(
                    'https://www.googleapis.com/oauth2/v3/userinfo',
                    headers={'Authorization': f'Bearer {access_token_str}'}
                )
                if userinfo_resp.status_code != 200:
                    return Response(
                        {'error': 'access_token de Google inválido o expirado.'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                idinfo = userinfo_resp.json()

            # Extraer datos del usuario de Google
            google_id = idinfo['sub']
            email = idinfo.get('email', '')
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            avatar_url = idinfo.get('picture', '')

            if not email:
                return Response(
                    {'error': 'No se pudo obtener el email de la cuenta de Google.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except (ValueError, KeyError) as e:
            return Response(
                {'error': f'Token de Google inválido: {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Buscar usuario existente por google_id o email
        profile = Profile.objects.filter(google_id=google_id).select_related('user').first()

        if profile:
            user = profile.user
        else:
            # Buscar por email (insensible a mayúsculas/minúsculas y normalizado para Gmail)
            user = find_user_by_email(email)

            if user:
                # Usuario existente (creado por admin) → vincular Google ID
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.google_id = google_id
                if avatar_url:
                    profile.avatar_url = avatar_url
                profile.save()
            else:
                # Usuario completamente nuevo → crear con is_approved=False
                username = email.split('@')[0]
                # Asegurar username único
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    # Password inutilizable para usuarios de Google
                    password=None
                )
                user.set_unusable_password()
                user.save()

                Profile.objects.create(
                    user=user,
                    google_id=google_id,
                    avatar_url=avatar_url,
                    is_approved=False,  # Pendiente de aprobación
                    role='BODEGA'  # Rol por defecto
                )

                return Response({
                    'status': 'pending_approval',
                    'message': 'Tu cuenta ha sido creada y está pendiente de aprobación por un administrador.',
                    'email': email,
                    'name': f'{first_name} {last_name}'.strip()
                }, status=status.HTTP_403_FORBIDDEN)

        # Usuario existente — verificar aprobación
        profile = user.profile if hasattr(user, 'profile') else Profile.objects.get_or_create(user=user)[0]

        if not profile.is_approved:
            return Response({
                'status': 'pending_approval',
                'message': 'Tu cuenta está pendiente de aprobación por un administrador.',
                'email': user.email,
                'name': f'{user.first_name} {user.last_name}'.strip()
            }, status=status.HTTP_403_FORBIDDEN)

        # Actualizar avatar si cambió
        if avatar_url and profile.avatar_url != avatar_url:
            profile.avatar_url = avatar_url
            profile.save(update_fields=['avatar_url'])

        # Generar tokens JWT propios
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'status': 'approved'
        }, status=status.HTTP_200_OK)
