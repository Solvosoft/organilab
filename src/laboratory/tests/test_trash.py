"""Papelera org-scoped (proyecto 13, fase C): los pilotos Protocol y
Procedure van a la papelera con su contexto (TrashRelation) y ninguna
organización ve, restaura ni purga lo de otra."""

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
from django.urls import reverse

from auth_and_perms.models import ProfilePermission, Rol
from djgentelella.models import Trash, TrashRelation
from laboratory.models import Laboratory, Protocol
from laboratory.tests.utils import BaseLaboratorySetUpTest, BaseSetUpAjaxRequest


def grant_trash_perms(user, *codenames):
    perms = Permission.objects.filter(
        content_type__app_label="djgentelella", codename__in=codenames
    )
    user.user_permissions.add(*perms)


class TrashPilotBase(BaseSetUpAjaxRequest):

    def make_protocol(self, lab, user, name="Protocolo piloto"):
        return Protocol.objects.create(
            name=name,
            short_description="corto",
            file="protocols/piloto.pdf",
            laboratory=lab,
            upload_by=user,
        )

    def trash_of(self, obj):
        return Trash.objects.get(
            content_type__app_label=obj._meta.app_label,
            content_type__model=obj._meta.model_name,
            object_id=obj.pk,
        )


class ProtocolToTrashTest(BaseLaboratorySetUpTest):
    """La vista de borrado (mismo armado de rol/ProfilePermission que
    ProtocolViewTest) ahora manda el protocolo a la papelera con contexto."""

    def test_delete_view_sends_protocol_to_trash_with_context(self):
        permissions = ProfilePermission.objects.filter(
            content_type__app_label="laboratory",
            object_id=self.lab.pk,
            profile=self.user.profile,
        ).first()
        permissions.rol.clear()
        rol = Rol.objects.create(name="Protocol trash user")
        permissions.rol.add(rol)
        rol.permissions.add(
            Permission.objects.get(
                content_type__app_label="laboratory",
                codename="delete_protocol",
            )
        )
        protocol = Protocol.objects.get(
            name="Manipulación de instrumentos de laboratorio"
        )
        response = self.client.post(
            reverse(
                "laboratory:protocol_delete",
                args=(self.org.pk, self.lab.pk, protocol.pk),
            )
        )
        self.assertEqual(response.status_code, 302)

        self.assertFalse(Protocol.objects.filter(pk=protocol.pk).exists())
        self.assertTrue(
            Protocol.objects_deleted_only.filter(pk=protocol.pk).exists()
        )
        trash = Trash.objects.get(
            content_type__app_label="laboratory",
            content_type__model="protocol",
            object_id=protocol.pk,
        )
        self.assertEqual(trash.deleted_by, self.user)
        self.assertEqual(
            {row.content_object for row in trash.gt_relations.all()},
            {self.org, self.lab},
        )


class ProcedureToTrashTest(TrashPilotBase):

    def make_procedure(self, org):
        from academic.models import Procedure
        from django.contrib.contenttypes.models import ContentType

        return Procedure.objects.create(
            title="Procedimiento piloto",
            description="desc",
            content_type=ContentType.objects.get(
                app_label="laboratory", model="organizationstructure"
            ),
            object_id=org.pk,
        )

    def test_delete_view_sends_procedure_to_trash_with_context(self):
        procedure = self.make_procedure(self.org1)
        perm = Permission.objects.get(
            content_type__app_label="academic", codename="delete_procedure"
        )
        self.user1_org1.user_permissions.add(perm)
        response = self.client1_org1.post(
            reverse("academic:delete_procedure", args=(self.org1.pk,)),
            {"pk": procedure.pk},
        )
        self.assertEqual(response.status_code, 200)

        from academic.models import Procedure as ProcedureModel

        self.assertFalse(
            ProcedureModel.objects.filter(pk=procedure.pk).exists()
        )
        trash = self.trash_of(procedure)
        self.assertEqual(trash.deleted_by, self.user1_org1)
        self.assertEqual(
            [row.content_object for row in trash.gt_relations.all()],
            [self.org1],
        )


