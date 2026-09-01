from django.conf import settings


def oidc_enabled(request):
    return {"oidc_enabled": bool(getattr(settings, "OIDC_RP_CLIENT_ID", ""))}
