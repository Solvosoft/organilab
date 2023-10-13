from django.http import HttpResponse
from django.http import HttpResponseForbidden
from report.models import TaskReport

def media_access(request, path):
    """
    When trying to access :
    myproject.com/media/uploads/passport.png

    If access is authorized, the request will be redirected to
    myproject.com/protected/media/uploads/passport.png

    This special URL will be handle by nginx we the help of X-Accel
    """
    user = request.user

    response = HttpResponse()

    if path.startswith("report"):
        if user.is_authenticated:
            report = TaskReport.objects.filter(created_by=user, file_type__isnull=False,
                                                   file__isnull=False,file__icontains=path).exclude(file_type="html").first()
            if report:
                del response['Content-Type']
                response['X-Accel-Redirect'] = '/protected/' + path
                return response
            else:
                return HttpResponseForbidden('Not authorized to access this media.')

        else:
            return HttpResponseForbidden('Not authorized to access this media.')

    del response['Content-Type']
    response['X-Accel-Redirect'] = '/protected/' + path
    return response
