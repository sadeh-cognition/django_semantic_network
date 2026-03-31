from django.urls import path
from ninja import NinjaAPI

from .views import router

api = NinjaAPI(title="Research Knowledge Graph API")

api.add_router("/", router)

urlpatterns = [
    path("", api.urls),  # Base is /api/
]
