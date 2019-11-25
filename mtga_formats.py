import simplejson as json
from mtga_log import MtgaLogParsingError
import scryfall

def normalize_set(set_id, conversion={}):
    """Convert set id readable by goldfish/deckstats"""
    conversion.update({'DAR': 'DOM'})
    return conversion.get(set_id.upper(), set_id.upper())


class MtgaFormats(object):
    """Process MTGA/Unity formats file"""

    def __init__(self, formats_filename):
        self.formats_filename = formats_filename

    def _get_formats_json(self):
        """Gets the formats json"""
        with open(self.formats_filename) as formats_file:
            return json.load(formats_file)

    def get_format_sets(self, mtg_format):
        """Returns list of current sets in standard format"""
        try:
            json_data = self._get_formats_json()
        except ValueError as exception:
            raise MtgaLogParsingError(exception)

        sets = []
        for item in json_data:
            if item.get("name").lower() == str(mtg_format):
                for mtga_set in item.get("sets"):
                    sets.append(mtga_set)
                    if mtga_set == "DAR":
                        sets.append("DOM")
        return sets

    def get_set_info(self, mtga_set):
        return scryfall.get_set_info(mtga_set)

    def get_set_card_count(self, mtga_set):
        set_info = self.get_set_info(mtga_set)
        return set_info.get('card_count', 0)