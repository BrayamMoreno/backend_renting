from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RecepcionViewSet, InventarioItemViewSet, MarcaViewSet,
    TipoProductoViewSet, TipoDiscoViewSet, ProcesadorViewSet, RamViewSet, DiscoViewSet, UbicacionViewSet, PuntoAlistamientoViewSet,
    DevolucionViewSet, RolViewSet, PermisoViewSet, AlistamientoViewSet,
    AlertaCriticaViewSet, UserPendingView, ProveedorViewSet, EntregadorViewSet,
    ConfiguracionEmailBajaViewSet, BackupViewSet
)

router = DefaultRouter()
router.register(r'recepciones', RecepcionViewSet)
router.register(r'inventario', InventarioItemViewSet)
router.register(r'marcas', MarcaViewSet)
router.register(r'tipos-producto', TipoProductoViewSet)
router.register(r'tipos-disco', TipoDiscoViewSet)
router.register(r'procesadores', ProcesadorViewSet)
router.register(r'ram', RamViewSet)
router.register(r'discos', DiscoViewSet)
router.register(r'ubicaciones', UbicacionViewSet)
router.register(r'puntos-alistamiento', PuntoAlistamientoViewSet)
router.register(r'devoluciones', DevolucionViewSet)
router.register(r'roles', RolViewSet)
router.register(r'permisos', PermisoViewSet)
router.register(r'alistamientos', AlistamientoViewSet)
router.register(r'alertas', AlertaCriticaViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'entregadores', EntregadorViewSet)
router.register(r'configuraciones-email-baja', ConfiguracionEmailBajaViewSet)
router.register(r'backups', BackupViewSet, basename='backups')

urlpatterns = [
    path('', include(router.urls)),
    path('user-pending/', UserPendingView.as_view(), name='user-pending'),
]
