from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .auth_serializers import RegisterSerializer, UserProfileSerializer
from .models import Profile, Rol
from .permissions import IsAdminRole


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/users/create/
    Crea un nuevo usuario. Solo accesible por administradores.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [IsAdminRole]


class MeView(APIView):
    """
    GET /api/auth/me/
    Devuelve el perfil del usuario autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    """
    GET /api/auth/users/
    Lista todos los usuarios. Solo para administradores.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminRole]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PUT, PATCH, DELETE /api/auth/users/<id>/
    Gestiona un usuario individual. Solo para administradores.
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminRole]

    def perform_update(self, serializer):
        # Handle role update if provided
        role_name = self.request.data.get('role')
        is_approved = self.request.data.get('is_approved')
        user = serializer.save()
        
        profile, created = Profile.objects.get_or_create(user=user)
        
        if role_name:
            # Buscar si el nombre corresponde a un Rol (entidad)
            rol_obj = Rol.objects.filter(nombre=role_name).first()
            if rol_obj:
                profile.rol_entidad = rol_obj
                profile.role = role_name # Sincronizar campo simple por compatibilidad
            else:
                profile.rol_entidad = None
                profile.role = role_name
        
        if is_approved is not None:
            profile.is_approved = is_approved
        
        profile.save()


class ApproveUserView(APIView):
    """
    PATCH /api/auth/users/<id>/approve/
    Aprueba un usuario pendiente. Solo para administradores.
    """
    permission_classes = [IsAdminRole]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.is_approved = True
        profile.save(update_fields=['is_approved'])
        
        serializer = UserProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Cambia la contraseña del usuario autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # Block password changes for Google accounts
        if hasattr(user, 'profile') and user.profile.google_id:
            return Response({'error': 'Las cuentas de Google no manejan contraseña local.'}, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get('new_password')

        if not new_password:
            return Response({'error': 'Faltan campos obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 6:
            return Response({'error': 'La nueva contraseña debe tener al menos 6 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Contraseña actualizada correctamente.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
