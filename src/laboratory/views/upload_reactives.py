from django.forms import formset_factory
from ..forms import ReactiveUploadForm


def upload_reactives(request):
    if request.method == "POST":
        ReactiveFormSet = formset_factory(ReactiveUploadForm, extra=0)

        formset = ReactiveFormSet(initial=request.POST.getlist("form"))
