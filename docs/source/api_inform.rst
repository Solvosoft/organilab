API
=====

There are 5 APIs implemented for data consulting for the following data models:
 - Objects (objectView)
 - Inform (informView)
 - Laboratory by organization (laboratoryOrgView)
 - Laboratory by user (laboratoryView)
 - Incident Report (incidentReportView)
 - Users in organization/laboratory (orgView)

    .. warning::
        * This API can process a parameter lab, that gets the users inside a specified laboratory if the organization can change it.

The data itself can be accessed using the ``http://host/derb/organization_id/api/modelViewToConsult``.

Form.io Configuration for Basic Select Component
=================================================
If the API is used in a select from ``Form.io``, follow these steps:
 - Access the ``Data tab``.
 - Change the ``Data Source Type`` to ``URL``.
 - Change the ``Data Source URL`` to ``http://host/derb/organization_id/api/modelViewToConsult``.
 - For consistency, disable the ``Lazy Load Data`` option, for the data to load correctly on edit.
 - Change the ``Storage Type`` to ``Number``.
 - Change the ``ID Path`` to ``item.key``.
 - Change the ``Value Property`` to ``key``.
 - Change the ``Item Template`` to the following:

    .. code:: HTML

        <option value={{item.key}}>{{item.value}}</option>

 - Save the component.

Form.io Configuration for Custom Select Component
==================================================
The ``Custom Select`` loads the configured APIs and automatically configures the select component, to load its data.

The APIs configured at this time are:
 - Users in Laboratory/Organization.

    .. warning::
        - Getting the users by laboratory requires inputting a laboratory pk in the ``Laboratory identifier`` field.
        - If the field is blank, the API will get users by organization.


 - Laboratory by Organization.
 - Laboratory by User.
 - Incident Report.
 - Inform.

Component settings:
 - The Value Property must be ``key``.
 - The display, limit of results, multiple and other settings can be changed.
 - Save the component.

New API for Custom Select Component
====================================
.. warning::
    It is recommended to create this API in ``derb`` application.

To create a new API follow these steps:
 - Configure a data serializer to return a key(pk) and value(text).
 - Configure a view that returns a response with the data ({key, value}).
 - Create a route that references this view.
 - Inside the ``CustomSelect.js`` file, in the ``Data`` component setting, create an option in the element with ``data.api`` key, with a descriptive label an the corresponding ``url_name`` as value.

        .. warning::
            * If the API needs extra data, a parameter for example, the corresponding fields must be implemented.
            * In the ``OnChange`` method, see if the url for the preview is being extracted correctly, if not, then implement the necessary extraction method.
            * If the data isn't showing in the preview doesn't mean that the ``url_name`` is wrong, test the functionality inside an inform instead.

 - If the url has any other parameter that isn't organization, the ``get_components_url`` method that construct the url, must be modified.
 - This method can be found in the ``informs.py`` file inside the ``laboratory`` app.


Documentation from every view class
====================================
.. automodule:: derb.api.views
    :members:

.. toctree::
   :maxdepth: 2
   :caption: Contents:
