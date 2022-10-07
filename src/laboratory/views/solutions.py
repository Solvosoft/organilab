from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, DetailView
from django.utils.translation import gettext_lazy as _
from django import forms
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from pyEQL import Solution
from laboratory.models import Solution
from laboratory.validators import validate_molecular_formula
from laboratory.decorators import has_lab_assigned


@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.view_solution'), name='dispatch')
class SolutionListView(ListView):
    model = Solution
    template_name = 'laboratory/solution_list.html'
    lab_pk = None

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(SolutionListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SolutionListView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        return context


@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.view_solution'), name='dispatch')
class SolutionDetailView(DetailView):
    model = Solution
    template_name = 'laboratory/solution_detail.html'
    lab_pk = None

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(SolutionDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        keys = [
            ('alkalinity', True, _('Alkalinity')),
            ('bjerrum_length', True, _('Bjerrum length')),
            ('charge_balance', False, _('Charge balance')),
            ('chemical_potential_energy', True, _('Chemical potential energy')),
            ('conductivity', True, _('Conductivity')),
            ('debye_length', True, _('Debye length')),
            ('density', True, _('Density')),
            ('dielectric_constant', True, _('Dielectric constant')),
            ('hardness', True, _('Hardness')),
            ('ionic_strength', True, _('Ionic strength')),
            ('mass', True, _('Mass')),
            ('moles_solvent', True, _('Moles solvent')),
            ('osmotic_coefficient', True, _('Osmotic coefficient')),
            ('osmotic_pressure', True, _('Osmotic pressure')),
            ('pressure', True, _('Pressure')),
            ('temperature', True, _('Temperature')),
            ('total_moles_solute', True, _('Total moles solute')),
            ('viscosity_dynamic', True, _('Viscosity dynamic')),
            ('viscosity_kinematic', True, _('Viscosity kinematic')),
            ('viscosity_relative', True, _('Viscosity relative')),
            ('volume', True, _('Volume')),
            ('water_activity', False, _('Water activity'))
        ]
        context = super(SolutionDetailView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        context['solution_details'] = {}
        for key, has_unit, verbose_name in keys:
            pysolution = self.object.solution_object
            kallable = getattr(pysolution, 'get_{}'.format(key))
            try:
                if has_unit:
                    context['solution_details'][key] = (verbose_name, '{} {}'.format(kallable().m, str(kallable().u)))
                else:
                    context['solution_details'][key] = (verbose_name, kallable())
            except Exception as e:
                print(e)
        return context


class SolutionCalculatorForm(forms.Form):
    name = forms.CharField(label=_('Name'), max_length=255, help_text=_('Descriptive name of the solution'))
    solutes = forms.CharField(label=_('Solutes'), widget=forms.Textarea,
                              help_text=_('Write in each line the formula along with its amount, separated by a comma'))
    volume = forms.CharField(label=_('Volumen'), help_text=_('For example: 500 mL, 1 L'))
    temperature = forms.IntegerField(label=_('Temperature'), initial=25, help_text=_('In degC'))
    pressure = forms.IntegerField(label=_('Pressure'), initial=1, help_text=_('In atm'))
    pH = forms.IntegerField(label=_('pH'), initial=7)

    def clean_solutes(self):
        final_solutes = []
        solutes = self.cleaned_data.get('solutes')
        splitted_solutes = solutes.split('\n')
        for line in splitted_solutes:
            values = line.strip().split(',')
            if len(values) != 2:
                raise forms.ValidationError(_('Incorrect solute definition'))
            try:
                validate_molecular_formula(values[0])
            except:
                raise forms.ValidationError(_('Incorrect solute definition'))
            final_solutes.append(values)
        return final_solutes

    def clean_temperature(self):
        return '%d degC' % self.cleaned_data.get('temperature')

    def clean_pressure(self):
        return '%d atm' % self.cleaned_data.get('pressure')

    def clean(self):
        cleaned_data = super(SolutionCalculatorForm, self).clean()
        try:
            Solution(**cleaned_data)
        except:
            raise forms.ValidationError(_('There are errors in the solution definition, please try again'))
        return cleaned_data


@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.view_solution'), name='dispatch')
class SolutionCalculatorView(FormView):
    form_class = SolutionCalculatorForm
    template_name = 'laboratory/solution_calculator.html'
    lab_pk = None
    solution = None

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(SolutionCalculatorView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SolutionCalculatorView, self).get_context_data(**kwargs)
        context['laboratory'] = self.lab_pk
        return context

    def get_success_url(self):
        return reverse_lazy('laboratory:solution_detail', kwargs={
            'lab_pk': self.lab_pk,
            'pk': self.solution.pk
        })

    def form_valid(self, form):
        self.solution = Solution.objects.create(**form.cleaned_data)
        return super(SolutionCalculatorView, self).form_valid(form=form)
