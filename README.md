
![eric half-a-bee](images/b.png)
# btypes

Btypes is a tool for working with packed binary data. It's ideal for things like verilog interfaces, and any situation where you are working with arbitrarily sized bitfields, and you need precise convenient control of the bit arrangement.

# Philosophy of btypes

Half a bee, philosophically

Must, ipso facto, half not be

But half the bee has got to be

A vis-a-vis its entity, d'you see?

-- *John Cleese*  https://www.youtube.com/watch?v=ftomw87g61Y

# Comparison to [ctypes](https://docs.python.org/3/library/ctypes.html)

As the name suggests, some of concepts are inspired by ctypes. While there are similarities, the primary purpose is different. Both btypes and ctypes are able to easily encode/decode binary data such as c structs without a generated wrapper.

| **tool** | **model** | **primary purpose** | **implementation** |
|----|--------|---|----|
| ctypes | C/C++ types | interface with C/C++ code, model C/C++ datatypes | python, C++ |
| btypes | bit fields | model arbitary bit alligned datatypes and interfaces | python |

* Use ctypes if you need to interface with C/C++ code.
* Use btypes if you need to have full control over a bit aligned binary protocol.
* Use both ctypes and btypes if you need both. The can work together.

# Comparison to bitfields in C++

Unfortunately, the core philosophy of C/C++ is that the language ultimately decides how to allocate bits for optimal performance, and the language thinks it knows better than you how to do this, such as respecting byte or word boundaries. If you have a good reason to control bit alignment, you have to write methods to explicitly extract the desired bits. So bitfields in C are inadequate if you want to really control bitwise allocation and have predictable results, such as assuming the size in bits of a struct is the sum of the sizes of it's members. This level of control is relevant for things like protocol implementations and verilog. Now with `btypes`, bitfields behave the way you expect them to work.

In other words, `btypes` prioritizes detailed control over optimization and it does not respect word or byte boundaries. A struct with a 5 bit integer and a 13 bit integer is an 18 bit struct. Of course if you choose to design your structures to respect word boundaries, there may be use cases where doing so can improve performance, but that's entirely up to you.

The python `int` type efficiently implements a bit field of unbounded size. Btypes leverages this abstraction for raw binary data rather than the more conventional use of `bytes`. Because of this, byte misalignment issues do not add any expressive complexity. A field of any size or alignment can be extracted with a `shift-and` operation, and written with `shift-or`.

In C++, bit field allocation is implementation defined. Usually word boundaries are respected, and the total size of a structure is usually implicitly padded to a multiple of 8 bits. This is the primary reason why `ctypes` is not suitable for certain use cases for which `btypes` was designed, such as verilog interface testing, where explicit control of bit allocation is a requirement.

In `btypes`, the size of a `struct` is simply the sum of the size of it's members, which are allocated consecutively without implicit padding. Fields may even straddle word boundaries. The intent is to give the programmer full control and predictability with respect to bit allocation. If you allocate an array of 7 7-bit integers, it will occupy precisely 49 bits: `uint(7)[7].size_ == 49`. Also, there is no upper bound on the size of a field. Note that the `_size` attribute is the size in bits, whereas the C `sizeof()` operator is the size in bytes. 

Although it can be argued that byte/word alignment is usually a good idea, `btypes` is intentionally agnostic about such things, and gives complete control over alignment policies to the developer. However, if desired, it would not be difficult to implement a custom allocation policy to add padding as needed.


# Ease of use

``` python

raw_data_source = sequence_of_integers_from_somewhere()

parrot_struct = struct(
    status = uint(2, enum={'dead': 0, 'pining': 1, 'resting': 2},
    plumage_rgb = uint(5)[3],
) 

knight_struct = struct(
    name = uint(7)[20],
    cause_of_death = uint(3, enum={'vorpal_bunny':0, 'liverectomy':1, 'ni':2, 'question':3, 'mint':4},
)

quest_struct = struct(
    type = uint(3, enum={'grail':0, 'shrubbery':1, 'meaning':2, 'larch':3, 'gourd':4},
    knights = knight_struct[10],
    holy = uint(1),
    parrot = parrot_struct,
)


def get_dead_parrot_quests(raw_data_source: Sequence[int]) -> Iterator[str]:
    '''yields a sequence of json quests where the parrot is dead'''
    data = quest_struct()
    json_list = []
    
    # fields can be assigned outside the loop for speed and convenience
    status = data.parrot.status
    quest = data.quest

    for data.n_ in raw_data_source:
        if status == 'dead':
            yield quest.json_
            
```

