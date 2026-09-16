from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from djgentelella.models import HistoryRelation

from auth_and_perms.models import Profile, ProfilePermission, Rol
from auth_and_perms.user_merge import (
    MEMBERSHIP,
    MOVE,
    PERSONAL,
    PROFILE_RELATIONS,
    USER_RELATIONS,
    UserManagementError,
    delete_user,
    merge_users,
    relation_label,
)
from laboratory.models import (
    Laboratory,
    OrganizationStructure,
    Protocol,
    ShelfObject,
    UserOrganization,
)
from laboratory.utils import organilab_logentry
from presentation.models import Tutorial, TutorialProgress

SENTINEL = "centinela-test"


class RelationClassificationTest(TestCase):
    """Una relación nueva hacia User o Profile debe clasificarse a conciencia.

    Sin clasificar se trata como MOVE, que no pierde datos pero puede no ser lo
    correcto (por ejemplo, darle al centinela una credencial o un rol).
    """

    def assert_classified(self, model, relations):
        labels = {relation_label(rel) for rel in model._meta.related_objects}
        unclassified = {label for label in labels - set(relations) if not label.endswith(".created_by")}
        self.assertFalse(unclassified, "relaciones sin clasificar en user_merge: %s" % sorted(unclassified))
        stale = set(relations) - labels
        self.assertFalse(stale, "relaciones clasificadas que ya no existen: %s" % sorted(stale))
        self.assertTrue(set(relations.values()) <= {MOVE, MEMBERSHIP, PERSONAL})

    def test_user_relations(self):
        self.assert_classified(User, USER_RELATIONS)

    def test_profile_relations(self):
        self.assert_classified(Profile, PROFILE_RELATIONS)


@override_settings(DELETED_USER_SENTINEL_USERNAME=SENTINEL)
class UserMergeBaseTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.org = OrganizationStructure.objects.first()
        self.lab = Laboratory.objects.first()
        self.actor = User.objects.create_superuser("gestor", "gestor@example.com", "x")
        self.sentinel = User.objects.create_user(SENTINEL, password="x")
        self.source = self.create_user("origen")
        self.target = self.create_user("destino")

    def create_user(self, username):
        user = User.objects.create_user(username, "%s@example.com" % username, "x")
        Profile.objects.get_or_create(user=user)
        return user

    def add_permission(self, user, *roles):
        permission = ProfilePermission.objects.create(
            profile=user.profile,
            organization=self.org,
            content_type=ContentType.objects.get_for_model(OrganizationStructure),
            object_id=self.org.pk,
        )
        permission.rol.add(*roles)
        return permission


