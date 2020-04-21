
![eric half-a-bee](images/b.png)
# btypes

Btypes is a tool for working with packed binary data. It's ideal for things like verilog interfaces, and any situation where you are working with arbitrarily sized bitfields.

# Philosophy of btypes

Half a bee, philosophically

Must, ipso facto, half not be

But half the bee has got to be

A vis-a-vis its entity, d'you see?

-- *Eric Idle*, on why he prefers btypes

# Comparison to [ctypes](https://docs.python.org/3/library/ctypes.html)

As the name suggests, some of concepts are inspired by ctypes. While there are similarities, the primary purpose is different.

| **tool** | **primary purpose** | **implementation** |
|----|--------|-------|
| ctypes | interface with C/C++ code, model C/C++ datatypes | python, C++ |
| btypes | model arbitary bit alligned datatypes and interfaces | python |


# Difference between btypes fields and C++ bit fields

In C++, bit field allocation is implementation defined. Usually word boundaries are respected, and the total size of a structure is padded to a multiple of 8 bits. This is the primary reason why `ctypes` is not suitable for certain use cases for which `btypes` was designed, such as verilog interface testing.

In `btypes`, the size of a `struct` is the sum of the size of it's members, which are allocated consecutively without implicit padding. Fields may even straddle word boundaries. The intent is to give the programmer full control and predictability with respect to bit allocation. If you create an array of 7 7-bit integers, it will occupy 49. Philosophically, must ipso facto not be padded to 64 bits. `uint(7)[7]._size == 49`. Also, there is no upper bound on the size of a field.

If this is not desired, it is up to the programmer to add padding as needed. Indeed, it would not be difficult to define a new btype class derived from `struct` and implement a different allocation scheme with padding.

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


# Interoperability

Every field (including the entire interface) has the following read/write properties that expose data:

| attribute | description |
|--|--|
| `_n` | The raw bits expressed as an int (unbounded size) |
| `_v` | The data value expressed as basic types: int, float, str, list, dict |
| `_json` | Same as `_v` expressed as a json string |

The type of the `_v` attribute depends on the underlyting btype of the field.
The btypes framework is extensible, the the following is not comprehensive.
As a rule, the value type is always json compatible.

| `x._btype` | `type(x._v)` | details |
|--|--|--|
| `uint(size)` | `int` | The size can be any positive integer number of bits |
| `sint(size)` | `int` | |
| `uint(size, enum)` | `str` or `int` | `enum={'label': value, ...}` output is str, input is either `int` or `str` 
| `struct((name, btype), ...)` | `dict` | values expanded recursively |
| `array(elem_type, dim)` | `list` | alternate syntax: `elem_type[dim]` |

When used directly, bound fields have duck-type behavior similar to their respective values, however it is important to keep in mind that fields are views of data. To access data properly, use the `_v` attribute.

# Performance

In `btypes`, performance is acheived by performing nearly all symbolic processing at interface allocation time, prior to binding data, and typically outside the main loop. So a python only application is pretty quick. Inside the main loop, a bound field is usually computed with nothing more than a `shift-and` operation.

The expressions module allows you to translate expressions such as filters and rules into purely numerical bitwise expressions. These expressions behave in the same way as ordinary fields, so you can bind them to a data source. Also they can be rendered as C/C++/python compatible source code strings which can then be processed with external tools such as numpy or compiled as C/C++. For example, `foo.payload.page[2].widget_type == 42` might translate to the somewhat less readable but faster `"(x[5] << 21) & 0x3f) == 42"`. That latter expression can filter millions of blocks per second, and the smaller result set can be conveniently processed in python. 


# Types, Fields, and Bound Fields


| | description | metatype  | example |
|--|--|--|--|
| *Type* | defines the size, representation, and other properties of a unit of binary data. | derived from `btype` | `foo = struct(('channel', uint(3)), ('pages', page[4]))) `| 
| *Interface* | a root field defined by a type (a special case of field) | named instance of a type allocated to offset 0, spanning the whole interface | `x = foo('x')` |
| *Field* | defines the type, name, and offest of a range of bits in an interface. | named instance of a type allocated to an offset within an interface | `x.channel` |
| *Bound Field* | A Field that is bound to a data source | instance of a field | `xdata = x(0x51e00034020039000023400020023)` |



