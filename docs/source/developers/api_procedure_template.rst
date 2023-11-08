Administrative Procedures API
*******************************

ProcedureAPI is a generic view that filter the information about procedure templates


ProcedureAPI functionality
===============================

This Model ViewSet filters the procedures template for the organization and validate if the user relate to the
organization is allow the table show all the procedures templates.
Also the last datatable column has to ``<i></i>`` elements:

    - The first icon is to view the procedure template and the steps to do the procedure.
    - The second icon is to add procedure step this action is relation to the model **ProcedureStep**.
    - The third icon is to update the procedure template title and description.
    - The last icon is to remove or delete procedure templates.

These functionality is related to **Procedure** model.
