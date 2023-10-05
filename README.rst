===============
Archive2rocrate
===============

Library and command-line tool to convert Norstore Archive datasets to ro-crates.

Uses Norstore Archive's basic_search API to fetch datasets in JSON format.

Running
=======

Can be run even without installing, by first downloading the code, then doing oine of:

1. entering the ``src``-directory and executing ``python -m archive2rocrate``
2. adding ``src`` to $PYTHONPATH then executing ``python -m archive2rocrate``

If installed it can be executed with both ``python -m archive2rocrate``
as well as ``archive2rocrate``.

Installation
============

Install with pip: ``pip install archive2rocrate``

Inputting the endpoints
=======================

The actual endpoints are not included with the script. They can be put in
a config-file, format::

    list_endpoint = https://WHATEVER
    dataset_endpoint = https://WHATEVER

The config is searched for in the following files, in prioritized order::

    $PWD/.archive2rocrate.toml
    $HOME/.archive2rocrate.toml
    $XDG_CONFIG_HOME/archive2rocrate.toml
    /usr/local/etc/archive2rocrate.toml
    /etc/archive2rocrate.toml

The config can be overriden by the flags ``--dataset_endpoint`` and
``__list_endpoint``.

Trivia
======

Names of persons are encoded in base 32 to serve as an identifier, since the
Norstore Archive do not use ORCID or similar identification standards.
