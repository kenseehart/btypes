"""
Playing Cards implementation using btypes

Copyright 2020, Ken Seehart
MIT License
https://github.com/kenseehart/btypes
"""

import random
import unittest

from btypes import enum, uint, unbound_field, field

class _card_t(uint):
    '''playing card'''

    def __init__(self):
        super().__init__(6, enum((r+s for r in '23456789TJQKA' for s in 'CHDS')))

    def allocate_(self, name:str, parent=None, offset:int=0) -> unbound_field:
        '''allocate a field recursively'''
        ftype = super().allocate_(name, parent, offset)
        
        self.fields_ = (('rank', uint(4, enum('23456789TJQKA'))),
                        ('suit', uint(2, enum('CHDS'))),
                        )
        z = offset

        for fname, ft in reversed(self.fields_):
            setattr(ftype, fname, ft.allocate_(f'{name}.{fname}', ftype, z))
            z += ft.size_

        return ftype

card = _card_t()


def shuffle(cards:field) -> None:
    a = list(map(int, cards))
    random.shuffle(a)
    # Naive in place sort, random.shuffle(deck), will not work correctly due to indirect reference of card fields.
    cards.v_ = a

def sort(cards:field) -> None:
    cards.v_ = sorted(map(int, cards))
    
    
class BCardsTest(unittest.TestCase):

    def test_deck(self):
        
        deck = card[52](range(52))
        self.assertEqual(deck, ['2C', '2H', '2D', '2S', '3C', '3H', '3D', '3S', '4C', '4H', '4D', '4S', '5C',
                                '5H', '5D', '5S', '6C', '6H', '6D', '6S', '7C', '7H', '7D', '7S', '8C', '8H',
                                '8D', '8S', '9C', '9H', '9D', '9S', 'TC', 'TH', 'TD', 'TS', 'JC', 'JH', 'JD',
                                'JS', 'QC', 'QH', 'QD', 'QS', 'KC', 'KH', 'KD', 'KS', 'AC', 'AH', 'AD', 'AS'])
        
        # assign data from previously shuffled deck
        deck.n_ = 206480033635037560160319767809886397911992016507243424853880220607585651965511326139019599053 
        
        self.assertEqual(deck, ['2H', 'JH', '7S', '5D', 'AC', 'JD', 'KS', '6H', '9D', 'QD', '9C', '8H', '3S',
                                '2D', '4S', 'AH', '7D', '4C', 'QS', 'TC', '5C', '7C', '8S', '3C', '6C', 'TD',
                                '5S', '8D', '4H', '4D', '3H', '8C', '6D', '2C', '2S', 'JS', '3D', 'KH', '9S',
                                '7H', 'TS', 'AD', 'QC', 'JC', 'TH', '6S', 'KC', 'KD', '9H', 'QH', 'AS', '5H'])
        
        self.assertEqual(deck, 206480033635037560160319767809886397911992016507243424853880220607585651965511326139019599053)
        
        hand = deck[5:10]
        self.assertEqual(hand, ['JD', 'KS', '6H', '9D', 'QD'])
        sort(hand)
        self.assertEqual(hand, ['6H', '9D', 'JD', 'QD', 'KS'])
        self.assertEqual(hand, [17, 30, 38, 42, 47])
        self.assertEqual(str(list(iter(hand))), "[<'6H'>, <'9D'>, <'JD'>, <'QD'>, <'KS'>]")

        self.assertEqual(hand[1], '9D')
        self.assertEqual(hand[1], 30)
        self.assertEqual(hand[1].rank, '9')
        self.assertEqual(hand[1].rank, 7)
        self.assertEqual(hand[1].suit, 'D')
        self.assertEqual(hand[1].suit, 2)
        self.assertEqual(repr(hand[1].suit), "<'D'>")

        self.assertEqual(deck, ['2H', 'JH', '7S', '5D', 'AC', '6H', '9D', 'JD', 'QD', 'KS', '9C', '8H', '3S',
                                '2D', '4S', 'AH', '7D', '4C', 'QS', 'TC', '5C', '7C', '8S', '3C', '6C', 'TD',
                                '5S', '8D', '4H', '4D', '3H', '8C', '6D', '2C', '2S', 'JS', '3D', 'KH', '9S',
                                '7H', 'TS', 'AD', 'QC', 'JC', 'TH', '6S', 'KC', 'KD', '9H', 'QH', 'AS', '5H'])

        sort(deck)
        self.assertEqual(deck, ['2C', '2H', '2D', '2S', '3C', '3H', '3D', '3S', '4C', '4H', '4D', '4S', '5C',
                                '5H', '5D', '5S', '6C', '6H', '6D', '6S', '7C', '7H', '7D', '7S', '8C', '8H',
                                '8D', '8S', '9C', '9H', '9D', '9S', 'TC', 'TH', 'TD', 'TS', 'JC', 'JH', 'JD',
                                'JS', 'QC', 'QH', 'QD', 'QS', 'KC', 'KH', 'KD', 'KS', 'AC', 'AH', 'AD', 'AS'])
        
        self.assertEqual(deck[0], '2C')
        self.assertEqual(deck[0], 0)
        self.assertEqual(deck[0].rank, '2')
        self.assertEqual(deck[0].rank, 0)
        self.assertEqual(repr(deck[0].suit), "<'C'>")
        
