from django.urls import reverse
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, render
from django.views.generic import ListView

from academic.models import SubstanceSGA
from django.contrib.auth.models import User
from academic.substance.forms import SustanceObjectForm, SustanceCharacteristicsForm
from laboratory.validators import isValidate_molecular_formula


@permission_required('laboratory.change_object')
def create_edit_sustance(request, pk=None):
    instance = SubstanceSGA.objects.filter(pk=pk).first()

    suscharobj=None
    if instance:
        suscharobj = instance.sustancecharacteristicssga
    postdata=None
    filesdata = None
    if request.method == 'POST':
        postdata = request.POST

    objform = SustanceObjectForm(postdata, instance=instance)
    suschacform = SustanceCharacteristicsForm(postdata, instance=suscharobj)
    if request.method == 'POST':
        if objform.is_valid() and suschacform.is_valid():
            obj = objform.save(commit=False)
            obj.creator=request.user
            obj.save()
            objform.save_m2m()
            suscharinst = suschacform.save(commit=False)
            suscharinst.substance = obj

            molecular_formula = suschacform.cleaned_data["molecular_formula"]
            if isValidate_molecular_formula(molecular_formula):
                suscharinst.valid_molecular_formula = True

            suscharinst.save()
            suschacform.save_m2m()
            return redirect(reverse('index'))


    return render(request, 'academic/substance/create_sustance.html', {
        'objform': objform,
        'suschacform': suschacform,
        'instance': instance,
    })


def get_substances(request):
    substances=None

    if request.user:
        substances = SubstanceSGA.objects.filter(creator=request.user)

    return render(request, 'academic/substance/list_substance.html', context={'substances':substances})

def get_list_substances(request):
    substances=None

    if request.user:
        substances = SubstanceSGA.objects.filter(is_approved=False).order_by('-id')

    return render(request, 'academic/substance/check_substances.html', context={'substances':substances})

def check_list_substances(request):
    substances=None

    if request.user:
        substances = SubstanceSGA.objects.filter(is_approved=False).order_by('--pk')

    return render(request, 'academic/substance/check_substances.html', context={'substances':substances})

def approve_substances(request,pk):
    substances=SubstanceSGA.objects.filter(pk=pk).first()
    if substances:
        substances.is_approved=True
        substances.save()
        return redirect('approved_substance')
    return redirect('approved_substance')

def delete_substance(request,pk):
    substances=SubstanceSGA.objects.filter(pk=pk).first()
    if substances:
        substances.delete()
        return redirect('get_substance')
    return redirect('get_substance')
