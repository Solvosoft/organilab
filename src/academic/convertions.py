"""convert centimeter to other units"""

def convert_meters(amount,unit):
    result = amount
    if unit =='Milímetros':
        result = amount/10**3
    elif unit == 'Centímetros':
        result = amount/10**2
    return result

def convert_milimeter(amount,unit):
    result = amount

    if unit == 'Centímetros':
        result = amount*10**1

    elif unit =='Metros':
        result = amount*10**3

    return result


def convert_centimeter(amount, unit):
    result = amount

    if unit == 'Milímetros':
        result = amount / 10 ** 1

    elif unit == 'Metros':
        result = amount / 10 ** 2

    return result

def convert_grams(amount, unit):
    result = amount
    if unit =='Milígramos':
        result = amount/10**3
    elif unit == 'Kilogramos':
        result = amount*10**3

    return result


def convert_kilogram(amount, unit):
    result = amount
    if unit =='Milígramos':
        result = amount*10**6
    elif unit == 'Gramos':
        result = amount*10**3

    return result


def convert_miligram(amount, unit):
    result = amount
    if unit =='Gramos':
        result = amount/10**3
    elif unit == 'Kilogramos':
        result = amount/10**6

    return result


def convert_lt(amount,unit):
    result = amount

    if unit == 'Mililitros':
        result = amount/10**6

    return result


def convert_mililiter(amount, unit):
    result = amount
    if unit == 'Litros':
        result = amount*10**6

    return result


def convertion(amount, unit_obj, unit_step_obj):
    result = amount

    if unit_obj =='Metros':
        result = convert_meters(amount,unit_step_obj)
    elif unit_obj =='Milímetros':
        result = convert_milimeter(amount, unit_step_obj)
    elif unit_obj == 'Centímetros':
        result = convert_centimeter(amount, unit_step_obj)
    elif unit_obj == 'Milígramos':
        result = convert_miligram(amount, unit_step_obj)
    elif unit_obj == 'Kilogramos':
        result = convert_kilogram(amount, unit_step_obj)
    elif unit_obj == 'Gramos':
        result = convert_grams(amount, unit_step_obj)
    elif unit_obj == 'Milílitros':
        result = convert_mililiter(amount, unit_step_obj)
    elif unit_obj =='Litros':
        result = convert_lt(amount, unit_step_obj)

    return result