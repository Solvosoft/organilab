import json

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from derb.models import CustomForm


@login_required
@permission_required("derb.view_customform")
def previewForm(request, org_pk, form_id):
    template_name = "formBuilder/preview_form.html"

    form = CustomForm.objects.get(id=form_id)
    schema = form.schema

    context = {"schema": json.dumps(schema, indent=2), "org_pk": org_pk}

    return render(request, template_name, context)
