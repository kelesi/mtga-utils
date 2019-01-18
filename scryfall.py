# -*- coding: utf-8 -*-

"""Scryfall to python-mtga Card
"""

import requests
from mtga.models.card import Card
import argparse
import json


SCRYFALL_CARDS_API = "https://api.scryfall.com/cards"
SCRYFALL_SETS_API = "https://api.scryfall.com/sets"


class ScryfallError(ValueError):
    pass


def get_mtga_card(arena_id):
    scryfall_card = get_arena_card_json(arena_id)
    return scryfall_to_mtga(scryfall_card)


def get_arena_card_json(arena_id):
    """Get card from Scryfall by arena id"""
    response = requests.get(SCRYFALL_CARDS_API+'/arena/'+str(arena_id))
    if response.status_code != requests.codes.ok:
        raise ScryfallError('Unknown card id %s. Status code: %s' % (arena_id, response.status_code))
    return response.json()


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
    set_id = scryfall_card['set'].upper()
    rarity = scryfall_card['rarity']
    set_number = scryfall_card['collector_number']
    mtga_id = scryfall_card['arena_id']
    mtga_card = Card(
        name, pretty_name, cost, color_identity,
        card_type, sub_types, set_id, rarity, set_number, mtga_id
    )
    return mtga_card

def get_set_info(set_name):
    """gets info on requested set"""
    response = requests.get(SCRYFALL_SETS_API+'/'+str(set_name))
    if response.status_code == requests.codes.not_found:
        print('Unknown set: %s. Reason: %s %s' % (set_name, response.status_code, response.reason))
        return {}
    if response.status_code != requests.codes.ok:
        raise ScryfallError('Unknown set: %s. Status code: %s' % (set, response.status_code))
    return response.json()

if __name__ == "__main__":
    x = get_arena_card_json(68369)
    print(scryfall_to_mtga(x))
    y = get_arena_card_json(67542)
    print(scryfall_to_mtga(y))
