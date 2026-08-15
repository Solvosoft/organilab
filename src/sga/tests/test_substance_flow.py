import json

from async_notifications.models import EmailNotification
from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from djgentelella.models import ChunkedUpload
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from auth_and_perms.models import Profile, ProfilePermission
from django.contrib.contenttypes.models import ContentType
from laboratory.models import (
    LabOrgLogEntry,
    Laboratory,
    Object,
    ObjectFeatures,
    OrganizationStructure,
)
from pending_tasks.models import PendingTask
from sga.models import (
    ReviewSubstance,
    SecurityLeaf,
    Substance,
    SubstanceCharacteristics,
    SubstanceLaboratory,
    SubstanceObservation,
)

MINIMAL_PDF = b"%PDF-1.4\ntrailer<</Root 1 0 R>>\n%%EOF\n"


def sds_file(name="ficha.pdf"):
    return SimpleUploadedFile(name, MINIMAL_PDF, content_type="application/pdf")


def chunked_token(user, name="ficha.pdf"):
    """El widget de gentelella sube por trozos y deja este token en el POST."""
    upload = ChunkedUpload.objects.create(
        user=user, filename=name, offset=len(MINIMAL_PDF), status=2
    )
    upload.file.save(name, ContentFile(MINIMAL_PDF), save=True)
    return json.dumps({"token": str(upload.upload_id)})


