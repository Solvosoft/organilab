"""
Created on /8/2016

@author: natalia
"""

from django.contrib.admin.models import DELETION, CHANGE, ADDITION
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from laboratory.forms import ObjectFeaturesForm
from laboratory.utils import organilab_logentry
from laboratory.views.djgeneric import CreateView, UpdateView, DeleteView
from laboratory.models import ObjectFeatures, Laboratory


@method_decorator(permission_required("laboratory.add_objectfeatures"), name="dispatch")
class FeatureCreateView(CreateView):
    model = ObjectFeatures
    form_class = ObjectFeaturesForm

    def get_context_data(self, **kwargs):
        paginator = Paginator(
            ObjectFeatures.objects.all().distinct().order_by("name"), 10
        )
        page = self.request.GET.get("page")

        context = super(FeatureCreateView, self).get_context_data(**kwargs)
        context["create"] = True

        try:
            context["object_list"] = paginator.page(page)
        except PageNotAnInteger:
            context["object_list"] = paginator.page(1)
        except EmptyPage:
            context["object_list"] = paginator.page(paginator.num_pages)

        return context

    def get_success_url(self):
        if self.lab is not None:
            return reverse_lazy(
                "laboratory:object_feature_create",
                kwargs={"lab_pk": self.lab, "org_pk": self.org},
            )
        return super(FeatureCreateView, self).get_success_url()

    def form_valid(self, form):
        object_feactures = form.save()
        organilab_logentry(
            self.request.user,
            object_feactures,
            ADDITION,
            changed_data=form.changed_data,
            relobj=self.lab,
        )
        return super(FeatureCreateView, self).form_valid(object_feactures)


@method_decorator(
    permission_required("laboratory.change_objectfeatures"), name="dispatch"
)
class FeatureUpdateView(UpdateView):
    model = ObjectFeatures
    form_class = ObjectFeaturesForm

    def get_success_url(self):
        if self.lab is not None:
            return reverse_lazy(
                "laboratory:object_feature_create",
                kwargs={"lab_pk": self.lab, "org_pk": self.org},
            )
        return super(FeatureUpdateView, self).get_success_url()

    def form_valid(self, form):
        object_feactures = form.save()
        organilab_logentry(
            self.request.user,
            object_feactures,
            CHANGE,
            changed_data=form.changed_data,
            relobj=self.lab,
        )
        return super(FeatureUpdateView, self).form_valid(object_feactures)


@method_decorator(
    permission_required("laboratory.delete_objectfeatures"), name="dispatch"
)
class FeatureDeleteView(DeleteView):
    model = ObjectFeatures

    def get_success_url(self):
        if self.lab is not None:
            return reverse_lazy(
                "laboratory:object_feature_create",
                kwargs={"lab_pk": self.lab, "org_pk": self.org},
            )
        return super(FeatureDeleteView, self).get_success_url()

    def form_valid(self, form):
        success_url = self.get_success_url()
        organilab_logentry(self.request.user, self.object, DELETION, relobj=self.lab)
        self.object.delete()
        return HttpResponseRedirect(success_url)
