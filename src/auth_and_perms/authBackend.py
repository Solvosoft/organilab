from django.contrib.auth.backends import ModelBackend


class OrganizationModelBackend(ModelBackend):
    def get_all_permissions(self, user_obj, obj=None):


        return super().get_all_permissions(user_obj, obj=obj)