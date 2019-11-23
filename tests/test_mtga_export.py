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

    def test_get_last_json_block2(self):
        result = self.mlog.get_last_json_block('blah')
        self.assertEqual(result.get('foo'), 'bar')

    def test_get_last_json_block_new_format(self):
        result = self.mlog.get_last_json_block('<== NewFormat')
        self.assertEqual(
            result.get('payload').get('68286'), 1
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
        #["64037", "Bomat Courier"],
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

class Test_Scryfall(unittest.TestCase):
    """Test the scryfall module"""

    @parameterized.expand([
        ["67682", "Aegis of the Heavens"],
        ["123", scryfall.ScryfallError],
        ["67688", "Ajani's Last Stand"],
        ["68369", "Firesong and Sunspeaker"],
        ["64037", "Bomat Courier"],
        ["69108", "Angelic Reward"]
    ])
    def test_get_mtga_card(self, mtga_id, expected_card_name):
        """Test fetching cards from Scryfall using arena ids"""
        try:
            card = scryfall.get_mtga_card(mtga_id)
            self.assertEqual(card.pretty_name, expected_card_name)
        except Exception as exception:
            self.assertIsInstance(exception, expected_card_name)