class MergeUsersTest(UserMergeBaseTest):
    def test_moves_data_including_soft_deleted_rows(self):
        shelfobject = ShelfObject.objects.first()
        ShelfObject.objects.filter(pk=shelfobject.pk).update(created_by=self.source)
        protocol = Protocol.objects.create(
            name="p", short_description="p", laboratory=self.lab, upload_by=self.source,
            created_by=self.source, file=ContentFile(b"x", name="p.pdf"),
        )
        Protocol.objects_with_deleted.filter(pk=protocol.pk).update(is_deleted=True)
        entry = organilab_logentry(self.source, self.lab, ADDITION, "laboratory", relobj=[self.org])

        merge_users(self.source, self.target, self.actor)

        self.assertFalse(User.objects.filter(pk=self.source.pk).exists())
        self.assertTrue(ShelfObject.objects.filter(pk=shelfobject.pk, created_by=self.target).exists())
        protocol = Protocol.objects_with_deleted.get(pk=protocol.pk)
        self.assertEqual((protocol.upload_by_id, protocol.created_by_id), (self.target.pk, self.target.pk))
        self.assertEqual(LogEntry.objects.get(pk=entry.pk).user, self.target)
        self.assertEqual(HistoryRelation.objects.filter(log_entry=entry).count(), 1)

    def test_merges_rows_that_cannot_be_duplicated(self):
        tutorial = Tutorial.objects.first()
        TutorialProgress.objects.create(user=self.source, tutorial=tutorial, completed=True)
        TutorialProgress.objects.create(user=self.target, tutorial=tutorial, completed=False)
        UserOrganization.objects.create(user=self.source, organization=self.org, type_in_organization=UserOrganization.ADMINISTRATOR)
        UserOrganization.objects.create(user=self.target, organization=self.org, type_in_organization=UserOrganization.LABORATORY_USER)
        rol_a, rol_b = Rol.objects.all()[:2]
        self.add_permission(self.source, rol_a)
        self.add_permission(self.target, rol_b)
        group = Group.objects.create(name="grupo-fusion")
        self.source.groups.add(group)
        self.source.profile.laboratories.add(self.lab)

        merge_users(self.source, self.target, self.actor)

        progress = TutorialProgress.objects.get(user=self.target, tutorial=tutorial)
        self.assertTrue(progress.completed)
        membership = UserOrganization.objects.get(user=self.target, organization=self.org)
        self.assertEqual(membership.type_in_organization, UserOrganization.ADMINISTRATOR)
        permission = ProfilePermission.objects.get(profile=self.target.profile, organization=self.org)
        self.assertEqual(set(permission.rol.all()), {rol_a, rol_b})
        self.assertIn(group, self.target.groups.all())
        self.assertIn(self.lab, self.target.profile.laboratories.all())

    def test_moves_many_to_many_memberships(self):
        self.org.users.add(self.source)
        merge_users(self.source, self.target, self.actor)
        self.assertIn(self.target, self.org.users.all())

    def test_cannot_merge_into_itself_or_own_user(self):
        with self.assertRaises(UserManagementError):
            merge_users(self.source, self.source, self.actor)
        with self.assertRaises(UserManagementError):
            merge_users(self.actor, self.target, self.actor)

    def test_only_superuser_can_merge_superuser(self):
        manager = self.create_user("gestor-plataforma")
        User.objects.filter(pk=self.source.pk).update(is_superuser=True)
        self.source.refresh_from_db()
        with self.assertRaises(UserManagementError):
            merge_users(self.source, self.target, manager)


class DeleteUserTest(UserMergeBaseTest):
    def test_data_goes_to_sentinel_and_memberships_are_dropped(self):
        shelfobject = ShelfObject.objects.first()
        ShelfObject.objects.filter(pk=shelfobject.pk).update(created_by=self.source)
        UserOrganization.objects.create(user=self.source, organization=self.org)
        rol = Rol.objects.first()
        self.add_permission(self.source, rol)
        entry = organilab_logentry(self.source, self.lab, ADDITION, "laboratory", relobj=[self.org])

        delete_user(self.source, self.actor)

        self.assertFalse(User.objects.filter(pk=self.source.pk).exists())
        self.assertTrue(ShelfObject.objects.filter(pk=shelfobject.pk, created_by=self.sentinel).exists())
        entry = LogEntry.objects.get(pk=entry.pk)
        self.assertEqual(entry.user, self.sentinel)
        self.assertIn("origen", entry.object_repr)
        self.assertEqual(HistoryRelation.objects.filter(log_entry=entry).count(), 1)
        self.assertFalse(UserOrganization.objects.filter(user=self.sentinel).exists())
        self.assertFalse(ProfilePermission.objects.filter(profile__user=self.sentinel).exists())

    def test_without_sentinel_nothing_is_deleted(self):
        self.sentinel.delete()
        with self.assertRaises(UserManagementError):
            delete_user(self.source, self.actor)
        self.assertTrue(User.objects.filter(pk=self.source.pk).exists())

    def test_sentinel_and_own_user_are_protected(self):
        with self.assertRaises(UserManagementError):
            delete_user(self.sentinel, self.actor)
        with self.assertRaises(UserManagementError):
            delete_user(self.actor, self.actor)

    def test_task_deletion_without_actor(self):
        delete_user(self.source)
        self.assertFalse(User.objects.filter(pk=self.source.pk).exists())
