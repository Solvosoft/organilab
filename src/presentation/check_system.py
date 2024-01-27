from django.http import HttpResponse


def do_checks(request):
    if 'raise' in request.GET:
        return 1/0
    return HttpResponse("ok")
