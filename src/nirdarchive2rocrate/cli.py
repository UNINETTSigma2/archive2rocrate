import argparse
import json
import sys

from . import name
from .config import get_config
from .convert import generate_jsonld, process_dataset, extract_dois
from .scrape import get_doi_blobs, get_dataset, get_multiple_datasets


__all__ = []


INDENT = 2


def arg_setup():
    parser = argparse.ArgumentParser(
        prog=name,
        description="Fetch and/or convert Norstore Archive datasets to ro-crates",
    )
    parser.add_argument(
        '-i', '--indent',
        action="store_const",
        const=INDENT,
        help="Indent outputted json by two spaces",
    )
    parser.add_argument(
        '-f', '--fail',
        action='store_true',
        help="Dump original dataset on failure",
    )

    subparsers = parser.add_subparsers(
        help='sub-command help',
        dest='command',
    )

    doi = subparsers.add_parser('fetch', help='fetch and convert')
    doi.add_argument('doi', help="Fetch and convert dataset of specific doi")
    doi.add_argument('--dataset_endpoint', help="Use alternative endpoint at URL")

    multi = subparsers.add_parser('multi', help='Fetch and convert multiple datasets')
    multi.add_argument('--dataset_endpoint', help="Use alternative endpoint at URL")
    multi.add_argument('--list_endpoint', help="Use alternative endpoint at URL")
    multi.add_argument('-a', '--after', help="Fetch datasets published AFTER date (YYYY-mm-dd)")
    multi.add_argument('-b', '--before', help="Fetch datasets published BEFORE date (YYYY-mm-dd)")

    convert = subparsers.add_parser('convert', help='convert file')
    convert.add_argument('json', help="Convert one or more datasets in JSON format")
    return parser


def _get_config(args):
    try:
        config = get_config()
    except FileNotFoundError:
        config = Config()
        sys.stderr.write("Config file not found, attempting to continue.\n")
    if args.dataset_endpoint:
        config.DATASET_ENDPOINT = args.dataset_endpoint
    if args.command == 'multi':
        if args.list_endpoint:
            config.LIST_ENDPOINT = args.list_endpoint
        if not config.LIST_ENDPOINT:
            raise ValueError('Missing list_endpoint')
    if not config.DATASET_ENDPOINT:
        raise ValueError('Missing dataset_endpoint')
    return config


def _get_blobs(args):
    blobs = []
    errors = {}
    config = _get_config(args)
    if args.command == 'fetch':
        try:
            blobs = [get_dataset(args.doi, config.DATASET_ENDPOINT)]
        except ValueError as e:
            errors[args.doi] = e
    elif args.command == 'multi':
        doi_blobs = get_doi_blobs(
            config.LIST_ENDPOINT,
            after=args.after,
            before=args.before,
        )
        dois = extract_dois(doi_blobs)
        blobs, errors = get_multiple_datasets(dois, config.DATASET_ENDPOINT)
    elif args.command == 'convert':
        blobs = json.load(args.json)
        if isinstance(blobs, dict):
            blobs = [blobs]
        elif isinstance(blobs, list):
            pass
        else:
            raise ValueError('Wrong format for input')

    return blobs, errors


def main():
    parser = arg_setup()
    args = parser.parse_args()
    if not args.command:
        parser.print_usage()
        sys.exit(1)

    try:
        blobs, errors = _get_blobs(args)
    except ValueError as e:
        sys.stderr.write(e)
        sys.exit(1)

    if errors:
        sys.stderr.write("The following doi(s) could not be fetched:\n")
        for doi, error in errors.items():
            sys.stderr.write(f"\t{doi}: {error}\n")

    if not blobs:
        sys.stderr.write('Nothing to convert\n')
        sys.exit(1)

    crates = []
    for dataset in blobs:
        try:
            crate = generate_jsonld(*process_dataset(dataset))
        except KeyError as e:
            if args.fail:
                sys.stderr.write(json.dumps(blobs, indent=INDENT) + '\n')
                sys.stderr.write(e)
                sys.stderr.write('\n')
        else:
            crates.append(crate)
    sys.stdout.write(json.dumps(crates, indent=args.indent) + '\n')
    sys.exit()
