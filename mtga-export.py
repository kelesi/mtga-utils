#!/usr/bin/env python
"""Export your card collection from MTG: Arena
    Notes:
        Card Collection - PlayerInventory.GetPlayerCardsV3
        Log File in windows - "%AppData%\\LocalLow\\Wizards Of The Coast\\MTGA\\Player.log"
"""
from __future__ import print_function
import logging
import argparse
import shlex
import sys
import os
from mtga_log import *
from mtga_formats import MtgaFormats, normalize_set
import scryfall

__version__ = "0.4.3"


def print_arrays_with_keys(data, prefix='', separator='|', last_separator='='):
    """Prints array branches on one line separated with a character.

    Args:
        prefix (string): Prefix to use at the begining of the line.
            Defaults to empty string.
        separator (string): Character or string to use as value/key separator.
            Defaults to pipe '|'.

    Examples:
        >>> print_arrays_with_keys({'a': {'bb': {'ccc': 1}}})
        a|bb|ccc=1

        >>> array = {'a': { 'aa': 1, 'bb': 2}, 'b': '3'}
        >>> print_arrays_with_keys(array, 'prefix', ':', '=>')
        prefix:a:aa=>1
        prefix:a:bb=>2
        prefix:b=>3
    """
    if isinstance(data, (dict)):
        if prefix:
            prefix += separator
        for key, value in iteritems(data):
            print_arrays_with_keys(value, prefix + key, separator, last_separator)
        return
    if isinstance(data, (list, tuple)):
        i=0
        for value in data:
            i+=1
            print_arrays_with_keys(value, prefix + '['+str(i)+']', separator, last_separator)
        return

    print(prefix + last_separator + str(data))


def get_argparse_parser():
    """Setup command line arguments and return parser object.

    Returns:
        argparse.ArgumentParser: Parser object
    """
    parser = argparse.ArgumentParser(description="Parse MTGA log file")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument("-l", "--log_file", help="MTGA/Unity log file [Win: %%AppData%%\\LocalLow\\Wizards Of The Coast\\MTGA\\Player.log]", nargs=1)
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
    parser.add_argument("-ds", "--deckstats", help="Export in deckstats format", action="store_true")
    parser.add_argument("-ct", "--completiontracker", help="Export set completion", action="store_true")
    parser.add_argument("-i",  "--inventory", help="Print inventory", action="store_true")
    parser.add_argument("-ij", "--inventoryjson", help="Print inventory as json", action="store_true")
    parser.add_argument("--decks", help="Print user decks", action="store_true")
    parser.add_argument("--decksjson", help="Print user decks as json", action="store_true")
    parser.add_argument("--decknames", help="Print names of user's decks", action="store_true")
    parser.add_argument("--deckinfo", metavar="DECK_NAME", help="Print info about specific deck", nargs=1)
    parser.add_argument("--deckexport", metavar="DECK_NAME", help="Export specific deck in Arena format", nargs=1)
    parser.add_argument("-f",  "--file", help="Store export to file", nargs=1)
    parser.add_argument("--log", help="Log level", nargs="?", default="INFO")
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


def setup_logging(args):
    """Setup logging for this script"""
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log)
    logging.basicConfig(level=numeric_level)


def get_keyword_data(args, mlog):
    """Get json data for specific keyword as dict"""
    keyword = args.keyword[0]
    try:
        data = mlog.get_last_json_block('<== ' + keyword)
    except MtgaLogParsingError as error:
        print('Error: Could not parse json data: ', error)
        logging.debug("Got:")
        logging.debug(mlog.get_last_keyword_block('<== ' + keyword))
        return {}
    return data


def get_collection(args, mlog):
    """Get collection and print messages"""
    from mtga.models.card import Card

    try:
        for (mtga_id, card, count) in mlog.get_collection():
            if isinstance(card, MtgaUnknownCard):
                print('Info: Unknown card in collection: %s (Will fetch it from Scryfall)' % card)
            elif isinstance(card, scryfall.ScryfallError):
                print('Warning: Could not fetch unknown card from scryfall: %s' % card)
            elif not isinstance(card, Card):
                print('Warning: Unexpected card format [id=%s, card=%s]' % (mtga_id, str(card)))
            else:
                yield [card, count]
    except MtgaLogParsingError as error:
        print('Error: Could not parse json data: ', error)
        logging.debug("Got:")
        logging.debug(mlog.get_last_keyword_block('<== ' + MTGA_COLLECTION_KEYWORD))


def main(args_string=None):
    output = []

    args = parse_arguments(args_string)
    setup_logging(args)

    log_file = None

    if args.log_file:
        log_file = args.log_file[0]
        if not os.path.isfile(log_file):
            print("Log file does not exist, provide proper logfile [%s]" % log_file)
            sys.exit(1)

    mlog = MtgaLog(log_file)

    if not mlog.detailed_logs():
        print('DETAILED LOGS (PLUGIN SUPPORT) ARE DISABLED.')
        print('Please Log into Arena and go to "Adjust Options":')
        print('    - click on "View Account"')
        print('    - check the “Detailed Logs (Plugin Support)” button')
        print('    - restart the game')
        return 1

    if args.collids:
        args.keyword = MTGA_COLLECTION_KEYWORD

    if args.keyword:
        print(get_keyword_data(args, mlog))

    if args.collection:
        for card, count in get_collection(args, mlog):
            logging.debug(str(card))
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
        mformats = MtgaFormats(mtga_log=mlog)

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

    if args.inventory:
        inventory_dict = mlog.get_inventory().inventory()
        print_arrays_with_keys(inventory_dict, '', ':')

    if args.inventoryjson:
        inventory_dict = mlog.get_inventory().inventory()
        output.append(json.dumps(inventory_dict, indent=2))

    if args.decks or args.decksjson:
        decks = {}
        for deck in mlog.get_deck_lists():
            decks[deck.name] = deck.deck()
        if args.decksjson:
            output.append(str(decks))
        if args.decks:
            print_arrays_with_keys(decks, '', ':')

    if args.decknames:
        for deck in mlog.get_deck_lists():
            output.append(deck.name)

    if args.deckinfo:
        for deck in mlog.get_deck_lists():
            if deck.name == args.deckinfo[0]:
                print_arrays_with_keys(deck.deck(), '', ':')

    if args.deckexport:
        for deck in mlog.get_deck_lists():
            if deck.name == args.deckexport[0]:
                output.append(deck.export_arena())

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
