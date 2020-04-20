# BTypes

Btypes is a tool for working with packed binary data. It's ideal for things like verilog interfaces, and any situation where you are working with bitfields.

# Comparison to ctypes
As the name suggests, some of the usage and features are inspired by ctypes. While there are similarities, the primary purpose is different.

|    | ctypes | btypes |
|----|--------|-------|
| **primary purpose** | interface with C/C++ code  | process bit alligned interfaces  |
| **implementation** | python and C++ | python |


# Ease of use

``` python

raw_data = sequence_of_integers()

def get_dead_parrot_quests(raw_data_source: Sequence[int]) -> Iterator[str]:
    '''yields a sequence of json quests where the parrot is dead'''
    data = my_interface()
    json_list = []
    
    # fields can be assigned outside the loop for speed and convenience
    status = data.parrot.status
    quest = data.quest

    for data._n in raw_data_source:
        if status == 'dead':
            yield quest._json
            
```




# Performance

In `btypes`, performance is acheived by performing nearly all symbolic processing outside the main loop. So a python only application is pretty quick. You can create bound field instances outside the main loop, so inside the main loop, a bound field is computed with nothing more than a `shift-and` operation.

Expressions such as filters and rules can be processed into purely numerical bitwise expressions. These expressions behave in the same way as fields, so you can bind them to a data source. Also they can be rendered as C/python compatible source code strings which can then be processed with external tools such as numpy or compiled as C/C++. For example, `foo.payload.page[2].widget_type==42` translates to the somewhat less readable but faster `"(x[2]<<21)&0x3f)==42"`. That latter expression can filter millions of blocks per second, and the smaller result set can be easily processed in python. 

``` python

```

# Types, Fields, and Bound Fields


| | description | metatype  | example |
|--|--|--|--|
| *Type* | defines the size, representation, and other properties of a unit of binary data. | derived from `btype` | `foo = struct(('channel', uint(3)), ('pages', page[4]))) `| 
| *Interface* | a root field defined by a type (a special case of field) | named instance of a type allocated to offset 0, spanning the whole interface | `x = foo('x')` |
| *Field* | defines the type, name, and offest of a range of bits in an interface. | named instance of a type allocated to an offset within an interface | `x.channel` |
| *Bound Field* | A Field that is bound to a data source | instance of a field | `xdata = x(0x51e00034020039000023400020023)` |
