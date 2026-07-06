from drf_spectacular.utils import extend_schema
from rest_framework import generics

from .serializers import MeSerializer


@extend_schema(tags=["auth"])
class MeView(generics.RetrieveAPIView):
    """Return the authenticated user's profile and role names."""

    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user
