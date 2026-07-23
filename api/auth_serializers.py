from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Rol
from .utils import find_user_by_email

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'role')

    def validate_email(self, value):
        if not value:
            return value
        existing_user = find_user_by_email(value)
        if existing_user:
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return value

    def create(self, validated_data):
        role_name = validated_data.pop('role', 'BODEGA')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        
        # Buscar si el nombre corresponde a un Rol (entidad)
        rol_obj = Rol.objects.filter(nombre=role_name).first()
        if rol_obj:
            Profile.objects.create(user=user, role=role_name, rol_entidad=rol_obj)
        else:
            Profile.objects.create(user=user, role=role_name)
            
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)
    rol_entidad_id = serializers.PrimaryKeyRelatedField(source='profile.rol_entidad', read_only=True)
    rol_entidad_nombre = serializers.CharField(source='profile.rol_entidad.nombre', read_only=True)
    permisos = serializers.SerializerMethodField()
    is_approved = serializers.BooleanField(source='profile.is_approved', read_only=True)
    avatar_url = serializers.URLField(source='profile.avatar_url', read_only=True)
    is_google_user = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'date_joined', 'role', 'rol_entidad_id', 'rol_entidad_nombre', 'permisos', 'is_approved', 'avatar_url', 'is_google_user')
        read_only_fields = ('id', 'is_staff', 'is_superuser', 'date_joined', 'role', 'permisos', 'is_approved', 'avatar_url', 'is_google_user')

    def validate_email(self, value):
        if not value:
            return value
        existing_user = find_user_by_email(value)
        if existing_user:
            if self.instance and existing_user.pk == self.instance.pk:
                return value
            raise serializers.ValidationError("Este correo electrónico ya está en uso por otro usuario.")
        return value

    def get_is_google_user(self, obj):
        return hasattr(obj, 'profile') and bool(obj.profile.google_id)

    def get_permisos(self, obj):
        # Unificar permisos del Rol y permisos extra del Perfil
        permisos = set()
        if hasattr(obj, 'profile'):
            if obj.profile.rol_entidad:
                for p in obj.profile.rol_entidad.permisos.all():
                    permisos.add(p.nombre)
            for p in obj.profile.permisos.all():
                permisos.add(p.nombre)
        return list(permisos)


