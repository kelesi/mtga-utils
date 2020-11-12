from __future__ import print_function
from future.utils import iteritems
import os
import simplejson as json
import scryfall
import re
import logging


MTGA_COLLECTION_KEYWORD = "PlayerInventory.GetPlayerCardsV3"
MTGA_DECK_LISTS_KEYWORD = "Deck.GetDeckListsV3"
MTGA_INVENTORY_KEYWORD = "PlayerInventory.GetPlayerInventory"
MTGA_PRECON_DECK_LISTS_KEYWORD = "Deck.GetPreconDecksV3"
MTGA_LOG_FILENAME = "Player.log"


def _mtga_file_path(filename):
    """Get the full path to the specified MTGA file"""
    appdata = os.getenv("APPDATA")

    # If we don't have APPDATA, assume we're in the user's home directory
    base = [os.path.dirname(appdata)] if appdata else ["AppData"]
    components = base + ["LocalLow", "Wizards Of The Coast", "MTGA", filename]
    return os.path.join(*components)


def get_mtga_file_path(filename):
    filepath = _mtga_file_path(filename)
    if not os.path.isfile(filepath):
        raise FileNotFoundError('Could not find file %s' % filepath)
    return filepath


def find_one_mtga_card(mtga_id):
    from mtga.set_data import all_mtga_cards
    return all_mtga_cards.find_one(mtga_id)


class MtgaLogParsingError(ValueError):
    """Exception raised when parsing json data fails"""
    pass


class MtgaUnknownCard(ValueError):
    """Exception when card is not found in python-mtga package"""
    pass


class MtgaLog(object):
    """Process MTGA/Unity log file"""

    def __init__(self, log_filename=None):
        self.log_filename = get_mtga_file_path(MTGA_LOG_FILENAME) if log_filename is None else log_filename
        logging.debug("MtgaLog: %s" % self.log_filename)
        self.fallback = True

    def detailed_logs(self):
        """Are detailed logs enabled"""
        with open(self.log_filename) as logfile:
            head = ''.join([next(logfile) for _ in range(100)])

        if re.search(r"DETAILED LOGS: ENABLED", head) is not None:
            return True
        return False

    def scryfall_fallback(self, fallback=True):
        """Enable/disable fallback to Scryfall"""
        self.fallback = fallback

    def get_last_keyword_block(self, keyword):
        """Find json block for specific keyword (last in the file)
        Args:
            keyword (str): Keyword to search for in the log file
        Returns: list
        """
        bucket = []
        copy = False
        dict_levels = 0
        list_levels = 0

        with open(self.log_filename) as logfile:
            for line in logfile:
                if re.search(r"%s\b" % re.escape(keyword), line):
                    bucket, dict_levels, list_levels = [], 0, 0

                    if line.count('{') > 0 or line.count('[') > 0:
                        line = re.sub(r'.*' + re.escape(keyword), '', line)
                    else:
                        line = ""
                    copy = True

                if copy and line:
                    bucket.append(line)
                    dict_levels += line.count('{') - line.count('}')
                    list_levels += line.count('[') - line.count(']')

                if line.count('}') > 0 and dict_levels == 0 and list_levels == 0:
                    copy = False
                if line.count(']') > 0 and list_levels == 0 and dict_levels == 0:
                    copy = False
        return bucket

    def get_last_json_block(self, keyword):
        """Get the block as dict"""
        try:
            block = self.get_last_keyword_block(keyword)
            return self._list_to_json(block)
        except ValueError as exception:
            raise MtgaLogParsingError(exception)
            # return False

    def _list_to_json(self, json_list):
        json_string = ''.join(json_list)
        return json.loads(json_string)

    def _fetch_card_from_scryfall(self, mtga_id):
        if not self.fallback:
            return None
        try:
            card = scryfall.get_mtga_card(mtga_id)
        except Exception as scryfall_error:
            card = scryfall.ScryfallError(scryfall_error)
        return card

    def lookup_cards(self, list_of_pairs):
        for (mtga_id, count) in list_of_pairs:
            try:
                card = find_one_mtga_card(mtga_id)
            except ValueError as exception:
                yield [mtga_id, MtgaUnknownCard(exception), count]
                # Card not found, try to get it from scryfall
                card = self._fetch_card_from_scryfall(mtga_id)

            if card is not None:
                yield [mtga_id, card, count]

    def lookup_card(self, mtga_id):
        try:
            return find_one_mtga_card(mtga_id)
        except ValueError:
            return self._fetch_card_from_scryfall(mtga_id)

    def get_collection(self):
        """Generator for MTGA collection"""
        collection = self.get_last_json_block('<== ' + MTGA_COLLECTION_KEYWORD)
        collection = collection.get('payload', collection)
        return self.lookup_cards(iteritems(collection))

    def get_inventory(self):
        """Convenience function to get the player's inventory"""
        inventory_dict = self.get_last_json_block('<== ' + MTGA_INVENTORY_KEYWORD)
        inventory_dict = inventory_dict.get('payload', inventory_dict)
        return MtgaInventory(inventory_dict)

    def get_deck_lists(self):
        """Get all deck lists"""
        deck_lists_json = self.get_last_json_block('<== ' + MTGA_DECK_LISTS_KEYWORD)
        deck_lists_json = deck_lists_json.get('payload', deck_lists_json)
        return [MtgaDeckList(j, self) for j in deck_lists_json]

    def get_preconstructed_deck_lists(self):
        """Get all preconstructed deck lists"""
        deck_lists_json = self.get_last_json_block('<== ' + MTGA_PRECON_DECK_LISTS_KEYWORD)
        deck_lists_json = deck_lists_json.get('payload', deck_lists_json)
        return [MtgaDeckList(j, self) for j in deck_lists_json]


