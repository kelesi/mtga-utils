from __future__ import print_function
from future.utils import iteritems

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from parameterized import parameterized
import scryfall
from mtga_log import *



class Test_MtgaLog(unittest.TestCase):

    def setUp(self):
        self.MTGA_LOG =  os.path.join( os.path.dirname(os.path.realpath(__file__)), 'test_mtga_output_log.txt')
        self.mlog = MtgaLog(self.MTGA_LOG)

    def test_get_last_json_block(self):
        result = self.mlog.get_last_json_block('<== TestKey')
        self.assertEqual(
            result.get('test1').get('test11'), '4'
        )
        self.assertEqual(
            result.get('67688').get('test22').get('x').get('a')
            , '1'
        )

    def test_get_last_json_block_whole_words(self):
        result = self.mlog.get_last_json_block('<== KeywordOne')
        self.assertEqual(result.get('id'), 1)
        self.assertEqual(result.get('payload').get('value'), 1)

    def test_get_last_json_block_with_array(self):
        result = self.mlog.get_last_json_block('<== TestArray')
        self.assertEqual(
            result[0].get('key'), 'value'
        )

    def test_get_last_json_block2(self):
        result = self.mlog.get_last_json_block('blah')
        self.assertEqual(result.get('foo'), 'bar')

    def test_get_last_json_block_new_format(self):
        result = self.mlog.get_last_json_block('<== NewFormat')
        self.assertEqual(
            result.get('payload').get('68286'), 1
        )

    def test_get_last_json_block_new_format_array(self):
        result = self.mlog.get_last_json_block('<== NewArrayFormat')
        self.assertEqual(
            result.get('payload')[0].get('key'), 'value'
        )

    @parameterized.expand([
        ["67682", "3"],
        ["123",   "4"],
        ["67688", "4"],
        ["68369", "1"],
        ["64037", "2"],
        ["123456", None]
    ])
    def test_get_last_json_block_last(self, mtga_id, expected_count):
        result = self.mlog.get_last_json_block('<== PlayerInventory.GetPlayerCardsV3')
        self.assertEqual(result.get(mtga_id), expected_count)

    def test_get_last_json_block_invalid(self):
        with self.assertRaises(MtgaLogParsingError):
            result = self.mlog.get_last_json_block('invalid')

    def test_get_last_json_block_notpresent(self):
        with self.assertRaises(MtgaLogParsingError):
            result = self.mlog.get_last_json_block('_NOT_PRESENT_')

    @parameterized.expand([
        ["67682", "Aegis of the Heavens"],
        ["123",   MtgaUnknownCard],
        ["67688", "Ajani's Last Stand"],
        ["68369", "Firesong and Sunspeaker"],
        ["71132", "Reconnaissance Mission"],
        ["70192", "Faerie Vandal"],
        ["69108", "Angelic Reward"]
    ])
    def test_collection(self, expected_mtga_id, expected_card_name):
        self.mlog.scryfall_fallback(True)
        collection = self.mlog.get_collection()
        for (mtga_id, card, count) in collection:
            if mtga_id == expected_mtga_id:
                try:
                    self.assertEqual(str(card.mtga_id), str(expected_mtga_id))
                    self.assertEqual(card.pretty_name, expected_card_name)
                except AttributeError:
                    self.assertIsInstance(card, expected_card_name)
                    mtga_id, card, count = next(collection)
                    self.assertIsInstance(card, scryfall.ScryfallError)

    def test_inventory(self):
        inventory = self.mlog.get_inventory()

        self.assertEqual(inventory.gems, 1)
        self.assertEqual(inventory.gold, 2)
        self.assertEqual(inventory.tokens['Draft'], 3)
        self.assertEqual(inventory.tokens['Sealed'], 4)
        self.assertEqual(inventory.vault_progress, 5.6)
        self.assertEqual(inventory.wildcards['Common'], 7)
        self.assertEqual(inventory.wildcards['Uncommon'], 8)
        self.assertEqual(inventory.wildcards['Rare'], 9)
        self.assertEqual(inventory.wildcards['Mythic Rare'], 10)

        starter_decks = inventory.starter_decks
        self.assertEqual(len(starter_decks), 2)
        self.assertEqual(starter_decks[0], '89622fa6-abf0-409e-b585-0f56d8514a77')
        self.assertEqual(starter_decks[1], 'a8e7c251-ea7a-49d5-8685-619008380aa8')

    def test_deck_lists(self):
        deck_lists = self.mlog.get_deck_lists()

        self.assertEqual(len(deck_lists), 2)
        kethis_deck = deck_lists[0]
        self.assertEqual(kethis_deck.name, 'Kethis Combo')
        self.assertEqual(kethis_deck.format, 'Standard')

        mtga_id, card, count = list(kethis_deck.maindeck)[0]
        self.assertEqual(mtga_id, 69996)
        self.assertEqual(card.pretty_name, 'Kethis, the Hidden Hand')
        self.assertEqual(count, 4)

        mtga_id, card, count = list(kethis_deck.sideboard)[1]
        self.assertEqual(mtga_id, 68645)
        self.assertEqual(card.pretty_name, 'Lazav, the Multifarious')
        self.assertEqual(count, 1)

        self.assertEqual(kethis_deck.deckbox_image.pretty_name, 'Fblthp, the Lost')
        self.assertEqual(kethis_deck.deck_id, '72ea9e67-1091-4e1c-81c2-3f2327378984')

    def test_preconstructed_deck_lists(self):
        precon_deck_lists = self.mlog.get_preconstructed_deck_lists()

        self.assertEqual(len(precon_deck_lists), 2)
        simic_flash = precon_deck_lists[0]
        self.assertEqual(simic_flash.name, 'Simic Flash')
        self.assertEqual(simic_flash.deck_id, '3b71e463-7a19-4a62-8695-855e024e645f')

class Test_Scryfall(unittest.TestCase):
    """Test the scryfall module"""

    @parameterized.expand([
        ["67682", "Aegis of the Heavens"],
        ["123", scryfall.ScryfallError],
        ["67688", "Ajani's Last Stand"],
        ["68369", "Firesong and Sunspeaker"],
        ["71132", "Reconnaissance Mission"],
        ["69108", "Angelic Reward"]
    ])
    def test_get_mtga_card(self, mtga_id, expected_card_name):
        """Test fetching cards from Scryfall using arena ids"""
        try:
            card = scryfall.get_mtga_card(mtga_id)
            self.assertEqual(card.pretty_name, expected_card_name)
        except Exception as exception:
            self.assertIsInstance(exception, expected_card_name)