class TrashScopeTest(TrashPilotBase):
    """El test anti-fuga: dos organizaciones, cada una ve SOLO su papelera."""

    def setUp(self):
        super().setUp()
        grant_trash_perms(
            self.user1_org1, "view_trash", "change_trash", "delete_trash"
        )
        grant_trash_perms(
            self.user2_org2, "view_trash", "change_trash", "delete_trash"
        )
        self.protocol_org1 = self.make_protocol(self.lab1_org1, self.user1_org1)
        self.protocol_org2 = self.make_protocol(
            self.lab2_org2, self.user2_org2, name="Protocolo ajeno"
        )
        self.protocol_org1.delete(
            user=self.user1_org1,
            related_objects=[self.org1, self.lab1_org1],
        )
        self.protocol_org2.delete(
            user=self.user2_org2,
            related_objects=[self.org2, self.lab2_org2],
        )
        self.trash_org1 = self.trash_of(self.protocol_org1)
        self.trash_org2 = self.trash_of(self.protocol_org2)

    def list_url(self, org):
        return reverse("laboratory:api-trash-list", args=(org.pk,))

    def test_each_org_sees_only_its_trash(self):
        response = self.client1_org1.get(
            self.list_url(self.org1), {"limit": 10, "offset": 0}
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = [row["id"] for row in payload["data"]]
        self.assertIn(self.trash_org1.pk, ids)
        self.assertNotIn(self.trash_org2.pk, ids)
        # recordsTotal es el universo scoped, no el global de la plataforma.
        self.assertEqual(payload["recordsTotal"], len(payload["data"]))
        self.assertLess(payload["recordsTotal"], Trash.objects.count())

    def test_restore_brings_the_protocol_back_and_logs_for_the_org(self):
        response = self.client1_org1.post(
            reverse(
                "laboratory:api-trash-restore",
                args=(self.org1.pk, self.trash_org1.pk),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["result"])
        self.assertTrue(
            Protocol.objects.filter(pk=self.protocol_org1.pk).exists()
        )
        self.assertFalse(
            Trash.objects.filter(pk=self.trash_org1.pk).exists()
        )
        # El log del restore queda relacionado al contexto del borrado, así
        # la bitácora org-scoped lo lista.
        entry = LogEntry.objects.filter(action_flag=5).latest("pk")
        self.assertIn(
            self.org1,
            [row.content_object for row in entry.gt_relations.all()],
        )

    def test_a_stranger_cannot_restore_another_orgs_entry(self):
        response = self.client2_org2.post(
            reverse(
                "laboratory:api-trash-restore",
                args=(self.org2.pk, self.trash_org1.pk),
            )
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(
            Protocol.objects.filter(pk=self.protocol_org1.pk).exists()
        )

    def test_hard_delete_purges_the_object(self):
        response = self.client1_org1.delete(
            reverse(
                "laboratory:api-trash-detail",
                args=(self.org1.pk, self.trash_org1.pk),
            )
        )
        self.assertIn(response.status_code, (200, 204))
        self.assertFalse(
            Protocol.objects_with_deleted.filter(
                pk=self.protocol_org1.pk
            ).exists()
        )
        self.assertFalse(
            Trash.objects.filter(pk=self.trash_org1.pk).exists()
        )
        self.assertFalse(
            TrashRelation.objects.filter(trash_id=self.trash_org1.pk).exists()
        )

    def test_without_the_view_permission_the_list_is_denied(self):
        self.user3_org1.user_permissions.clear()
        from django.test import Client

        client = Client()
        client.force_login(self.user3_org1)
        response = client.get(
            self.list_url(self.org1), {"limit": 10, "offset": 0}
        )
        self.assertIn(response.status_code, (302, 403))


class ProtocolApiIsReadOnlyTest(BaseLaboratorySetUpTest):
    """El viewset de protocolos solo lista.

    Cuando era un ModelViewSet completo, DELETE .../api_protocol/<pk>/
    ejecutaba instance.delete() sin usuario ni related_objects: el protocolo
    entraba a la papelera sin TrashRelation y, como la pantalla org-scoped
    filtra justamente por esa relación, quedaba borrado e irrecuperable.
    """

    def detail_url(self, pk):
        return "%s%d/" % (reverse("laboratory:api-protocol-list"), pk)

    def test_delete_is_not_routed_and_the_protocol_survives(self):
        protocol = Protocol.objects.get(
            name="Manipulación de instrumentos de laboratorio"
        )
        # Como XHR para que HandleErrorMiddleware no convierta el 404 en un
        # redirect a la pantalla de error.
        response = self.client.delete(
            self.detail_url(protocol.pk), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Protocol.objects.filter(pk=protocol.pk).exists())
        self.assertFalse(
            Trash.objects.filter(
                content_type__app_label="laboratory",
                content_type__model="protocol",
                object_id=protocol.pk,
            ).exists()
        )

    def test_records_total_is_scoped_to_the_laboratory(self):
        other_lab = Laboratory.objects.exclude(pk=self.lab.pk).first()
        Protocol.objects.create(
            name="Protocolo de otro laboratorio",
            short_description="corto",
            file="protocols/otro.pdf",
            laboratory=other_lab,
            upload_by=self.user,
        )
        response = self.client.get(
            reverse("laboratory:api-protocol-list"),
            data={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["recordsTotal"],
            Protocol.objects.filter(laboratory=self.lab).count(),
        )
        self.assertNotContains(response, "Protocolo de otro laboratorio")
