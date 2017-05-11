#!/usr/bin/env python
"""Test receiving logical replication messages
"""

from __future__ import print_function
import sys
import psycopg2
import psycopg2.extras


def main():
    opt = parse_cmdline()

    conn = psycopg2.connect(
        opt.dsn,
        connection_factory=psycopg2.extras.LogicalReplicationConnection)
    cur = conn.cursor()

    if opt.create_slot:
        cur.create_replication_slot(opt.slot, output_plugin=opt.plugin)

    opts = dict(o.split('=', 1) for o in opt.options)

    cur.start_replication(slot_name=opt.slot, options=opts)

    def consumer(msg):
        notices = msg.cursor.connection.notices
        if notices:
            for n in notices:
                print(n.rstrip())
            del notices[:]

        print("size: %s, data_start: %X, wal_end: %X" % (
            msg.data_size, msg.data_start, msg.wal_end))
        print(msg.payload)
        print()
        msg.cursor.send_feedback(flush_lsn=msg.data_start)

    print("Starting streaming, press Control-C to end...", file=sys.stderr)
    try:
        cur.consume_stream(consumer)
    except KeyboardInterrupt:
        cur.close()
        conn.close()

    if opt.drop_slot:
        conn = psycopg2.connect(
            opt.dsn,
            connection_factory=psycopg2.extras.LogicalReplicationConnection)
        cur = conn.cursor()
        cur.drop_replication_slot(opt.slot)
        cur.close()
        conn.close()


def parse_cmdline():
    from argparse import ArgumentParser
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        '--dsn', default='', help="database connection string")
    parser.add_argument(
        '--plugin', default='test_decoding',
        help="name of the decoding plugin to use [default: %(default)s]")
    parser.add_argument(
        '--slot',
        help="some of the slot to use [default: PLUGIN]")
    parser.add_argument(
        '--create-slot', action="store_true",
        help="create the slot at the beginnig of the script")
    parser.add_argument(
        '--drop-slot', action="store_true",
        help="drop the slot at the end of the script")
    parser.add_argument(
        '--option', '-o', dest='options', metavar="NAME=VALUE", nargs='*',
        default=[], help="option to pass to the decoding plugin")

    opt = parser.parse_args()
    if not opt.slot:
        opt.slot = opt.plugin

    return opt

if __name__ == '__main__':
    sys.exit(main())
