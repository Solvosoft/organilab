from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from laboratory.models import Provider, Laboratory
from .djgeneric import CreateView, ListView, UpdateView
from laboratory.forms import ProviderForm
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404

@method_decorator(permission_required('laboratory.add_provider'), name='dispatch')
class ProviderCreate(CreateView):
    model = Provider
    form_class = ProviderForm
    template_name = 'laboratory/provider_add.html'
    lab_pk_field = 'pk'

    def form_valid(self, form):
        provider = form.save(commit=False)

        lab = get_object_or_404(Laboratory, pk=self.lab)
        provider.laboratory = lab
        provider.save()
        return super(ProviderCreate, self).form_valid(provider)


    def get_success_url(self):
        return reverse_lazy('laboratory:list_provider', args=(self.lab,))


@method_decorator(permission_required('laboratory.change_provider'), name='dispatch')
class ProviderUpdate(UpdateView):
    model = Provider
    form_class = ProviderForm
    template_name = 'laboratory/provider_update.html'

    def get_success_url(self):
        lab = self.object.laboratory.pk
        return reverse_lazy('laboratory:list_provider', args=(lab,))

@method_decorator(permission_required('laboratory.view_provider'), name='dispatch')
class ProviderList(ListView):
    model = Provider
    template_name = 'laboratory/provider_list.html'

    def get_queryset(self):
        providers = Provider.objects.filter(laboratory__pk=int(self.lab))
        return providers