Note that the data source is a sequence of integers.
This may be counterintuitive if you are accustomed to languages with finite sized integers.
Python integers are unbounded, which means a data record of any size can be encoded as a single integer, and btypes operates on these unbounded integers.

Typically your data source might be a sequence of arrays of 32 or 64 bit integers.
If so, it's easy to implement a generator to perform the conversion by shift-adding the arrays.

# Interoperability

Every field (including the entire interface) has the following read/write properties that expose data:

| attribute | description |
|--|--|
| `n_` | The raw bits expressed as an int (unbounded size) |
| `v_` | The data value expressed as basic types: int, float, str, list, dict |
| `json_` | Same as `v_` expressed as a json string |

The type of the `v_` attribute depends on the underlyting btype of the field.
The btypes framework is extensible, the the following is not comprehensive.
As a rule, the value type is always json compatible.

| `x.btype_` | `type(x.v_)` | details |
|--|--|--|
| `uint(size)` | `int` | The size can be any positive integer number of bits |
| `sint(size)` | `int` | |
| `uint(size, enum)` | `str` or `int` | `enum={'label': value, ...}` output is str, input is either `int` or `str` 
| `struct((name, btype), ...)` | `dict` | values expanded recursively |
| `array(elem_type, dim)` | `list` | alternate syntax: `elem_type[dim]` |

When used directly, bound fields have duck-type behavior similar to their respective values, however it is important to keep in mind that fields are views of data. To access data properly, use the `v_` attribute.

# Performance

In `btypes`, performance is acheived by performing nearly all symbolic processing at interface allocation time, prior to binding data, and typically outside the main loop. So a python only application is pretty quick. Inside the main loop, a bound field is usually computed with nothing more than a `shift-and` operation.

The expressions module allows you to translate expressions such as filters and rules into purely numerical bitwise expressions. These expressions behave in the same way as ordinary fields, so you can bind them to a data source. Also they can be rendered as C/C++/python compatible source code strings which can then be processed with external tools such as numpy or compiled as C/C++. For example, `foo.payload.page[2].widget_type == "fortytwo"` might translate to the somewhat less readable but faster `"(x[5] << 21) & 0x3f) == 42"`. That latter expression can filter millions of blocks per second, and the smaller result set can be conveniently processed in python. 

If you need performance that exceeds typical C++, we can help. See [high performance query module](https://github.com/kenseehart/btypes/issues/2) This would take about 40 hours of effort, hopefully with the support of a patron. Let me know if this is important to you. 

```
for quest in bcolz_data_source.query('quest', where='parrot.status=="dead"'):
    ...
```


# Trailing Underscore Convention

In order to give the developer full use of the field namespace, we distiguish fields from non-field attributes by marking the latter with a trailing underscore. For example, `foo.n_`, `foo.size_`. This means you may not define fields ending with `_`. 

If you implement a custom type and you wish to define your own non-field attributes, please use a trailing underscore for that purpose.

You can assign arbitrarily to trailing underscore attributes (if they are not defined by btypes) for use as metadata, etc.

# Metatypes, field types, and fields

It's important when using **btypes** to have a clear understanding of levels of types. So, for example, `uint` is a metatype which you instantiate to get a field type, so `uint(5)` is a 5 bit unsigned integer field type (as opposed to an unsigned integer with a value of 5). You instantiate a field type to get a field, e.g. `x = uint(5)()`, and then assign values to the field via the `x.v_` or `x.n_` attributes. Metatypes are important because they support expression of complex datatypes such as structures and arrays, e.g. `struct(('x', uint(5)), ('y', array(uint(3), 4)), ('z', uint(15))`. 


# Possible future extensions

- Parse Verilog to **btypes**
  - Use an existing parser such as [Pyverilog: https://github.com/PyHDI/Pyverilog]
  - Creates btype field types directly from a verilog string. Python code generation, if needed, is already implemented as the repr of the field type.

- numpy + bcolz integration
  - Massive performance boost by instantiating low level functions from high level python code. Potentially process terabytes of data in seconds.
  - New `expr_` attribute gives a string representation of a field as shift-and operations operating on native integer arrays.
  - The expression string would be compatible with C++, python, numpy, and anything using similar syntax for logic operations.

- Additional Verilog and SystemVerilog support
  - parallel bitfields to implement X and Z values
  - interfaces to simulator/emulator tools

