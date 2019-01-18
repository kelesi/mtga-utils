"""Export your card collection from MTG: Arena
    Notes:
        Card Collection - PlayerInventory.GetPlayerCardsV3
        Log File in windows - "%AppData%\LocalLow\Wizards Of The Coast\MTGA\output_log.txt"
"""
from __future__ import print_function
from future.utils import iteritems
import json
from mtga.set_data import all_mtga_cards
import argparse
import shlex
import sys
import os
import scryfall


__version__ = "0.2.2"
MTGA_COLLECTION_KEYWORD = "PlayerInventory.GetPlayerCardsV3"
MTGA_WINDOWS_LOG_FILE = os.getenv('APPDATA')+"\..\LocalLow\Wizards Of The Coast\MTGA\output_log.txt"

class MtgaLogParsingError(ValueError):
    pass

class MtgaUnknownCard(ValueError):
    pass

class MtgaLog(object):
    """Process MTGA/Unity log file"""

    def __init__(self, log_filename):
        self.log_filename = log_filename

    def get_last_keyword_block(self, keyword):
        """Find json block for specific keyword (last in the file)
        Args:
            keyword (str): Keyword to search for in the log file
        Returns: list
        """
        bucket = []
        copy = False
        levels = 0
        with open(self.log_filename) as logfile:
            for line in logfile:
                if copy:
                    bucket.append(line)

                if line.find(keyword) > -1:
                    bucket = []
                    copy = True

                levels += line.count('{')
                levels -= line.count('}')

                if line.count('}') > 0 and levels == 0:
                    copy = False
        return bucket

    def get_last_json_block(self, keyword):
        """Get the block as dict"""
        try:
            block = self.get_last_keyword_block(keyword)
            return self._list_to_json(block)
        except ValueError as exception:
            raise MtgaLogParsingError(exception)
            #return False

    def _list_to_json(self, json_list):
        json_string = ''.join(json_list)
        return json.loads(json_string)

    def get_collection(self, fallback=True):
        collection = self.get_last_json_block('<== ' + MTGA_COLLECTION_KEYWORD)
        for (mtga_id, count) in iteritems(collection):
            try:
                card = all_mtga_cards.find_one(mtga_id)
                yield [mtga_id, card, count]
            except ValueError as exception:
                yield [mtga_id, MtgaUnknownCard(exception), 0]
                #Card not found, try to get it from scryfall
                if fallback:
                    try:
                        card = scryfall.get_mtga_card(mtga_id)
                        yield [mtga_id, card, count]
                    except Exception as scryfall_error:
                        yield [mtga_id, scryfall.ScryfallError(scryfall_error), 0]


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
            'set', 'set_number', 'card_type', 'mtga_id'
        ]
    )
    parser.add_argument("-gf", "--goldfish", help="Export in mtggoldfish format", action="store_true")
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
    keyword = args.keyword[0]
    try:
        data = mlog.get_last_json_block('<== ' + keyword)
    except MtgaLogParsingError as error:
        print('Error parsing json data: ', error)
        if args.debug:
            print("Got:")
            print(mlog.get_last_keyword_block('<== ' + keyword))
        return {}
    return data


def get_collection(args, mlog):
    try:
        for (mtga_id, card, count) in mlog.get_collection():
            if isinstance(card, MtgaUnknownCard):
                print('Warning: Unknown card in collection: %s (Trying to fetch it from Scryfall)' % card)
            elif isinstance(card, scryfall.ScryfallError):
                print('Warning: Could not fetch unknown card from scryfall: %s' % card)
            else:
                yield [card, count]
    except MtgaLogParsingError as error:
        print('Error parsing json data: ', error)
        if args.debug:
            print("Got:")
            print(mlog.get_last_keyword_block('<== ' + MTGA_COLLECTION_KEYWORD))



def main(args_string=None):
    output = []

    args = parse_arguments(args_string)

    log_file = MTGA_WINDOWS_LOG_FILE
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
                fields.append(str(getattr(card, key)))
            output.append(','.join(fields))

    if args.goldfish:
        output.append('Card,Set ID,Set Name,Quantity,Foil')
        for card, count in get_collection(args, mlog):
            card_set = card.set
            if card_set == 'ANA':
                card_set = 'ARENA'
            output.append('"%s",%s,%s,%s' % (card.pretty_name, card_set, '', count))

    if args.deckstats:
        output.append('card_name,amount,set_code,is_foil,is_pinned')
        for card, count in get_collection(args, mlog):
            card_set = card.set
            if card_set == 'ANA':
                card_set = 'MTGA'
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