@override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
class SubstanceWizardFlowTest(TestCase):
    """Recorre el asistente de punta a punta con sus efectos laterales."""

    fixtures = ["substances.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)
        self.org_pk = 1
        self.url_attr = {"org_pk": self.org_pk}
        self.substance = Substance.objects.get(pk=134)
        self.characteristics = SubstanceCharacteristics.objects.get(
            substance=self.substance
        )
        self.lab = Laboratory.objects.get(pk=1)
        self.feature = ObjectFeatures.objects.get(pk=1)

    # ---------- utilidades ----------

    def payload(self, **overrides):
        data = {
            "comercial_name": "Acetona",
            "synonymous": '[{"value":"propanona"}]',
            "features": [self.feature.pk],
            "organization": self.org_pk,
            "description": "Disolvente",
            "brand": "ACME",
            "density": 0.79,
            "bioaccumulable": False,
            "molecular_formula": "C3H6O",
            "cas_id_number": "67-64-1",
            "is_precursor": False,
            "seveso_list": False,
        }
        data.update(overrides)
        return data

    def attach_sheet(self):
        self.characteristics.security_sheet = sds_file()
        self.characteristics.save(update_fields=["security_sheet"])

    def make_reviewer(self):
        """Un usuario del grupo que recibe los avisos de revisión."""
        reviewer = User.objects.create_user("revisor", "revisor@test.org", "x")
        Profile.objects.create(user=reviewer)
        Group.objects.get(name="RegisterOrganization").user_set.add(reviewer)
        return reviewer

    def foreign_org(self):
        return OrganizationStructure.objects.create(name="Organización ajena")

    def extra_lab(self, name="Laboratorio de Física"):
        """Otro laboratorio del usuario en la misma organización.

        La fixture solo trae uno. Hace falta el ProfilePermission además del
        laboratorio: `get_user_laboratories_queryset` es lo que acota el campo, y
        sin él el formulario rechazaría el laboratorio nuevo.
        """
        lab = Laboratory.objects.create(
            name=name,
            organization=self.lab.organization,
            created_by=self.user,
        )
        ProfilePermission.objects.create(
            profile=self.user.profile,
            organization=self.lab.organization,
            content_type=ContentType.objects.get_for_model(Laboratory),
            object_id=lab.pk,
        )
        return lab

    # ---------- paso 1 ----------

    def test_step_one_stores_the_uploaded_sheet(self):
        response = self.client.post(
            reverse("sga:update_substance", kwargs={"org_pk": 1, "pk": 134}),
            data=dict(self.payload(), security_sheet=chunked_token(self.user, "hoja.pdf")),
        )
        self.assertEqual(response.status_code, 302)
        self.characteristics.refresh_from_db()
        self.assertTrue(self.characteristics.security_sheet)
        self.assertIn("hoja", self.characteristics.security_sheet.name)
        self.assertGreater(self.characteristics.security_sheet.size, 0)

    def test_step_one_requires_features(self):
        data = self.payload()
        data.pop("features")
        count = Substance.objects.count()
        response = self.client.post(
            reverse("sga:create_sustance", kwargs=self.url_attr), data=data
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("features", response.context["objform"].errors)
        self.assertEqual(Substance.objects.count(), count)

    def test_step_one_requires_density(self):
        data = self.payload()
        data.pop("density")
        response = self.client.post(
            reverse("sga:update_substance", kwargs={"org_pk": 1, "pk": 134}), data=data
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("density", response.context["suschacform"].errors)

    # ---------- paso 2 ----------

    def test_step_four_redirects_to_send_to_review(self):
        SecurityLeaf.objects.get_or_create(substance=self.substance)
        response = self.client.post(
            reverse("sga:step_four", kwargs={"org_pk": 1, "substance": 134}),
            data={"general": "Lavar con agua"},
        )
        self.assertRedirects(
            response,
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134}),
            fetch_redirect_response=False,
        )
        self.assertEqual(
            SecurityLeaf.objects.get(substance=self.substance).general,
            "Lavar con agua",
        )

    def test_step_four_context_step_is_two(self):
        SecurityLeaf.objects.get_or_create(substance=self.substance)
        response = self.client.get(
            reverse("sga:step_four", kwargs={"org_pk": 1, "substance": 134})
        )
        self.assertEqual(response.context["step"], 2)

    # ---------- paso 3 ----------

    def test_send_to_review_is_blocked_without_a_sheet(self):
        self.characteristics.security_sheet = None
        self.characteristics.save(update_fields=["security_sheet"])

        response = self.client.post(
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134}),
            data={"organization": self.org_pk, "laboratories": [self.lab.pk]},
        )
        self.assertRedirects(
            response,
            reverse("sga:update_substance", kwargs={"org_pk": 1, "pk": 134}),
            fetch_redirect_response=False,
        )
        self.substance.refresh_from_db()
        self.assertEqual(self.substance.status, Substance.DRAFT)
        self.assertEqual(ReviewSubstance.objects.count(), 0)

    def test_send_to_review_success(self):
        self.attach_sheet()
        response = self.client.post(
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134}),
            data={"organization": self.org_pk, "laboratories": [self.lab.pk]},
        )
        self.assertRedirects(
            response,
            reverse("sga:get_substance", kwargs=self.url_attr),
            fetch_redirect_response=False,
        )
        self.substance.refresh_from_db()
        self.assertEqual(self.substance.status, Substance.UNDER_REVIEW)
        self.assertEqual(list(self.substance.laboratories.all()), [self.lab])

        review = ReviewSubstance.objects.get(substance=self.substance)
        self.assertFalse(review.is_approved)
        self.assertEqual(review.organization_id, self.org_pk)

    def test_send_to_review_notifies_reviewers(self):
        reviewer = self.make_reviewer()
        self.attach_sheet()

        self.client.post(
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134}),
            data={"organization": self.org_pk, "laboratories": [self.lab.pk]},
        )

        task = PendingTask.objects.get(profile=reviewer.profile)
        self.assertEqual(task.name, "New Substance Request")
        self.assertEqual(
            task.link, reverse("sga:approved_substance", kwargs=self.url_attr)
        )
        # send_email_from_template solo persiste un EmailNotification: mirar
        # mail.outbox daría un verde falso permanente. Además esta aserción
        # atraviesa el try/except silencioso de sga.utils._send.
        self.assertEqual(
            EmailNotification.objects.filter(recipient=reviewer.email).count(), 1
        )

    def test_send_to_review_rejects_a_foreign_organization(self):
        self.attach_sheet()
        other = self.foreign_org()

        response = self.client.post(
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134}),
            data={"organization": other.pk, "laboratories": [self.lab.pk]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("organization", response.context["form"].errors)
        self.assertEqual(ReviewSubstance.objects.count(), 0)
        self.substance.refresh_from_db()
        self.assertEqual(self.substance.organization_id, self.org_pk)

    def test_send_to_review_rejects_a_foreign_laboratory(self):
        self.attach_sheet()
        other = self.foreign_org()
        foreign_lab = Laboratory.objects.create(
            name="Ajeno", organization=other, created_by=self.user
        )

        response = self.client.post(
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134}),
            data={"organization": self.org_pk, "laboratories": [foreign_lab.pk]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("laboratories", response.context["form"].errors)
        self.assertFalse(self.substance.laboratories.exists())

    def test_send_to_review_accepts_several_laboratories(self):
        self.attach_sheet()
        second = self.extra_lab()

        response = self.client.post(
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134}),
            data={
                "organization": self.org_pk,
                "laboratories": [self.lab.pk, second.pk],
            },
        )
        self.assertRedirects(
            response,
            reverse("sga:get_substance", kwargs=self.url_attr),
            fetch_redirect_response=False,
        )
        self.substance.refresh_from_db()
        self.assertEqual(self.substance.status, Substance.UNDER_REVIEW)
        self.assertCountEqual(
            self.substance.laboratories.all(), [self.lab, second]
        )
        # Una sola solicitud para todos: no una por laboratorio.
        self.assertEqual(ReviewSubstance.objects.count(), 1)

    def test_send_to_review_rejects_the_whole_form_if_one_lab_is_foreign(self):
        """Basta un laboratorio ajeno para tumbar el envío, aunque el otro valga."""
        self.attach_sheet()
        foreign_lab = Laboratory.objects.create(
            name="Ajeno", organization=self.foreign_org(), created_by=self.user
        )

        response = self.client.post(
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134}),
            data={
                "organization": self.org_pk,
                "laboratories": [self.lab.pk, foreign_lab.pk],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("laboratories", response.context["form"].errors)
        self.assertFalse(self.substance.laboratories.exists())
        self.assertEqual(ReviewSubstance.objects.count(), 0)

    def test_send_to_review_requires_at_least_one_laboratory(self):
        self.attach_sheet()

        response = self.client.post(
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134}),
            data={"organization": self.org_pk, "laboratories": []},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("laboratories", response.context["form"].errors)
        self.assertEqual(ReviewSubstance.objects.count(), 0)

    def test_send_to_review_of_a_foreign_substance_is_not_found(self):
        foreign = Substance.objects.create(
            created_by=self.user,
            organization=self.foreign_org(),
            comercial_name="ajena",
        )
        response = self.client.get(
            reverse(
                "sga:send_to_review", kwargs={"org_pk": 1, "substance": foreign.pk}
            ),
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 404)

    def test_send_to_review_context_step_is_three(self):
        self.attach_sheet()
        response = self.client.get(
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134})
        )
        self.assertEqual(response.context["step"], 3)
        self.assertTrue(response.context["has_security_sheet"])

    # ---------- aprobación ----------

    def test_approval_creates_the_inventory_object(self):
        self.substance.features.add(self.feature)
        self.characteristics.is_dangerous = True
        self.characteristics.has_threshold = True
        self.characteristics.threshold = 5.0
        self.characteristics.is_pure = True
        self.characteristics.save()
        review = ReviewSubstance.objects.create(substance=self.substance, note=70)

        response = self.client.post(
            reverse("sga:accept_substance", kwargs={"org_pk": 1, "pk": review.pk})
        )
        self.assertEqual(response.status_code, 302)

        review.refresh_from_db()
        self.substance.refresh_from_db()
        self.assertTrue(review.is_approved)
        self.assertEqual(self.substance.status, Substance.APPROVED)

        obj = Object.objects.get(name=self.substance.comercial_name)
        self.assertEqual(obj.type, Object.REACTIVE)
        self.assertEqual(obj.organization, self.substance.organization.root)
        self.assertTrue(obj.is_dangerous)
        self.assertTrue(obj.has_threshold)
        self.assertEqual(obj.threshold, 5.0)
        self.assertTrue(obj.is_pure)
        self.assertEqual(list(obj.features.values_list("pk", flat=True)), [self.feature.pk])

        self.characteristics.refresh_from_db()
        self.assertEqual(self.characteristics.object_related_id, obj.pk)

    def lab_log_entries(self, obj, laboratory):
        """Entradas de bitácora del laboratorio que apuntan a este objeto."""
        return LabOrgLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(Laboratory),
            object_id=laboratory.pk,
            log_entry__object_id=str(obj.pk),
            log_entry__content_type=ContentType.objects.get_for_model(Object),
        )

    def test_approval_registers_the_object_in_every_laboratory(self):
        """El objeto es uno solo, pero su alta consta en cada laboratorio."""
        second = self.extra_lab()
        self.substance.laboratories.set([self.lab, second])
        review = ReviewSubstance.objects.create(substance=self.substance, note=70)

        self.client.post(
            reverse("sga:accept_substance", kwargs={"org_pk": 1, "pk": review.pk})
        )

        obj = Object.objects.get(name=self.substance.comercial_name)
        self.assertEqual(self.lab_log_entries(obj, self.lab).count(), 1)
        self.assertEqual(self.lab_log_entries(obj, second).count(), 1)

    def approve(self):
        review = ReviewSubstance.objects.create(substance=self.substance, note=70)
        self.client.post(
            reverse("sga:accept_substance", kwargs={"org_pk": 1, "pk": review.pk})
        )
        return review

    def test_approval_issues_one_code_per_laboratory(self):
        """Tres laboratorios, tres códigos que solo difieren en su tramo."""
        self.lab.code = "QUG"
        self.lab.save(update_fields=["code"])
        second = self.extra_lab()
        second.code = "FIS"
        second.save(update_fields=["code"])
        self.substance.organization.code = "CIE"
        self.substance.organization.save(update_fields=["code"])
        self.substance.laboratories.set([self.lab, second])

        self.approve()

        codigos = dict(
            SubstanceLaboratory.objects.filter(substance=self.substance).values_list(
                "laboratory_id", "code"
            )
        )
        esperado = f"EQ-QUG-CIE-{self.substance.pk:06d}"
        self.assertEqual(codigos[self.lab.pk], esperado)
        self.assertEqual(codigos[second.pk], esperado.replace("QUG", "FIS"))

    def test_approval_copies_the_first_code_to_the_object(self):
        """El reactivo llega al inventario identificable, no sin código."""
        self.lab.code = "QUG"
        self.lab.save(update_fields=["code"])
        self.substance.organization.code = "CIE"
        self.substance.organization.save(update_fields=["code"])
        self.substance.laboratories.set([self.lab])

        self.approve()

        obj = Object.objects.get(name=self.substance.comercial_name)
        self.assertEqual(obj.code, f"EQ-QUG-CIE-{self.substance.pk:06d}")

    def test_approval_without_acronym_leaves_the_code_empty(self):
        """Sin sigla no se inventa un código, pero aprobar termina bien."""
        self.lab.code = None
        self.lab.save(update_fields=["code"])
        self.substance.laboratories.set([self.lab])

        self.approve()

        enlace = SubstanceLaboratory.objects.get(
            substance=self.substance, laboratory=self.lab
        )
        self.assertIsNone(enlace.code)
        self.assertTrue(
            Object.objects.filter(name=self.substance.comercial_name).exists()
        )

    def test_approval_without_laboratories_still_creates_the_object(self):
        """Sin laboratorios no hay bitácora que escribir, pero el alta no falla."""
        review = ReviewSubstance.objects.create(substance=self.substance, note=70)

        response = self.client.post(
            reverse("sga:accept_substance", kwargs={"org_pk": 1, "pk": review.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Object.objects.filter(name=self.substance.comercial_name).exists()
        )

    def test_approval_is_idempotent(self):
        """Aprobar dos veces no debe duplicar el objeto de inventario."""
        self.substance.features.add(self.feature)
        self.substance.laboratories.set([self.lab])
        review = ReviewSubstance.objects.create(substance=self.substance, note=70)
        url = reverse("sga:accept_substance", kwargs={"org_pk": 1, "pk": review.pk})

        self.client.post(url)
        self.client.post(url)

        objects = Object.objects.filter(
            name=self.substance.comercial_name, type=Object.REACTIVE
        )
        self.assertEqual(objects.count(), 1)
        # Tampoco se duplica la entrada en la bitácora del laboratorio.
        self.assertEqual(self.lab_log_entries(objects.first(), self.lab).count(), 1)

    # ---------- observaciones ----------

    def test_observation_on_a_foreign_substance_is_not_found(self):
        foreign = Substance.objects.create(
            created_by=self.user,
            organization=self.foreign_org(),
            comercial_name="ajena",
        )
        response = self.client.post(
            reverse(
                "sga:add_observation", kwargs={"org_pk": 1, "substance": foreign.pk}
            ),
            data={"description": "no debería entrar"},
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(SubstanceObservation.objects.count(), 0)

    # ---------- de punta a punta ----------

    def test_full_substance_lifecycle(self):
        reviewer = self.make_reviewer()

        # 1. alta con la ficha subida
        response = self.client.post(
            reverse("sga:update_substance", kwargs={"org_pk": 1, "pk": 134}),
            data=dict(self.payload(), security_sheet=chunked_token(self.user, "ciclo.pdf")),
        )
        self.assertRedirects(
            response,
            reverse("sga:step_four", kwargs={"org_pk": 1, "substance": 134}),
            fetch_redirect_response=False,
        )

        # 2. hoja de seguridad
        response = self.client.post(
            reverse("sga:step_four", kwargs={"org_pk": 1, "substance": 134}),
            data={"general": "Ventilar"},
        )
        self.assertRedirects(
            response,
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134}),
            fetch_redirect_response=False,
        )

        # 3. envío a revisión
        response = self.client.post(
            reverse("sga:send_to_review", kwargs={"org_pk": 1, "substance": 134}),
            data={"organization": self.org_pk, "laboratories": [self.lab.pk]},
        )
        self.assertEqual(response.status_code, 302)

        review = ReviewSubstance.objects.get(substance=self.substance)
        self.assertEqual(PendingTask.objects.filter(profile=reviewer.profile).count(), 1)
        self.assertEqual(
            EmailNotification.objects.filter(recipient=reviewer.email).count(), 1
        )

        # 4. aprobación
        response = self.client.post(
            reverse("sga:accept_substance", kwargs={"org_pk": 1, "pk": review.pk})
        )
        self.assertEqual(response.status_code, 302)

        self.substance.refresh_from_db()
        self.characteristics.refresh_from_db()
        self.assertEqual(self.substance.status, Substance.APPROVED)
        self.assertTrue(ReviewSubstance.objects.get(pk=review.pk).is_approved)
        self.assertIsNotNone(self.characteristics.object_related_id)
        # La ficha del paso 1 sigue donde estaba tras todo el recorrido.
        self.assertIn("ciclo", self.characteristics.security_sheet.name)


class SubstanceApiTest(TestCase):
    fixtures = ["substances.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)

    def test_list_survives_a_substance_without_characteristics(self):
        """Una sustancia sin características no debe impedir listar el resto.

        El accesor inverso de un OneToOne lanza excepción cuando no hay fila, así
        que la tabla debe consultarlo de una forma que admita la ausencia.
        """
        Substance.objects.create(
            created_by=self.user,
            organization_id=1,
            comercial_name="sin características",
        )
        response = self.client.get(
            reverse("sga:api-substance-list", kwargs={"org_pk": 1}),
            {"length": 25, "start": 0, "draw": 1},
        )
        self.assertEqual(response.status_code, 200)
