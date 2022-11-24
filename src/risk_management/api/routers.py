
from rest_framework.routers import DefaultRouter
from risk_management.api.views import (RiskZoneViewSet, ZoneTypeViewSet,
                                       RiskZoneUpdateviewset, ZoneTypeTableViewSet, ZoneTypeCrudViewSet)

router = DefaultRouter()
router.register('riskzonetableview', RiskZoneViewSet, 'risk_zone')
router.register('zonetypeview', ZoneTypeViewSet, 'zone_type')
router.register('riskzoneupdateview', RiskZoneUpdateviewset, 'risk_zone_update')
router.register('zonetypetableview', ZoneTypeTableViewSet, 'zone_type')
router.register('zonetypecreateupdateview', ZoneTypeCrudViewSet, 'zone_type_crud')
urlpatterns = router.urls
