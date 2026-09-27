"""Tenant-safe PostgreSQL search endpoint."""

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organisations.selectors import organisation_for_user

from .serializers import SearchResultSerializer
from .services import search_organisation


class OrganisationSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(
            user=request.user,
            organisation_id=organisation_id,
        )
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            raise serializers.ValidationError({"q": "Enter at least two characters to search."})
        results = search_organisation(organisation=organisation, query_text=query)
        return Response(
            {
                "query": query,
                "count": len(results),
                "results": SearchResultSerializer(results, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