class MtgaInventory(object):
    """Wrapper for the player's inventory"""

    def __init__(self, inventory_dict):
        self.inventory_dict = inventory_dict

    @property
    def gems(self):
        return self.inventory_dict['gems']

    @property
    def gold(self):
        return self.inventory_dict['gold']

    @property
    def tokens(self):
        return {
            'Draft': self.inventory_dict['draftTokens'],
            'Sealed': self.inventory_dict['sealedTokens']
        }

    @property
    def vault_progress(self):
        return self.inventory_dict['vaultProgress']

    @property
    def wildcards(self):
        return {
            'Common': self.inventory_dict['wcCommon'],
            'Uncommon': self.inventory_dict['wcUncommon'],
            'Rare': self.inventory_dict['wcRare'],
            'Mythic Rare': self.inventory_dict['wcMythic']
        }

    @property
    def starter_decks(self):
        return self.inventory_dict['starterDecks']

    def __str__(self):
        """String representation of the inventory"""
        return str(self.inventory())

    def inventory_raw(self):
        return self.inventory_dict

    def inventory(self):
        """Dictionary representation of the inventory"""
        return {
            'Gems': self.gems,
            'Gold': self.gold,
            'Tokens': self.tokens,
            'VaultProgress': self.vault_progress,
            'Wildcards': self.wildcards
        }


class MtgaDeckList(object):
    """Wrapper for a deck list"""

    def __init__(self, deck_list_json, card_lookup):
        self.deck_list_json = deck_list_json

        maindeck_pairs = zip(*[iter(self.deck_list_json['mainDeck'])]*2)
        self.maindeck = card_lookup.lookup_cards(maindeck_pairs)

        sideboard_pairs = zip(*[iter(self.deck_list_json['sideboard'])]*2)
        self.sideboard = card_lookup.lookup_cards(sideboard_pairs)

        self.deckbox_image = card_lookup.lookup_card(self.deck_list_json['deckTileId'])

    @property
    def deck_id(self):
        return self.deck_list_json['id']

    @property
    def name(self):
        return self.deck_list_json['name']

    @property
    def format(self):
        return self.deck_list_json['format']

    def deck(self):
        return {
            'id': self.deck_id,
            'name': self.name,
            'format': self.format,
            'maindeck': list(self.maindeck),
            'sideboard': list(self.sideboard)
        }

    def export_arena(self):
        export = ["Deck"]
        for [mtga_id, card, count] in self.maindeck:
            export.append("{} {} ({}) {}".format(count, card.pretty_name, card.set, card.set_number))
        export.append("")

        export.append("Sideboard")
        for [mtga_id, card, count] in self.sideboard:
            export.append("{} {} ({}) {}".format(count, card.pretty_name, card.set, card.set_number))

        return '\n'.join(export)

    def __repr__(self):
        return self.deck()

    def __str__(self):
        """String representation of the inventory"""
        return str(self.deck())
