from django.urls import path
from ninja import NinjaAPI

api = NinjaAPI(title="Research Knowledge Graph API")

from .views import router
api.add_router("/", router)

urlpatterns = [
    path("", api.urls), # Base is /api/
]
