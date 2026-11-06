"""Tutoriales guiados: índice por capítulo, API de progreso y etiquetas de plantilla."""
import json

from django.contrib.auth.models import AnonymousUser, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.template import Context, Template, TemplateSyntaxError
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse

from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import Laboratory, OrganizationStructure, UserOrganization
from presentation import views
from presentation.models import Tutorial, TutorialProgress, TutorialStep
from presentation.templatetags import tutorial_tags


def dar_rol(user, organization, rol):
    permission = ProfilePermission.objects.create(
        profile=user.profile, organization=organization,
        content_type=ContentType.objects.get_for_model(OrganizationStructure),
        object_id=organization.pk,
    )
    permission.rol.add(rol)


class TutorialBaseTest(TestCase):
    """Una organización con laboratorio y un usuario cuyo rol da acceso a la institución."""

    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationStructure.objects.create(name="Universidad")
        cls.laboratory = Laboratory.objects.create(name="Lab", organization=cls.organization)
        cls.rol = Rol.objects.create(name="Rol de tutoriales")
        cls.rol.permissions.add(Permission.objects.get(codename="institution_can_access"))
        cls.other_rol = Rol.objects.create(name="Rol ajeno")
        cls.user = User.objects.create_user(username="tutor", password="pass")
        Profile.objects.create(user=cls.user)
        UserOrganization.objects.create(user=cls.user, organization=cls.organization,
                                        type_in_organization=3, status=True)
        dar_rol(cls.user, cls.organization, cls.rol)

    def make_tutorial(self, slug, url_name, steps=1, **kwargs):
        tutorial = Tutorial.objects.create(title=slug.title(), slug=slug, url_name=url_name, **kwargs)
        for order in range(steps):
            TutorialStep.objects.create(tutorial=tutorial, order=order, step_key="paso-%d" % order,
                                        title="Paso %d" % order, content="<p>Hola</p>")
        return tutorial


class IndexTutorialTest(TutorialBaseTest):

    def setUp(self):
        Tutorial.objects.all().delete()
        self.client.force_login(self.user)

    def items(self, response):
        return {item["tutorial"].slug: item for items in response.context["chapters"].values() for item in items}

    def test_resuelve_la_url_de_cada_tutorial_y_filtra_por_rol(self):
        lab = self.make_tutorial("salas", "laboratory:rooms_list", chapter="LABORATORIOS")
        self.make_tutorial("procedimientos", "academic:procedure_list", chapter="PROCEDIMIENTOS")
        self.make_tutorial("portada", "index")
        self.make_tutorial("roto", "ruta_que_no_existe")
        restringido = self.make_tutorial("restringido", "index")
        restringido.target_roles.add(self.other_rol)
        TutorialProgress.objects.create(user=self.user, tutorial=lab, current_step=1)

        response = self.client.get(reverse("tutorials", kwargs={"org_pk": self.organization.pk}))
        self.assertEqual(response.status_code, 200)
        items = self.items(response)
        self.assertNotIn("restringido", items)
        self.assertEqual(items["salas"]["target_url"], reverse(
            "laboratory:rooms_list", kwargs={"org_pk": self.organization.pk, "lab_pk": self.laboratory.pk}))
        self.assertEqual(items["salas"]["progress"].current_step, 1)
        self.assertEqual(items["procedimientos"]["target_url"],
                         reverse("academic:procedure_list", kwargs={"org_pk": self.organization.pk}))
        self.assertEqual(items["portada"]["target_url"], "%s?org_pk=%s" % (reverse("index"), self.organization.pk))
        self.assertIsNone(items["roto"]["target_url"])
        self.assertEqual(items["salas"]["step_count"], 1)

    def test_sin_organizacion_en_la_url_usa_la_del_perfil(self):
        superuser = User.objects.create_superuser(username="root", password="pass")
        Profile.objects.create(user=superuser)
        dar_rol(superuser, self.organization, self.rol)
        self.make_tutorial("procedimientos", "academic:procedure_list")
        self.client.force_login(superuser)
        response = self.client.get(reverse("tutorials", kwargs={"org_pk": 0}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.items(response)["procedimientos"]["target_url"],
                         reverse("academic:procedure_list", kwargs={"org_pk": self.organization.pk}))

    def test_rol_sin_acceso_a_la_institucion_recibe_403(self):
        otro = OrganizationStructure.objects.create(name="Ajena")
        response = self.client.get(reverse("tutorials", kwargs={"org_pk": otro.pk}))
        self.assertRedirects(response, reverse("error_view") + "?status=403", fetch_redirect_response=False)

    def test_sin_perfil_no_revienta(self):
        """El middleware corta antes a quien no tiene perfil; la vista igual se defiende."""
        superuser = User.objects.create_superuser(username="sinperfil", password="pass")
        request = RequestFactory().get("/")
        request.user = superuser
        self.assertEqual(views.index_tutorial(request, org_pk=0).status_code, 200)


class TutorialApiTest(TutorialBaseTest):

    def setUp(self):
        self.client.force_login(self.user)
        self.tutorial = self.make_tutorial("api", "index")

    def post(self, name, data):
        body = data if isinstance(data, str) else json.dumps(data)
        return self.client.post(reverse(name), data=body, content_type="application/json")

    def test_progreso_valida_la_peticion(self):
        self.assertEqual(self.post("tutorial_progress_api", "{no es json").status_code, 400)
        self.assertEqual(self.post("tutorial_progress_api", {}).status_code, 400)
        self.assertEqual(self.post("tutorial_progress_api", {"tutorial_id": 999999}).status_code, 404)

    def test_progreso_completado_y_descartado(self):
        response = self.post("tutorial_progress_api", {
            "tutorial_id": self.tutorial.pk, "step_order": 2, "completed": True, "dismissed": True})
        self.assertEqual(response.json(), {"ok": True})
        progress = TutorialProgress.objects.get(user=self.user, tutorial=self.tutorial)
        self.assertEqual(progress.current_step, 2)
        self.assertTrue(progress.completed)
        self.assertIsNotNone(progress.completed_at)
        self.assertTrue(progress.dismissed)

    def test_alternar_tutoriales(self):
        response = self.client.post(reverse("tutorial_toggle_api"))
        self.assertEqual(response.json(), {"show_tutorials": False})
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.show_tutorials)

    def test_alternar_sin_perfil(self):
        request = RequestFactory().post("/")
        request.user = User.objects.create_user(username="sinperfil")
        response = views.tutorial_toggle_api(request)
        self.assertEqual(response.status_code, 400)

    def test_reactivar(self):
        TutorialProgress.objects.create(user=self.user, tutorial=self.tutorial, dismissed=True,
                                        completed=True, current_step=3)
        self.assertEqual(self.post("tutorial_reactivate_api", "{no es json").status_code, 400)
        self.assertEqual(self.post("tutorial_reactivate_api", {}).status_code, 400)
        response = self.post("tutorial_reactivate_api", {"tutorial_id": self.tutorial.pk})
        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(response.cookies["tutorial_reactivated"].value, str(self.tutorial.pk))
        progress = TutorialProgress.objects.get(user=self.user, tutorial=self.tutorial)
        self.assertEqual((progress.dismissed, progress.completed, progress.current_step), (False, False, 0))


