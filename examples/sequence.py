from typing import Sequence
from random import randint
from btypes import uint, metastruct

class MyRegister(metaclass=metastruct):
    rtype: uint(2, enum_={'grail':0, 'shrubbery':1, 'meaning':2, 'larch':3, 'gourd':4})
    stuff: uint(3)
    junk: uint(1)

class MyProtocol(metaclass=metastruct):
    header: uint(5)
    a: MyRegister
    b: MyRegister
    c: MyRegister

def datastream():
  while(1):
    yield randint(0,(1<<MyProtocol.size_)-1)

def look_for_fives(datastream: Sequence[int]):
    buffer = MyProtocol() # allocation of bit fields happens here, outside the loop
    bstuff = buffer.b.stuff # optimization: do attribute access outside loop
    hits = []

    for i, n in enumerate(datastream()): # iterate data source as sequence of abitrarily sized integers
        buffer.n_ = n # put the next block of data in the buffer
        if bstuff==5: # check if buffer.b.stuff == 5, this reduces to a simple shift-and operation with negligible overhead
            hits.append(i)

        if i==100:
          break

    return hits

print(look_for_fives(datastream))

