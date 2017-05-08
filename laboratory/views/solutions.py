from django.urls import reverse_lazy
from django.views.generic import FormView
from django.utils.translation import ugettext_lazy as _
from django import forms
from pyEQL import Solution
from laboratory.models import Solution


class SolutionCalculatorForm(forms.Form):
    solutes = forms.CharField(widget=forms.Textarea,
                              help_text=_('Write in each line the formula along with its amount, separated by a '
                                          'whitespace'))
    volume = forms.CharField(label=_('Volumen'))
    temperature = forms.IntegerField(label=_('Temperature'), initial=25)
    pressure = forms.IntegerField(label=_('Pressure'), initial=1)
    pH = forms.IntegerField(label=_('pH'), initial=7)

    def clean_solutes(self):
        final_solutes = []
        solutes = self.cleaned_data.get('solutes')
        splitted_solutes = solutes.split('\n')
        for line in splitted_solutes:
            final_solutes.append(line.strip().split(','))
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


class SolutionCalculatorView(FormView):
    form_class = SolutionCalculatorForm
    template_name = 'laboratory/solution_calculator.html'
    lab_pk = None

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(SolutionCalculatorView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SolutionCalculatorView, self).get_context_data(**kwargs)
        return context

    def get_success_url(self):
        return reverse_lazy('laboratory:solution_calculator', kwargs={'lab_pk': self.lab_pk})

    def form_valid(self, form):
        Solution.objects.create(**form.cleaned_data)
        return super(SolutionCalculatorView, self).form_valid(form=form)
