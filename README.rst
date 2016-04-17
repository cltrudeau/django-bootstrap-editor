django-bootstrap-editor
***********************

BSEditor is used to dynamically generate and store Bootstrap compatible CSS
files.  Multiple sheets can be created and controlled using a web interface
based on the Bootstrap template variables.  Once generated several mechanisms
are provided for deploying the files.  Multiple versions of Bootstrap can be
supported at the same time.  The ``sheetpath`` template tag allows easy
inclusion of the generated CSS using the name of the sheet in the database.

Installation
============

Add 'bseditor' to your ``settings.INSTALLED_APPS`` field and include the urls
from the library:

.. code-block:: python

    urlpatterns += (
        url(r'bseditor/', include('bseditor.urls')),
    )

Run:

.. code-block:: bash

    $ manage.py makemigrations
    $ manage.py migrate

To use the included version of Bootstrap, run:

.. code-block:: bash

    $ manage.py defaultversion


Docs
====

Docs available at: http://bseditor.readthedocs.org/en/latest/