class TutorialLauncherTest(TutorialBaseTest):
    url_name = "academic:procedure_list"

    def setUp(self):
        Tutorial.objects.all().delete()

    def context(self, user, resolved=True, **extra):
        request = RequestFactory().get("/")
        request.user = user
        request.resolver_match = resolve(
            reverse(self.url_name, kwargs={"org_pk": self.organization.pk})) if resolved else None
        return {"request": request, "org_pk": self.organization.pk, **extra}

    def config(self, html):
        start = html.index("window._tutorialConfig = ") + len("window._tutorialConfig = ")
        return json.loads(html[start:html.index(";</script>")])

    def test_sin_perfil_o_sin_ruta_no_muestra_nada(self):
        self.make_tutorial("uno", self.url_name)
        sin_perfil = User.objects.create_user(username="sinperfil")
        self.assertEqual(tutorial_tags.tutorial_launcher(self.context(sin_perfil)), "")
        self.assertEqual(tutorial_tags.tutorial_launcher(self.context(self.user, resolved=False)), "")
        self.assertEqual(tutorial_tags._get_user_rol_ids(sin_perfil, self.organization.pk), set())

    def test_arma_la_configuracion_de_los_tutoriales_pendientes(self):
        con_imagen = self.make_tutorial("con-imagen", self.url_name)
        paso = con_imagen.steps.get()
        paso.image.name = "tutorial_images/paso.png"
        paso.save()
        TutorialProgress.objects.create(user=self.user, tutorial=con_imagen, current_step=1)
        descartado = self.make_tutorial("descartado", self.url_name)
        TutorialProgress.objects.create(user=self.user, tutorial=descartado, dismissed=True)
        self.make_tutorial("sin-pasos", self.url_name, steps=0)
        self.make_tutorial("automatico", self.url_name, auto_start=True)

        config = self.config(tutorial_tags.tutorial_launcher(self.context(self.user)))
        by_slug = {t["slug"]: t for t in config["tutorials"]}
        self.assertEqual(set(by_slug), {"con-imagen", "automatico"})
        self.assertEqual(by_slug["con-imagen"]["currentStep"], 1)
        self.assertTrue(by_slug["con-imagen"]["steps"][0]["imageUrl"].endswith("tutorial_images/paso.png"))
        self.assertEqual(config["autoStart"], ["automatico"])
        self.assertTrue(TutorialProgress.objects.filter(user=self.user, tutorial__slug="automatico").exists())

    def test_todos_descartados_no_muestra_boton(self):
        tutorial = self.make_tutorial("visto", self.url_name)
        TutorialProgress.objects.create(user=self.user, tutorial=tutorial, completed=True)
        self.assertEqual(tutorial_tags.tutorial_launcher(self.context(self.user)), "")


class TutorialStepTagTest(TutorialBaseTest):
    source = '{% load tutorial_tags %}{% tutorial_step "guia" "paso" %}hola{% end_tutorial_step %}'

    def render(self, user=None):
        context = {}
        if user is not None:
            request = RequestFactory().get("/")
            request.user = user
            context["request"] = request
        return Template(self.source).render(Context(context))

    def test_envuelve_solo_si_el_usuario_ve_tutoriales(self):
        self.assertEqual(self.render(), "hola")
        self.assertEqual(self.render(AnonymousUser()), "hola")
        self.assertEqual(self.render(User.objects.create_user(username="sinperfil")), "hola")
        self.assertEqual(self.render(self.user),
                         '<div data-tutorial-slug="guia" data-tutorial-step="paso">hola</div>')
        self.user.profile.show_tutorials = False
        self.user.profile.save()
        self.assertEqual(self.render(self.user), "hola")

    def test_exige_dos_argumentos(self):
        with self.assertRaises(TemplateSyntaxError):
            Template('{% load tutorial_tags %}{% tutorial_step "guia" %}x{% end_tutorial_step %}')

    def test_marcador(self):
        html = Template('{% load tutorial_tags %}{% tutorial_marker "guia" "paso" "#boton" %}').render(Context())
        self.assertIn('data-tutorial-target="#boton"', html)
        self.assertIn('data-tutorial-slug="guia"', html)
