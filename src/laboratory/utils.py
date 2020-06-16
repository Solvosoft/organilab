
from django.db.models.query_utils import Q
from laboratory.models import Laboratory,OrganizationStructure
 


def check_group_has_perm(group,codename):
    if codename:
        _, perm = (codename.split("."))
        return group.permissions.filter(codename=perm).exists()
    return False

def sum_ancestors_group(user_org,lab_org,perm):        
    lab_parant = lab_org.get_ancestors(ascending=True, include_self=True) 
    user_org = user_org.first()  # first have the first org 
    for org in  lab_parant:
        if org.level >= user_org.level  :
            group = org.group  if hasattr(org, 'group') else None
            if group :                
                if check_group_has_perm(group,perm):
                    return True
    return False        
def check_user_has_perm(user, perm):
    return bool(user.has_perm(perm))


def get_user_laboratories(user, q=None):
    user_org = OrganizationStructure.os_manager.filter_user(user) 
    return filter_laboratorist_profile_student(user, user_org, q)


def filter_laboratorist_profile_student(user,user_org, q=None):
    queryset = Laboratory.objects.filter(Q(profile__user=user.pk) |
                                     Q(organization__in=user_org)  ).distinct()
    if q is not None:
        queryset = queryset.filter(name__icontains=q)
    return queryset


def filter_laboratorist_profile(user, user_org=None):
    if user_org is None:
        user_org = OrganizationStructure.os_manager.filter_user(user)
    return Laboratory.objects.filter( Q(profile__user=user.pk) |
                                      Q (organization__in=user_org) 
                                    ).distinct()

def check_lab_group_has_perm(user,lab,perm,callback_filter=filter_laboratorist_profile):
    if not user or not lab:
        return False
    
    # django admins        
    if user.is_superuser:
        return True;

    if not user.is_authenticated:
        return False 

    # Check org of labs
    lab_org = lab.organization  if hasattr(lab, 'organization') else None
    user_org = OrganizationStructure.os_manager.filter_user(user) 
    
    if not user_org:    
        user_org=[]   
        
    # if lab have an organizations, compare that perms with perm param
    if lab_org  and lab_org in  user_org:  # user have some organization
        if sum_ancestors_group(user_org,lab_org,perm): # check ancestor perms
                return True


    user_perm = check_user_has_perm(user,perm) if perm else False  # check if user has perms to do action
    labs = callback_filter(user,user_org)                                                                          

    if not False in [user_perm,lab in labs]: # User have perms to all action level
            return True
    return False    

    
check_lab_perms = check_lab_group_has_perm




def get_cas(object, default=None):
    result = default
    if hasattr(object, 'sustancecharacteristics') and object.sustancecharacteristics:
        result = object.sustancecharacteristics.cas_id_number
    return result


def get_imdg(object, default=None):
    result = default
    if hasattr(object, 'sustancecharacteristics') and object.sustancecharacteristics:
        result = object.sustancecharacteristics.imdg
    return result

def get_molecular_formula(object, default=None):
    result = default
    if hasattr(object, 'sustancecharacteristics') and object.sustancecharacteristics:
        result = object.sustancecharacteristics.molecular_formula
    return result
