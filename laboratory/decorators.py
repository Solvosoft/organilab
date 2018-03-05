from django.db.models.query_utils import Q
from laboratory.models import Laboratory,OrganizationStructure
from django.shortcuts import redirect, get_object_or_404
from django.core.urlresolvers import reverse
from laboratory.utils import check_lab_perms


def check_group_has_perm(group,codename):
    appname, perm = (codename.split("."))
    return group.permissions.filter(codename=perm).exists()

def sum_ancestors_group(user_org,lab_org,perm):     
    lab_ancestors = lab_org.get_ancestors(ascending=True, include_self=True) 
    user_org = user_org.first()  # first have the first org 
    for org in  lab_ancestors:
        if org.level >= user_org.level  :
            group = org.group  if hasattr(org, 'group') else None
            if group :
                return check_group_has_perm(group,perm)
    return False        
def check_user_has_perm(user, perm):
   return bool(user.has_perm(perm))

def check_lab_group_has_perm(user,lab,perm):
            
    # Check org of labs
    lab_org = lab.organization  if hasattr(lab, 'organization') else None
    user_org = OrganizationStructure.os_manager.filter_user(user)
    
    if not user_org:    
        user_org=[]
        
    # if lab have an organizations, compare that perms with perm param
    if lab_org :
        if lab_org in user_org:  # user have some organization
            if sum_ancestors_group(user_org,lab_org,perm): # check ancestor perms
                return True

            
    labs = Laboratory.objects.filter(Q(laboratorists__pk=user.pk) |
                                      Q(principaltechnician__credentials=user.pk) |
                                      Q (organization__in=user_org) 
                                    ).distinct()                                                                               
    if lab in labs:
        print ("User have not organization... checking perms: '%s' to '%s'"%(perm,lab))
        return True      
    return False    

    
        
def check_perms(lab_pk,request,perm):
    user = request.user
    lab = None
    
    # User Admin can allway all
    if user.is_superuser:
        return True
    # redirect to select lab, if no login that send to login form
    if not lab_pk:
        redirect('laboratory:select_lab')
        return True
    else:
        lab = get_object_or_404(Laboratory, pk=lab_pk)
        
    user_perm = check_user_has_perm(user,perm) if perm else False  # check if user has perms to do action
    lab_perms = check_lab_group_has_perm(user,lab,perm) if lab else False  # check if user have perms over lab  
     
    if not False in [user_perm,lab_perms]: # User have perms to all action level
            return True
    return False


""" Used to get perms with perm codename """
def user_group_perms(function=None,perm=None):
    def _decorate(view_function, *args, **kwargs):
        def view_wrapper(request, *args, **kwargs):        
            lab_pk = kwargs.get('lab_pk')
            if not check_perms(lab_pk,request,perm):
                     return redirect(reverse('laboratory:permission_denied'))
            return view_function(request, *args, **kwargs)
        return view_wrapper            
    if function:
        return _decorate(view_function=function)
    return _decorate
    
view_user_group_perms = user_group_perms



