"""Export your card collection from MTG: Arena
    Notes:
        Card Collection - PlayerInventory.GetPlayerCardsV3
        Log File in windows - "%AppData%\LocalLow\Wizards Of The Coast\MTGA\output_log.txt"
"""
from __future__ import print_function
import json
from mtga.set_data import all_mtga_cards
import argparse
import shlex
import sys
import os
from setuptools_scm import get_version

MTGA_COLLECTION_KEYWORD = "PlayerInventory.GetPlayerCardsV3"
MTGA_WINDOWS_LOG_FILE = os.getenv('APPDATA')+"\..\LocalLow\Wizards Of The Coast\MTGA\output_log.txt"

class MtgaLog(object):

    """Read log file into memory and process it"""
    def __init__(self, log_filename):
        self.log_filename = log_filename
        self.exception = None

    def get_last_keyword_block(self, keyword):
        bucket = []
        copy = False
        with open(self.log_filename) as logfile:
            for line in logfile:
                if copy:
                    bucket.append(line)

                if line.find(keyword) > -1:
                    bucket = []
                    copy = True
                elif line.strip() == "}":
                    copy = False
        return bucket

    def get_last_json_block(self, keyword):
        try:
            block = self.get_last_keyword_block(keyword)
            return self.list_to_json(block)
        except ValueError as exception:
            self.exception = exception
            return False

    def list_to_json(self, json_list):
        json_string = ''.join(json_list)
        return json.loads(json_string)




def get_argparse_parser():
    """Setup command line arguments and return parser object.

    Returns:
        argparse.ArgumentParser: Parser object
    """
    parser = argparse.ArgumentParser(description="Parse MTGA log file")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + get_version())
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


def get_keyword_data(mlog, keyword):
    data = mlog.get_last_json_block('<== ' + keyword)
    if data is False:
        print('Error parsing json data: ', mlog.exception)
        # print(mlog.get_last_keyword_block('<== ' + args.keyword[0]))
        return {}
    else:
        return data


def get_collection(mlog):
    collection = get_keyword_data(mlog, MTGA_COLLECTION_KEYWORD)
    for id, count in collection.iteritems():
        #print(id, count)
        card = all_mtga_cards.find_one(id)
        yield [card, count]


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

    if args.keyword:
        print(get_keyword_data(mlog, args.keyword[0]))

    if args.collids:
        print(get_keyword_data(mlog, MTGA_COLLECTION_KEYWORD))

    if args.collection:
        for card, count in get_collection(mlog):
            print(card.mtga_id, card, count)

    if args.export:
        output.append(','.join(args.export))
        for card, count in get_collection(mlog):
            fields = []
            for key in args.export:
                fields.append(str(getattr(card, key)))
            output.append(','.join(fields))

    if args.goldfish:
        output.append('Card,Set ID,Set Name,Quantity,Foil')
        for card, count in get_collection(mlog):
            output.append('"%s",%s,%s,%s' % (card.pretty_name, card.set, '', count))

    if args.deckstats:
        output.append('amount,card_name,is_foil,is_pinned,set_id,set_code')
        for card, count in get_collection(mlog):
            output.append('%d,"%s",%d,%d,%d,"%s"' % (
                count, card.pretty_name, 0, 0, card.set_number, card.set
            ))

    if output is not []:
        output_str = '\n'.join(output)
        if args.file:
            with open(args.file[0], "w") as out_file:
                out_file.write(output_str)
            print("Exported to file")
        else:
            print(output_str)


if __name__ == "__main__":
    sys.exit(main())
