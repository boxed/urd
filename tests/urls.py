from django.urls import (
    include,
    path,
)
from iommi.admin import Admin

urlpatterns = [
    path('admin/', include(Admin().urls())),
]
