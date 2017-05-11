Test the interaction between psycopg and decoding plugin
========================================================

This repository contains material to test a problem I've found with psycopg2
2.7.1 and logical decoding: if the transaction is transmitted in a single
message the stream position is not set correctly and the last transaction is
repeated when the stream is restarted.

This repos contain a test script to receive a logical stream using psycopg and
an hacked-up version of the PostgreSQL `test_decoding`_ plugin with added
options ``skip-begin``, ``skip-commit``, ``skip-change`` to play with the
message length.

.. _test_decoding: https://www.postgresql.org/docs/9.4/static/test-decoding.html


Usage
-----

- Compile and install the decoding plugin. It will be called `test_decoding2`::

    make
    sudo make install

- Run the script in normal mode (use ``--create-slot`` only once)::

    $ python receive.py --plugin test_decoding2 --create-slot
    Starting streaming, press Control-C to end...

- In a separate shell run some database command::

    =# create table t (id serial primary key);
    CREATE TABLE
    =# insert into t default values;
    INSERT 0 1

- Verify that the data is received ok::

    size: 11, data_start: 35E0BC60, wal_end: 35E0BC60
    BEGIN 60604

    size: 12, data_start: 35E30678, wal_end: 35E30678
    COMMIT 60604

    size: 11, data_start: 35E306B0, wal_end: 35E306B0
    BEGIN 60605

    size: 37, data_start: 35E307B0, wal_end: 35E307B0
    table public.t: INSERT: id[integer]:1

    size: 12, data_start: 35E308B0, wal_end: 35E308B0
    COMMIT 60605

- Verify that stopping and restarting the script will not play the messages
  again::

    ^C $
    $ python receive.py --plugin test_decoding2
    Starting streaming, press Control-C to end...

  ... no output until new db commands::

    =# insert into t default values;
    INSERT 0 1

  which produces::

    size: 11, data_start: 35E309C0, wal_end: 35E309C0
    BEGIN 60606

    size: 37, data_start: 35E30A80, wal_end: 35E30A80
    table public.t: INSERT: id[integer]:2

    size: 12, data_start: 35E30C18, wal_end: 35E30C18
    COMMIT 60606

- Now restart the script requesting only one message::

    $ python receive.py --plugin test_decoding2 -o skip-begin=1 skip-commit=1
    Starting streaming, press Control-C to end...

    =# insert into t default values;
    INSERT 0 1

  ...produces::

    size: 37, data_start: 35E30DE8, wal_end: 35E30DE8
    table public.t: INSERT: id[integer]:3

- Stop and restart the script: it will emit the last transaction again::

    ^C $
    $ python receive.py --plugin test_decoding2 -o skip-begin=1 skip-commit=1
    Starting streaming, press Control-C to end...
    size: 37, data_start: 35E30DE8, wal_end: 35E30DE8
    table public.t: INSERT: id[integer]:3
