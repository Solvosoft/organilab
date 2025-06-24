"""
ASGI config for pylatam2025 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""


from djgentelella.firmador_digital.config.asgi_config import AsgiConfig

application = AsgiConfig('organilab.settings').application
