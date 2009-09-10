#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
A commandline tool for parsing RDF in different formats and serializing the
resulting graph to a chosen format.
"""

import rdflib
from rdflib import plugin
from rdflib.store import Store
from rdflib.graph import Graph
from rdflib.namespace import Namespace, RDF, RDFS, OWL, _XSD_NS
from rdflib.syntax.parsers import Parser
from rdflib.syntax.serializers import Serializer

from rdflib_tools.pathutils import guess_format

import sys
from optparse import OptionParser
import logging


STORE_CONNECTION = ''
STORE_TYPE = 'IOMemory'

DEFAULT_INPUT_FORMAT = 'xml'
DEFAULT_OUTPUT_FORMAT = 'n3'

NS_BINDINGS = {
    'rdf':  RDF,
    'rdfs': RDFS,
    'owl':  OWL,
    'xsd':  _XSD_NS,
    'dc':   "http://purl.org/dc/elements/1.1/",
    'dct':  "http://purl.org/dc/terms/",
    'foaf': "http://xmlns.com/foaf/0.1/",
    'wot':  "http://xmlns.com/wot/0.1/"
}


def parse_and_serialize(input_files, input_format, guess,
        outfile, output_format, ns_bindings,
        store_conn=STORE_CONNECTION, store_type=STORE_TYPE):

    store = plugin.get(store_type, Store)()
    store.open(store_conn)
    graph = Graph(store)

    for prefix, uri in ns_bindings.items():
        graph.namespace_manager.bind(prefix, uri, override=False)

    for fpath in input_files:
        use_format = input_format
        if fpath == '-':
            fpath = sys.stdin
        elif not input_format and guess:
            use_format = guess_format(fpath) or DEFAULT_INPUT_FORMAT
        graph.parse(fpath, format=use_format)

    # TODO: get extra kwargs to serializer (by parsing output_format key)?
    if outfile:
        graph.serialize(destination=outfile, format=output_format, base=None)
    store.rollback()


_get_plugin_names = lambda kind: ", ".join(repr(p.name) for p in plugin.plugins(kind=kind))

def make_option_parser():
    parser_names = _get_plugin_names(Parser)
    serializer_names = _get_plugin_names(Serializer)

    oparser = OptionParser(
            "%prog [-h] [-i INPUT_FORMAT] [-o OUTPUT_FORMAT] [--ns=PFX=NS ...] [-] [FILE ...]",
            description=__doc__.strip() + (
                " Reads file system paths, URLs or from stdin if '-' is supplied."
                " The result is serialized to stdout."),
            version="%prog " + "(using rdflib %s)" % rdflib.__version__)

    oparser.add_option('-i', '--input-format',
            type=str, #default=DEFAULT_INPUT_FORMAT,
            help="Format of the input document(s). One of: %s." % parser_names,
            metavar="INPUT_FORMAT")

    oparser.add_option('-o', '--output-format',
            type=str, default=DEFAULT_OUTPUT_FORMAT,
            help="Format of the final serialized RDF graph. One of: %s." % serializer_names
                + " Default is '%default'.",
            metavar="OUTPUT_FORMAT")

    oparser.add_option('--ns',
            action="append", type=str,
            help="Register a namespace binding (QName prefix to a base URI). "
                    "This can be used more than once.",
            metavar="PREFIX=NAMESPACE")

    oparser.add_option('--no-guess', dest='guess',
            action='store_false', default=True,
            help="Don't guess format based on file suffix.")

    oparser.add_option('--no-out',
            action='store_true', default=False,
            help="Don't output the resulting graph (useful for checking validity of input).")

    oparser.add_option('-w', '--warn',
            action='store_true', default=False,
            help="Output warnings to stderr (by default only critical errors).")

    return oparser


def main():
    oparser = make_option_parser()
    opts, args = oparser.parse_args()
    if len(args) < 1:
        oparser.print_usage()
        oparser.exit()

    if opts.warn:
        loglevel = logging.WARNING
    else:
        loglevel = logging.CRITICAL
    logging.basicConfig(level=loglevel)

    ns_bindings = dict(NS_BINDINGS)
    if opts.ns:
        for ns_kw in opts.ns:
            pfx, uri = ns_kw.split('=')
            ns_bindings[pfx] = uri

    outfile = sys.stdout
    if opts.no_out:
        outfile = None

    parse_and_serialize(args, opts.input_format, opts.guess,
            outfile, opts.output_format, ns_bindings)


if __name__ == "__main__":
    main()

