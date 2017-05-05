

def check_lab_perms(lab, user, perm):
    admin = lab.lab_admins.filter(username=user.username).exists()
    if perm == 'admin':
        return admin
    elif perm == 'search':
        laborits=lab.laboratorists.filter(username=user.username).exists()
        students = lab.students.filter(username=user.username).exists()
        return admin or laborits or students
    elif perm == 'report':
        return admin  # FIXME: tratar esto mejor
    
    return False