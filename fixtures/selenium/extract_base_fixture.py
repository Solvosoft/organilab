#!/usr/bin/env python3
"""
Extract shared base records from Selenium fixtures into a common base fixture,
and generate delta fixtures containing only the unique records per fixture.

Shared base models (between laboratory_selenium.json and risk_management.json):
- auth.user (pk=1,2,3)
- auth_and_perms.profile (pk=1,2,3)
- auth_and_perms.profilepermission (pk=1,2,3)
- auth_and_perms.rol (pk=1..22)
- laboratory.organizationstructure (pk=1..4)
- laboratory.organizationstructurerelations (pk=1..4)
- laboratory.laboratory (pk=1..3)

Usage:
    cd fixtures/selenium/
    python extract_base_fixture.py
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_MODELS = {
    'auth.user': {1, 2, 3},
    'auth_and_perms.profile': {1, 2, 3},
    'auth_and_perms.profilepermission': {1, 2, 3},
    'auth_and_perms.rol': set(range(1, 23)),
    'laboratory.organizationstructure': {1, 2, 3, 4},
    'laboratory.organizationstructurerelations': {1, 2, 3, 4},
    'laboratory.laboratory': {1, 2, 3},
}


def is_base_record(record):
    model = record['model']
    pk = record['pk']
    return model in BASE_MODELS and pk in BASE_MODELS[model]


def read_fixture(filename):
    path = os.path.join(SCRIPT_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_fixture(filename, data):
    path = os.path.join(SCRIPT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  {filename}: {len(data)} records")


def main():
    lab = read_fixture('laboratory_selenium.json')
    risk = read_fixture('risk_management.json')
    proc = read_fixture('procedure_templates.json')

    # Extract base from laboratory_selenium (canonical source)
    base = [r for r in lab if is_base_record(r)]
    lab_delta = [r for r in lab if not is_base_record(r)]
    risk_delta = [r for r in risk if not is_base_record(r)]

    # For procedure_templates: extract delta + override for profile pk=1
    proc_delta = []
    for r in proc:
        if is_base_record(r):
            # Include records that differ from the base version as overrides
            base_match = next(
                (b for b in base if b['model'] == r['model'] and b['pk'] == r['pk']),
                None
            )
            if base_match and json.dumps(r, sort_keys=True) != json.dumps(base_match, sort_keys=True):
                proc_delta.append(r)
        else:
            proc_delta.append(r)

    print("Generated fixtures:")
    write_fixture('base_selenium.json', base)
    write_fixture('laboratory_delta.json', lab_delta)
    write_fixture('risk_delta.json', risk_delta)
    write_fixture('procedure_delta.json', proc_delta)

    print(f"\nOriginal sizes:")
    print(f"  laboratory_selenium.json: {len(lab)} records")
    print(f"  risk_management.json: {len(risk)} records")
    print(f"  procedure_templates.json: {len(proc)} records")
    print(f"\nBase has {len(base)} shared records")
    print(f"Reduction: {len(base) * 2} fewer duplicate records loaded")


if __name__ == '__main__':
    main()
