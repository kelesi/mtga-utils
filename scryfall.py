# -*- coding: utf-8 -*-

"""Scryfall to python-mtga Card
"""

import requests
from mtga.models.card import Card
import argparse
import json

SCRYFALL_API = "https://api.scryfall.com/cards"

def get_arena_card_json(arena_id):
    """Get card from Scryfall by arena id"""
    card = requests.get(SCRYFALL_API+'/arena/'+str(arena_id))
    return card.json()

def scryfall_to_mtga(scryfall_card):
    name = scryfall_card['name'].lower().replace(' ', '_')
    pretty_name = scryfall_card['name']
    cost = list(scryfall_card['mana_cost'].replace('}', '').replace('{', ''))
    color_identity = scryfall_card['color_identity']
    types = scryfall_card['type_line'].split(u' — ')
    card_type = types[0]
    try:
        sub_types = types[1]
    except IndexError:
        sub_types = ""
    set_id = scryfall_card['set']
    rarity = scryfall_card['rarity']
    set_number = scryfall_card['collector_number']
    mtga_id = scryfall_card['arena_id']
    mtga_card = Card(
        name, pretty_name, cost, color_identity,
        card_type, sub_types, set_id, rarity, set_number, mtga_id
    )
    return mtga_card


if __name__ == "__main__":
    x = get_arena_card_json(68369)
    print scryfall_to_mtga(x)
    y = get_arena_card_json(67542)
    print scryfall_to_mtga(y)
