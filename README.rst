django-bootstrap-editor
***********************

*description*

Installation
============

Add 'dform' to your ``settings.INSTALLED_APPS`` field.

The URLs for DForm are split into two files, the first is for the admin pieces, 
the second for form submission.  By default the form submission pieces have no
security or control on them and the correct usage of URLs will result in
creating and/or editing of any survey.  To fine tune what can be accessed you
can either use the permissions hook, or not include the submission URLs and
wrap the given views in your own.  To use the default, include both URL sets
in your ``urls.py`` file:

.. code-block:: python

    urlpatterns += (
        url(r'dform/', include('dform.urls')),                                      
        url(r'dform_admin/', include('dform.admin_urls')), 
    )

See the documentation for more information no using the permission hook or
what views to wrap.

Run:

.. code-block:: bash

    $ manage.py makemigrations
    $ manage.py migrate


Demo Installation
=================

A full django project is included in the repository that is used for testing
and can give you a quick idea what DForm is about.  The project is available
in ``extras/sample_site``

.. code-block:: bash

    $ cd django-dform
    $ pip install -r requirements.txt
    $ cd extras/sample_site
    $ pip install -r requirements.txt
    $ ./resetdb.sh
    $ ./runserver.sh

Docs
====

Docs available at: http://django-dform.readthedocs.org/en/latest/
