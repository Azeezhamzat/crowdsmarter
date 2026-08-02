import pytest
from django.urls import reverse

from apps.organisations.models import Membership


@pytest.mark.django_db
def test_workspace_endpoints_are_tenant_isolated(
    api_client, user_factory, workspace_factory
):  # type: ignore[no-untyped-def]
    outsider = user_factory()
    workspace = workspace_factory()
    api_client.force_authenticate(outsider)

    detail = api_client.get(reverse("workspaces:detail", kwargs={"workspace_id": workspace.id}))
    collection = api_client.get(
        reverse(
            "workspaces:list-create",
            kwargs={"organisation_id": workspace.organisation_id},
        )
    )

    assert detail.status_code == 404
    assert collection.status_code == 404


@pytest.mark.django_db
def test_owner_can_list_create_retrieve_and_update_workspace(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    api_client.force_authenticate(owner)
    collection_url = reverse(
        "workspaces:list-create", kwargs={"organisation_id": organisation.id}
    )

    create_response = api_client.post(
        collection_url,
        {"name": "Strategy", "slug": "strategy", "description": "Strategic choices."},
        format="json",
    )
    assert create_response.status_code == 201
    assert api_client.get(collection_url).status_code == 200

    detail_url = reverse(
        "workspaces:detail", kwargs={"workspace_id": create_response.json()["id"]}
    )
    assert api_client.get(detail_url).status_code == 200
    patch = api_client.patch(
        detail_url,
        {"name": "Executive strategy", "description": "High-impact choices."},
        format="json",
    )
    assert patch.status_code == 200
    assert patch.json()["name"] == "Executive strategy"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "expected_status"),
    [("owner", 201), ("admin", 201), ("contributor", 403), ("viewer", 403)],
)
def test_workspace_create_permission_matrix(
    api_client, user_factory, organisation_factory, role, expected_status
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    actor = owner if role == "owner" else user_factory()
    organisation = organisation_factory(owner=owner)
    if actor != owner:
        Membership.objects.create(organisation=organisation, user=actor, role=role)
    api_client.force_authenticate(actor)

    response = api_client.post(
        reverse("workspaces:list-create", kwargs={"organisation_id": organisation.id}),
        {"name": f"{role} workspace", "slug": f"{role}-workspace"},
        format="json",
    )

    assert response.status_code == expected_status
