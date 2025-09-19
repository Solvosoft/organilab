from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils.text import slugify
from django.utils.timezone import now
from djgentelella.widgets import core as genwidgets

from presentation.utils import build_qr_instance
from report.forms import LaboratoryRoomReportForm, ValidateFurnitureForm
from ..forms import FurnitureForm, CatalogForm, FurnitureLabRoomForm
from ..utils import organilab_logentry

"""
Created on 26/12/2016

@author: luisza
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django_ajax.decorators import ajax


from laboratory.models import Furniture, Laboratory, LaboratoryRoom, Shelf
from laboratory.shelf_utils import get_dataconfig
from .djgeneric import ListView, CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _


@method_decorator(permission_required("laboratory.do_report"), name="dispatch")
class FurnitureReportView(ListView):
    model = Furniture
    template_name = "report/base_report_form_view.html"

    def get_queryset(self):
        return Furniture.objects.filter(labroom__laboratory=self.lab)

    def get_context_data(self, **kwargs):
        context = super(FurnitureReportView, self).get_context_data(**kwargs)
        lab_obj = get_object_or_404(Laboratory, pk=self.lab)
        title = _("Objects by Furniture Report")
        initial_data = {
            "name": slugify(title + " " + now().strftime("%x").replace("/", "-")),
            "title": title,
            "organization": self.org,
            "report_name": "report_furniture",
            "laboratory": lab_obj,
            "all_labs_org": False,
        }

        if self.request.method == "GET":
            furniture_form = ValidateFurnitureForm(self.request.GET)
            if furniture_form.is_valid():
                furniture = Furniture.objects.get(
                    pk=furniture_form.cleaned_data["furniture"]
                )
                lab_obj = get_object_or_404(
                    Laboratory, pk=furniture_form.cleaned_data["laboratory"]
                )
                initial_data.update(
                    {
                        "furniture": furniture,
                        "lab_room": furniture.labroom,
                        "laboratory": lab_obj,
                    }
                )

        context.update(
            {
                "title_view": title,
                "report_urlnames": ["reports_furniture_detail"],
                "form": LaboratoryRoomReportForm(initial=initial_data),
            }
        )
        return context


@method_decorator(permission_required("laboratory.add_furniture"), name="dispatch")
class FurnitureCreateView(CreateView):
    model = Furniture
    fields = ("name", "type")

    def get(self, request, *args, **kwargs):
        self.labroom = kwargs["labroom"]
        return super(FurnitureCreateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.labroom = kwargs["labroom"]
        return super(FurnitureCreateView, self).post(request, *args, **kwargs)

    def generate_qr(self):
        schema = self.request.scheme + "://"
        domain = schema + self.request.get_host()
        url = domain + reverse(
            "laboratory:rooms_list", kwargs={"org_pk": self.org, "lab_pk": self.lab}
        )
        url = url + "#labroom=%d&furniture=%d" % (self.labroom, self.object.pk)
        build_qr_instance(url, self.object, self.org)

    def form_valid(self, form):
        self.object = form.save(commit=False)

        self.object.labroom = get_object_or_404(LaboratoryRoom, pk=self.labroom)
        self.object.created_by = self.request.user
        self.object.save()
        self.generate_qr()
        organilab_logentry(
            self.request.user,
            self.object,
            ADDITION,
            "furniture",
            changed_data=form.changed_data,
            relobj=self.lab,
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(
            "laboratory:furniture_update", args=(self.org, self.lab, self.object.pk)
        )

    def get_context_data(self, **kwargs):
        context = CreateView.get_context_data(self, **kwargs)
        lab = get_object_or_404(Laboratory, pk=self.lab)
        context["object_list"] = self.model.objects.filter(
            labroom__in=lab.laboratoryroom_set.all()
        ).order_by("labroom")
        return context

    class Meta:
        model = Furniture
        fields = "__all__"
        widgets = {
            "name": genwidgets.TextInput(),
            "type": genwidgets.Select(),
        }


@method_decorator(permission_required("laboratory.change_furniture"), name="dispatch")
class FurnitureUpdateView(UpdateView):
    model = Furniture
    success_url = "/"
    form_class = FurnitureForm

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context["dataconfig"] = self.build_configdata()
        return context

    def get_dataconfig(self):
        dataconfig = self.object.dataconfig
        return get_dataconfig(dataconfig)

    def build_configdata(self):
        dataconfig = self.get_dataconfig()
        row = len(dataconfig)
        if row > 0:
            col = len(dataconfig[0])
        else:
            col = 0
        return render_to_string(
            "laboratory/dataconfig.html",
            {
                "dataconfig": dataconfig,
                "obj": self.object,
                "col": col,
                "row": row,
                "org_pk": self.org,
                "laboratory": self.lab,
            },
            request=self.request,
        )

    def get_success_url(self):
        return reverse_lazy("laboratory:rooms_create", args=(self.org, self.lab))

    def form_valid(self, form):
        shelfs = form.cleaned_data["shelfs"]
        if shelfs:
            Shelf.objects.filter(pk__in=shelfs).delete()
        self.object = form.save()

        organilab_logentry(
            self.request.user,
            self.object,
            CHANGE,
            "furniture",
            changed_data=form.changed_data,
            relobj=self.lab,
        )
        return redirect(self.get_success_url())


@method_decorator(permission_required("laboratory.delete_furniture"), name="dispatch")
class FurnitureDelete(DeleteView):
    model = Furniture
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy("laboratory:rooms_create", args=(self.org, self.lab))

    def form_valid(self, form):
        success_url = self.get_success_url()
        organilab_logentry(
            self.request.user, self.object, DELETION, "furniture", relobj=self.lab
        )
        self.object.delete()
        return HttpResponseRedirect(success_url)


@login_required
def list_furniture_render(request, org_pk, lab_pk):
    furnitures = Furniture.objects.filter(labroom__laboratory=lab_pk)

    if request.method == "GET":
        form = FurnitureLabRoomForm(request.GET)
        if form.is_valid():
            furnitures = Furniture.objects.filter(
                labroom__laboratory=lab_pk, labroom=form.cleaned_data["labroom"]
            )

    return render_to_string(
        "laboratory/furniture_list.html",
        context={
            "object_list": furnitures,
            "laboratory": lab_pk,
            "org_pk": org_pk,
            "request": request,
        },
    )


# Here we need to discuss if it is necesary to look for lab_pk in ajax requests
@login_required
@ajax
def list_furniture(request, org_pk, lab_pk):
    return {
        "inner-fragments": {
            "#furnitures": list_furniture_render(request, org_pk, lab_pk),
            ".jsmessage": "<script>see_prototype_shelf_field();</script>",
        },
    }


@login_required
def add_catalog(request, key):

    if request.method == "POST":
        form = CatalogForm(request.POST, initial={"key": key})
        if form.is_valid():
            instance = form.save()
            return JsonResponse(
                {"ok": True, "id": instance.pk, "text": instance.description}
            )
        return JsonResponse(
            {"ok": False, "title": _("ERROR"), "message": _("Data is not valid")}
        )

    form = CatalogForm(initial={"key": key})
    url = reverse("laboratory:add_furniture_type_catalog")
    title = _("New furniture type")
    if key == "container_type":
        title = _("New Container type")
    if key == "shelfobject_status":
        title = _("New Shelfobject status")
        url = reverse("laboratory:add_shelfobject_status")
    if key == "structure_type":
        title = _("New Structure type")
        url = reverse("laboratory:add_structure_type_catalog")
    data = {
        "ok": True,
        "title": title,
        "message": """
        <form method="post" action="%s">
            %s
        </form>
        """
        % (url, str(form.as_horizontal())),
    }
    return JsonResponse(data)
