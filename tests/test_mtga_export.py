from __future__ import print_function
from future.utils import iteritems

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from parameterized import parameterized

import mtga_export
from mtga_export import MtgaLog, MtgaLogParsingError



class Test_MtgaLog(unittest.TestCase):

    def setUp(self):
        self.MTGA_LOG =  os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_mtga_output_log.txt')
        self.mlog = MtgaLog(self.MTGA_LOG)
        self.mlog_collection = self.mlog.get_collection(False)

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
        ["123",   mtga_export.MtgaUnknownCard],
        ["67688", "Ajani's Last Stand"],
        ["68369", "Firesong and Sunspeaker"],
        ["64037", "Bomat Courier"],
        ["69108", "Angelic Reward"]
    ])
    def test_collection(self, expected_mtga_id, expected_card_name):
        for (mtga_id, card, count) in self.mlog_collection:
            if mtga_id == expected_mtga_id:
                try:
                    self.assertEqual(card.pretty_name, expected_card_name)
                    self.assertEqual(str(card.mtga_id), str(expected_mtga_id))
                except AttributeError:
                    self.assertIsInstance(card, expected_card_name)



class Test_Scryfall(unittest.TestCase):
    pass