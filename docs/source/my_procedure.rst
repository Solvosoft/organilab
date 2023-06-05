====
API
====

There are 2 ModelViewSets implemented for the data management of Procedure Step Comments:

 - ProcedureStepCommentTableView: filters the information shown in the complete_my_procedure view's datatable.
 - ProcedureStepCommentAPI: works as a CRUD for the comments through ``action`` decorators. Every method has a permissions checker for ``user.has_perms`` (depending on the requested action), ``user_is_allowed_on_organization`` and ``organization_can_change_laboratory`` through the ``_check_permission_on_laboratory`` method.

============================================
ProcedureStepCommentTableView functionality
============================================

This Model View Set filters the comments for the selected procedure step; in case that no procedure has been selected,
the table shows all the comments associated to the ``My Procedure`` entity.
The table has a button to add new comments which only allows to add a new comment if there is a selected step; if the isn't
a selected one, an alert is shown asking the user to select a step to proceed.
The last datatable column has to ``<i></i>`` elements, one for comment edition and the other for comment deletion that are
associated to the ``ProcedureStepCommentAPI`` methods. For edition or deletion it's not necessary to select a step before.

=======
MODELS
=======

There are 2 models related to this funcionality:

 - MyProcedure: entity that takes a ``Procedure`` object as its template and groups the users comments for each template's ``Procedure Step``.
 - CommentProcedureStep: has the information of its creator, the creation date, the referenced procedure step, the grouping ``My procedure`` and the comment.
