====
API
====

SearchLabView is a generic view set with following features:

 - Check user permission on laboratory and organization.
 - Search by laboratory room: It allows to relate and find and specific laboratory room inside a laboratory.
 - Search by furniture: It allows to relate and find and specific furniture inside a laboratory.
 - Search by shelf: It allows to relate and find and specific shelf inside a laboratory.
 - Search by shelf object: It allows to relate and find and specific shelf object inside a laboratory.
 - Search by object It allows to relate and find and coincidences about shelf object name inside a shelf object table.
   The accepted objects just will be used objects by this laboratory its stock.
 - Search by url by get request with following parameters: [labroom, furniture, shelf, shelfobject]. They are not
   required parameters in this view. It just an optional search.

============================================
Search Priority Classification
============================================

 Elements inside laboratory view will be classified by following priority:

 - 1. Object
 - 2. Shelf Object
 - 3. Shelf
 - 4. Furniture
 - 5. Laboratory Room

 Object will have greater priority while laboratory room will have lower priority.