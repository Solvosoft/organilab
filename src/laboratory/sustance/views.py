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

            warning_precursor = 'fa fa-thumbs-up fa-fw text-success' if item.sustancecharacteristics.is_precursor \
                else 'fa fa-thumbs-down fa-fw text-warning'
            warning_bioaccumulable = 'fa fa-exclamation-triangle fa-fw text-success' if item.sustancecharacteristics.bioaccumulable \
                else 'fa fa-exclamation-triangle fa-fw text-warning'
            warning_is_public = 'fa fa-toggle-on fa-fw text-success' if item.is_public \
                else 'fa fa-toggle-off fa-fw text-warning'

            precursor = '<i class="{0}"></i>'.format(warning_precursor)
            bioaccumulable = '<i class="{0}"></i>'.format(warning_bioaccumulable)
            is_public = '<i class="{0}" aria-hidden="true"></i>'.format(warning_is_public)
            name_url = """<a href="{0}">{1}</a>""".format(reverse('laboratory:sustance_manage',
                                                                  kwargs={'pk': item.id}),
                                                          item.name)
            delete = """<a href="{0}" ><i class="fa fa-trash-o" style="color:red"></i></a>"""\
                .format(reverse('laboratory:sustance_delete',
                                kwargs={'pk': item.id}))

            json_data.append([
                is_public+precursor+bioaccumulable,
                name_url,
                item.sustancecharacteristics.cas_id_number,
                delete
            ])
        return json_data