from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView
from django_datatables_view.base_datatable_view import BaseDatatableView

from laboratory.models import Object
from laboratory.sustance.forms import SustanceObjectForm, SustanceCharacteristicsForm
from django.utils.translation import ugettext_lazy as _



def create_edit_sustance(request, pk=None):
    instance = Object.objects.filter(pk=pk).first()

    suscharobj=None
    if instance:
        suscharobj = instance.sustancecharacteristics
    postdata=None
    filesdata = None
    if request.method == 'POST':
        postdata = request.POST
        filesdata = request.FILES
    objform = SustanceObjectForm(postdata, instance=instance)
    suschacform = SustanceCharacteristicsForm(postdata, files=filesdata, instance=suscharobj)

    if request.method == 'POST':
        if objform.is_valid() and suschacform.is_valid():
            obj = objform.save(commit=False)
            obj.type = Object.REACTIVE
            obj.save()
            suscharinst = suschacform.save(commit=False)
            suscharinst.obj = obj
            suscharinst.save()
            messages.success(request, _("Sustance saved successfully"))
            return redirect(reverse('laboratory:sustance_list'))

    return render(request, 'laboratory/sustance/sustance_form.html', {
        'objform': objform,
        'suschacform': suschacform
    })

def sustance_list(request):
    #object_list = Object.objects.filter(type=Object.REACTIVE)
    return render(request, 'laboratory/sustance/list.html', {
        'object_url': '#'
    })

class SubstanceDelete(DeleteView):
    model = Object
    success_url = reverse_lazy('laboratory:sustance_list')
    template_name = 'laboratory/sustance/substance_deleteview.html'


class SustanceListJson(BaseDatatableView, UserPassesTestMixin):
    model = Object
    columns = ['id','name','cas_code','action']
    max_display_length = 500

    def test_func(self):
        return True

    def filter_queryset(self, qs):
        qs = qs.filter(type=Object.REACTIVE)
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(code__istartswith=search) |
                Q(name__istartswith=search) |
                Q(sustancecharacteristics__cas_id_number__istartswith=search) |
                Q(synonym__icontains=search)
         )
        # Delete duplicates from queryset
        return qs.distinct()

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            precursor = '<i class="fa fa-tags fa-fw"></i>'
            if item.sustancecharacteristics.is_precursor:
                precursor = '<i class="fa fa-tags fa-fw text-warning"></i>'
            bioaccumulable = '<i class="fa fa-dashboard fa-fw"></i>'
            if item.sustancecharacteristics.bioaccumulable:
                bioaccumulable = '<i class="fa fa-dashboard fa-fw text-warning"></i>'
            is_public = '<i class="fa fa-circle-o "  aria-hidden="true"></i>'
            if item.is_public:
                is_public = '<i class="fa fa-check-circle-o text-warning" aria-hidden="true"></i>'
            name_url = """<a href="{0}" class="label label-info">{1}</a>""".format(reverse('laboratory:sustance_manage',
                                                                                         kwargs={'pk': item.id}),
                                                                                 item.name)
            # FIXME needs to use custom deleteview?
            delete = """<a href="{0}" class="label label-danger">{1}</a>""".format(reverse('laboratory:sustance_delete',
                                                                                         kwargs={'pk': item.id}),
                                                                                 _('Delete'))

            json_data.append([
                is_public+precursor+bioaccumulable,
                name_url,
                item.sustancecharacteristics.cas_id_number,
                delete
            ])
        return json_data