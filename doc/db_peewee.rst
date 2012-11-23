Peewee backend
==============

Flask-Admin provides Peewee ORM backend.

Peewee is a small ORM and some people showed interest in

Features:

 - Peewee 2.x+ support;
 - Paging, sorting, filters, etc;
 - Inline editing of related models;

In order to use peewee integration, you need to install two additional Python packages: `peewee` and `wtf-peewee`.

Known issues:

 - Many-to-Many model relations are not supported: there's no built-in way to express M2M relation in Peewee


For more documentation, check :doc:`api/mod_contrib_peeweemodel` documentation.
