Autoinvent-Schema
=================

Python implementation of the Autoinvent Schema, the metadata that
Conveyor and Magql use to describe data models.

The schema describes the models making up an application, and the fields
belonging to each model. Each model and field has properties describing
where and how it should be queried, displayed, or interacted with.

There are two layers to the schema:

-   The data layer is the JSON-serializable data that can be sent from
    one program and loaded by another. This contains all the static
    values for the schema.
-   The functional layer can return dynamic values based on the static
    data and the current state of the application. This allows for
    complex custom behavior.

Typically, the data layer will be generated automatically with another
library. Then, the project will override specific values and methods to
describe the behavior they want that couldn't be automatically detected.
For example, Autoinvent-Schema-SQLAlchemy will introspect SQLAlchemy
models to create schema models and fields describing SQL tables and
columns.

.. toctree::
    :maxdepth: 2

    schema

.. toctree::
    :maxdepth: 2

    license
    changes
