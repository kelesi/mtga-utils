#!/usr/bin/env python
"""Export your card collection from MTG: Arena
    Notes:
        Card Collection - PlayerInventory.GetPlayerCardsV3
        Log File in windows - "%AppData%\LocalLow\Wizards Of The Coast\MTGA\output_log.txt"
"""
from __future__ import print_function
import argparse
import shlex
import sys
import os
from mtga_log import *
import scryfall


__version__ = "0.2.7"


def get_argparse_parser():
    """Setup command line arguments and return parser object.

    Returns:
        argparse.ArgumentParser: Parser object
    """
    parser = argparse.ArgumentParser(description="Parse MTGA log file")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument("-l", "--log_file", help="MTGA/Unity log file [Win: %%AppData%%\LocalLow\Wizards Of The Coast\MTGA\output_log.txt]", nargs=1)
    parser.add_argument("-k", "--keyword", help="List json under keyword", nargs=1)
    parser.add_argument("--collids", help="List collection ids", action="store_true")
    parser.add_argument("-c", "--collection", help="List collection with card data", action="store_true")
    parser.add_argument(
        "-e", "--export", help="Export collection in custom format", nargs="+",
        choices=[
            'name', 'pretty_name', 'cost', 'sub_types',
            'set', 'set_number', 'card_type', 'mtga_id',
            'count'
        ]
    )
    parser.add_argument("-gf", "--goldfish", help="Export in mtggoldfish format", action="store_true")
    parser.add_argument("-ct", "--completiontracker", help="Export set completion", action="store_true")
    parser.add_argument("-ds", "--deckstats", help="Export in deckstats format", action="store_true")
    parser.add_argument("-f", "--file", help="Store export to file", nargs=1)
    parser.add_argument("--debug", help="Show debug messages", action="store_true")
    return parser


def parse_arguments(args_string=None):
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Arguments object
    """
    parser = get_argparse_parser()

    if args_string is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(shlex.split(args_string))

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)

    return args


def get_keyword_data(args, mlog):
    """Get json data for specific keyword as dict"""
    keyword = args.keyword[0]
    try:
        data = mlog.get_last_json_block('<== ' + keyword)
    except MtgaLogParsingError as error:
        print('Error: Could not parse json data: ', error)
        if args.debug:
            print("Got:")
            print(mlog.get_last_keyword_block('<== ' + keyword))
        return {}
    return data


def get_collection(args, mlog):
    """Get collection and print messages"""
    try:
        for (mtga_id, card, count) in mlog.get_collection():
            if isinstance(card, MtgaUnknownCard):
                print('Info: Unknown card in collection: %s (Will fetch it from Scryfall)' % card)
            elif isinstance(card, scryfall.ScryfallError):
                print('Warning: Could not fetch unknown card from scryfall: %s' % card)
            else:
                yield [card, count]
    except MtgaLogParsingError as error:
        print('Error: Could not parse json data: ', error)
        if args.debug:
            print("Got:")
            print(mlog.get_last_keyword_block('<== ' + MTGA_COLLECTION_KEYWORD))


def normalize_set(set_id, conversion={}):
    """Convert set id readable by goldfish/deckstats"""
    conversion.update({'DAR': 'DOM'})
    return conversion.get(set_id.upper(), set_id.upper())


def main(args_string=None):
    output = []

    args = parse_arguments(args_string)

    log_file = MTGA_WINDOWS_LOG_FILE
    formats_file = MTGA_WINDOWS_FORMATS_FILE

    if args.log_file:
        log_file = args.log_file[0]

    if not os.path.isfile(log_file):
        print("Log file does not exist, provide proper logfile [%s]" % log_file)
        sys.exit(1)

    mlog = MtgaLog(log_file)

    if args.collids:
        args.keyword = MTGA_COLLECTION_KEYWORD

    if args.keyword:
        print(get_keyword_data(args, mlog))

    if args.collection:
        for card, count in get_collection(args, mlog):
            print(card.mtga_id, card, count)

    if args.export:
        output.append(','.join(args.export))
        for card, count in get_collection(args, mlog):
            fields = []
            for key in args.export:
                if key == "count":
                    fields.append(str(count))
                else:
                    fields.append(str(getattr(card, key)))
            output.append(','.join(fields))

    if args.completiontracker:
        sets_progression_output = {}
        mformats = MtgaFormats(formats_file)

        for card, count in get_collection(args, mlog):
            if sets_progression_output.get(card.set, None) is None:
                sets_progression_output[card.set] = {
                    'singlesOwned': 0,
                    'completeSetsOwned': 0,
                    'totalSetCount': mformats.get_set_card_count(card.set)
                }

            sets_progression_output[card.set]['singlesOwned'] += 1

            if int(count) >= 4:
                sets_progression_output[card.set]['completeSetsOwned'] += 1

        output.append(json.dumps(sets_progression_output, indent=2))

    if args.goldfish:
        output.append('Card,Set ID,Set Name,Quantity,Foil')
        for card, count in get_collection(args, mlog):
            card_set = normalize_set(card.set, {'ANA': 'ARENA'})
            output.append('"%s",%s,%s,%s,%s' % (card.pretty_name, card_set, '', count, ''))

    if args.deckstats:
        output.append('card_name,amount,set_code,is_foil,is_pinned')
        for card, count in get_collection(args, mlog):
            card_set = normalize_set(card.set, {'ANA': 'MTGA'})
            output.append('"%s",%s,"%s",%s,%s' % (
                card.pretty_name, count, card_set, 0, 0,
            ))

    if output != []:
        output_str = '\n'.join(output)
        if args.file:
            with open(args.file[0], "w") as out_file:
                out_file.write(output_str)
            print("Exported to file")
        else:
            print(output_str)


if __name__ == "__main__":
    sys.exit(main())
