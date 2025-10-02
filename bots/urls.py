from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'bots', views.BotViewSet)
router.register(r'scenarios', views.ScenarioViewSet)
router.register(r'steps', views.StepViewSet)
router.register(r'executions', views.BotExecutionViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/root/', views.api_root, name='api-root'),
    path('', views.home, name='home'),
]