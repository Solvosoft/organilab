Login and register for new organizations
*******************************************

Esta sección describe las formas como se puede uno registrar en organilab.org
/perms/organization/registration


Registro con OTPT
====================


/perms/registration/totp/<int:id>/

Registro con Firma digital
=============================


/perms/create_profile_by_digital_signature/<int:id>

Registro de usuarios invitados por administrador
=====================================================

/perms/organization/manage/users/add/<int:organizacion>/

Registro de usuarios usando QR de laboratorio
=================================================

/register_user_qr/<int:org>/<int:org>/login/<int:pk>/
