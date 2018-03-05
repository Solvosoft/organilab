from django.db.models.query_utils import Q
from laboratory.models import Laboratory,OrganizationStructure
from django.shortcuts import redirect, get_object_or_404
from django.core.urlresolvers import reverse
from laboratory.utils import check_lab_perms


# def check_lab_permissions(function=None):
#  
#     def _decorate(view_function, *args, **kwargs):
#         def view_wrapper(request, *args, **kwargs):
#             print ("check_lab_permissions")
#             lab_pk = kwargs.get('lab_pk')
#             if lab_pk is not None:
#                 if not has_perm_in_lab(request.user, get_object_or_404(Laboratory, pk=lab_pk)):
#                     return redirect(reverse('laboratory:permission_denied'))
#             return view_function(request, *args, **kwargs)
#         return view_wrapper
#  
#     if function:
#         return _decorate(view_function=function)
#     return _decorate
 
 
# def user_lab_perms(function=None, perm='search'):
#     def _decorate(view_function, *args, **kwargs):
#         def view_wrapper(request, *args, **kwargs):
#             print ("user_lab_perms")
#             user = request.user
#             lab = get_object_or_404(Laboratory, pk=request.session.get('lab_pk'))
#             if not check_lab_perms(lab, user, perm):
#                 return redirect(reverse('laboratory:permission_denied'))
#             return view_function(request, *args, **kwargs)
#         return view_wrapper
#     if function:
#         return _decorate(view_function=function)
#     return _decorate

def has_perm_in_lab(user, lab):
    if not lab:
        return False
    return user in lab.laboratorists.all() or user in lab.lab_admins.all() 

def check_user_has_perm(user, perm):
   return bool(user.has_perm(perm))

def check_user_has_lab(user,lab):
    if not lab:
        return False
    if user.is_superuser:
            return True
    # Use assigned labs of organization from assigned used 
    organizations_child = OrganizationStructure.os_manager.filter_user(user)

    # user have perm on that organization ?  else Use assigned user with direct relationship
    if not organizations_child:    
        organizations_chil=[]

    labs = Laboratory.objects.filter(Q(laboratorists__pk=user.pk) | Q(principaltechnician__credentials=user.pk) | Q (organization__in=organizations_child) ).distinct().values_list('id', flat=True)
                      
    if lab in labs:
        return True      
    return False    
    
def check_perm_lab(lab_pk,request,perm):
    user = request.user
    lab = None
    if user.is_superuser:
         return True
     
    if lab_pk is not None:
        lab = get_object_or_404(Laboratory, pk=lab_pk)
        
    uperm = check_user_has_perm(user,perm) if perm else False
    user_owner = check_user_has_lab(user,lab) if lab else False
    other_perms = has_perm_in_lab(user,lab) if lab else False
    
    if True in [uperm,user_owner,other_perms]:
            return True
    return False



""" Used to get perms with perm codename """
def user_group_perms(function=None,perm=None):
    def _decorate(view_function, *args, **kwargs):
        def view_wrapper(request, *args, **kwargs):        
            lab_pk = kwargs.get('lab_pk')
            if not check_perm_lab(lab_pk,request,perm):
                     return redirect(reverse('laboratory:permission_denied'))
            return view_function(request, *args, **kwargs)
        return view_wrapper            
    if function:
        return _decorate(view_function=function)
    return _decorate
    
view_user_group_perms = user_group_perms



