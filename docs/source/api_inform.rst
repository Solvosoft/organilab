API
=====

There are 5 APIs implemented for data consulting for the following data models:
 - Objects (objectView)
 - Inform (informView)
 - Laboratory by organization (laboratoryOrgView)
 - Laboratory by user (laboratoryView)
 - Incident Report (incidentReportView)
 - Users in organization (objectView)

The data itself can be accessed using the ``derb/organization_id/api/modelToConsult``.

Form.io Configuration
=======================

If the API is used in a select from ``Form.io``, follow these steps:
 - Access the ``Data tab``.
 - Change the ``Data Source Type`` to ``URL``.
 - Change the ``Data Source URL`` to ``derb/organization_id/api/modelToConsult``.
 - For consistency, disable the ``Lazy Load Data`` option, for the data to load correctly on edit.
 - Change the ``Storage Type`` to ``Number``.
 - Change the ``ID Path`` to ``item.key``.
 - Change the ``Value Property`` to ``key``.
 - Change the ``Item Template`` to the following:
    .. code:: HTML

        <option value={{item.key}}>{{item.value}}</option>

 - Save the component.

Documentation from every view class
====================================
.. automodule:: derb.api.views
    :members:

.. toctree::
   :maxdepth: 2
   :caption: Contents: