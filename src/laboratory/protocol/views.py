from django.contrib.admin.models import ADDITION, DELETION
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from rest_framework.reverse import reverse_lazy

from laboratory.models import Protocol, Laboratory, Object
from laboratory.protocol.forms import ProtocolForm
from laboratory.utils import organilab_logentry
from laboratory.views.djgeneric import CreateView, DeleteView, UpdateView

@permission_required('laboratory.view_protocol')
def protocol_list(request, *args, **kwargs ):
    context={
        'laboratory': kwargs['lab_pk']
    }
    return render(request, 'laboratory/protocol/protocol_list.html', context=context)

@method_decorator(permission_required('laboratory.add_protocol'), name='dispatch')
class ProtocolCreateView(CreateView):
    model = Protocol
    template_name = 'laboratory/protocol/create.html'
    form_class = ProtocolForm


    def get_success_url(self):
        return reverse_lazy('laboratory:protocol_list', args=(self.lab,))

    def get_context_data(self, **kwargs):
        context = super(ProtocolCreateView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab
        return context

    def form_valid(self, form):
        protocol = form.save(commit=False)
        laboratory = get_object_or_404(Laboratory, pk = self.lab)
        protocol.laboratory = laboratory
        protocol.upload_by = self.request.user
        protocol.save()
        ct = ContentType.objects.get_for_model(self.object)
        organilab_logentry(self.request.user, ct, self.object, ADDITION, 'incident report')
        return super(ProtocolCreateView,self).form_valid(form)


class ProtocolUpdateView(UpdateView):
    model = Protocol
    success_url = '/'
    form_class = ProtocolForm
    template_name = 'laboratory/protocol/update.html'

    def get_success_url(self):
        return reverse_lazy('laboratory:protocol_list', args=(self.lab,))

    def form_valid(self, form):
        dev = super().form_valid()
        ct = ContentType.objects.get_for_model(self.object)
        organilab_logentry(self.request.user, ct, self.object, DELETION, 'Protocol')
        return dev


class ProtocolDeleteView(DeleteView):
    model = Protocol
    template_name = 'laboratory/protocol/delete.html'
    success_url = ''

    def get_success_url(self):
        return reverse_lazy('laboratory:protocol_list', args=(self.lab,))

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        ct = ContentType.objects.get_for_model(self.object)
        organilab_logentry(request.user, ct, self.object, DELETION, 'Protocol')
        self.object.delete()
        return HttpResponseRedirect(success_url)