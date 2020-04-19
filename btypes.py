"""
Copyright 2020, Ken Seehart
All rights reserved.

License to Jon Shiell for research purposes only, subject to NDA.
Commercial use prohibited.

A framework for packed binary data
"""

import unittest
from typing import Union, Any, Callable
from itertools import islice
from pprint import pprint as std_pprint
import json

try:
    import libcst # required for _expr and _cst attribute support
except ImportError:
    libcst = None

def assert_libcst():
    if not libcst:
        raise NotImplementedError('Expression features require libcst: pip install libcst')

if libcst:
    from .expressions import cst_uint, cst_expr, cst_source_code, CSTNode

def enum(a:Union[list, str]) -> dict:
    '''return an _enum dict given an iterable'''
    return {c:i for i,c in enumerate(a)}

def isiter(obj) -> bool:
    '''return `True` if obj is a non-string iterable'''
    return hasattr(obj, '__iter__') and not isinstance(obj, str)


def pprint(v):
    '''
    pretty print customized for btypes usage
    
    dictionaries keep original order (not sorted)
    bound fields converted to value
    '''
    
    if isinstance(v, bound_field):
        v = v._v
        
    std_pprint(v, sort_dicts=False)



class IntDuck:
    '''Implement integer emulation. Define __int__() and IntDuck does the rest.
    Integer behavior supercedes _enum, including ordering.
    Not suitable for floating point
    '''
    
    def __index__(self):
        return int(self)
    
    def __add__(self, other):
        return int(self) + other

    def __radd__(self, other):
        return other + int(self)

    def __iadd__(self, other):
        self._n += other
        return self

    def __mul__(self, other):
        return int(self) * other

    def __rmul__(self, other):
        return other * int(self)

    def __imul__(self, other):
        self._n = int(self) * other
        return self

    def __sub__(self, other):
        return int(self) - other

    def __rsub__(self, other):
        return other - int(self)

    def __isub__(self, other):
        self._n -= other
        return self

    def __div__(self, other):
        return int(self) / other

    def __rdiv__(self, other):
        return other / int(self)

    def __floordiv__(self, other):
        return int(self) // other

    def __rfloordiv__(self, other):
        return other // int(self)

    def __ifloordiv__(self, other):
        self._n = int(self) // other
        return self    
    
    def __and__(self, other):
        return self._n & other
        
    def __rand__(self, other):
        return other & self._n
        
    def __iand__(self, other):
        self._n &= other
        return self

    def __or__(self, other):
        return self.n | other
        
    def __ror__(self, other):
        return other | self._n

    def __ior__(self, other):
        self._n |= other
        return self

    def __rshift__(self, other):
        return self.n >> other
    
    def __rrshift__(self, other):
        return other >> self.n 
    
    def __irshift__(self, other):
        self.n >>= other
        return self
    
    def __lshift__(self, other):
        return self.n << other
    
    def __rlshift__(self, other):
        return other << self.n 
    
    def __ilshift__(self, other):
        self.n <<= other
        return self
    
    def __lt__(self, other):
        return int(self) < int(other)

    def __gt__(self, other):
        return int(self) > int(other)
    
    def __le__(self, other):
        return int(self) <= int(other)
    
    def __ge__(self, other):
        return int(self) >= int(other)



class NumDuck(IntDuck):
    '''Implement numeric emulation, where self._v is expected to be numeric.
    Not suitable for enums.
    '''
    
    def __add__(self, other):
        return self._v + other

    def __radd__(self, other):
        return other + self._v

    def __iadd__(self, other):
        self._v += other
        return self

    def __mul__(self, other):
        return self._v * other

    def __rmul__(self, other):
        return other * self._v

    def __imul__(self, other):
        self._v *= other
        return self

    def __sub__(self, other):
        return self._v - other

    def __rsub__(self, other):
        return other - self._v

    def __isub__(self, other):
        self._v -= other
        return self

    def __div__(self, other):
        return self._v / other

    def __rdiv__(self, other):
        return other / self._v

    def __idiv__(self, other):
        self.v /= other
        return self.v

    def __floordiv__(self, other):
        return self._v // other

    def __rfloordiv__(self, other):
        return other // self._v

    def __ifloordiv__(self, other):
        self._v //= other
        return self    
    
    def __lt__(self, other):
        return self._v < other

    def __gt__(self, other):
        return self._v > other
    
    def __le__(self, other):
        return self._v <= other
    
    def __ge__(self, other):
        return self._v >= other

class field(type):
    '''Unbound field implementing propery protocol'''

    def __repr__(self):
        return self.__name__

    def __bool__(self):
        return True
    
    @property
    def _desc(self):
        return f'{type(self._btype).__name__} {self.__name__}'

    def __get__(self, instance, owner):
        if instance is None: # unbound field
            return self
        else:
            return self(instance) # return the binding of this field to the target

    def __set__(self, instance, value):
        self(instance)._v = value

    def __getitem__(self, k):
        if isinstance(k, int):
            try:
                return getattr(self, f'_{k}')
            except AttributeError as e:
                if self._btype._dim is not None:
                    raise IndexError(f'{self._desc} index {k} out of range') from e
                else:
                    raise TypeError(f'{self._desc} is not subscriptable') from e
        elif(isinstance(k, slice)):
            if self._btype._dim is not None:
                fname = f'{k.start}_{k.stop}_{k.step}'
                try:
                    return getattr(self, fname)
                except AttributeError:
                    ft = bslice(self._btype, k)
                    f = ft._allocate(f'{self.__name__}.{fname}', self)
                    setattr(self, fname, f) 
                    return f
            else:
                raise TypeError(f'{self._desc} is not subscriptable') from e
        else:
            try:
                return getattr(self, k)
            except AttributeError as e:
                raise KeyError(f'{self.__name__}:undefined subfield {k}') from e


    def __iter__(self):
        if self._btype._dim is None:
            raise TypeError(f'{self._desc} is not iterable')
        
        for i in range(self._btype._dim):
            yield self[i]     

    def __len__(self):
        if self._btype._dim is None:
            raise TypeError(f'{self._desc} has no len()')
        else:
            return self._btype._dim


    @property
    def _this(self):
        return self
    
    def _cst(self, expr: str='', word_size: int=0) -> CSTNode:
        '''Return a CSTNode for this field, or an expression  
        '''
        assert_libcst()

        if expr=='':
            return cst_uint(self._offset, self._mask, word_size)
        else:
            def resolver(s: str, word_size=word_size) -> CSTNode:
                return self[s]._cst('', word_size)
            
            return cst_expr(expr, resolver, word_size)
            
    
    def _expr(self, expr: str='', word_size: int=0) -> str:
        return cst_source_code(self._cst(expr, word_size))

    def _expr_field(self, expr: str, word_size: int=0) -> str:
        cst = self._cst(expr, word_size)
        src = cst_source_code(cst)
        d={}
        exec('def fn(n: int):\n    return '+src, d, d)
        fnf = fn_type(d['fn'], src)._allocate('<expr>', self)
        fnf._expr = lambda *a: src
        
        return fnf


class bound_field(IntDuck, metaclass=field):
    '''Bound field'''
    _offset:int
    _mask:int
    __slots__ = ('_target',)
    
    def __init__(self, target=0):
        '''bind a field to a target list consisting of a single integer'''
        if isinstance(target, bound_field):
            self._target = target._target
        else:
            self._target = [0]
            self._v = target
        
    def __repr__(self):
        return f'<{repr(self._v)}>'
    
    @property
    def _n(self) -> int:
        '''raw integer value'''
        return (self._target[0] >> self._offset) & self._mask
        
    @_n.setter        
    def _n(self, n:int):
        self._target[0] = self._target[0] & ~(self._mask << self._offset) | ((n&self._mask) << self._offset)

    @property
    def _v(self) -> int:
        '''overload _mixin to express as a different type'''
        return int(self)
        
    @_v.setter        
    def _v(self, n:int):
        '''overload _mixin to receive other data types'''
        self._n = n

    @property
    def _json(self):
        return json.dumps(self._v)

    @_json.setter
    def _json(self, s):
        self._v = json.loads(s)

    def __bool__(self):
        return self._n != 0

    def __len__(self):
        return self._btype._dim

    # comparison
    def __eq__(self, other):
        if isinstance(other, int):
            return int(self)==other

        if isinstance(other, str):
            return str(self)==other

        if isiter(other):
            if len(self) == len(other):
                for sv, ov in zip(self, other):
                    if sv!=ov:
                        return False
                else:
                    return True
            else:
                return False

        if isinstance(other, bound_field):
            return self._n == other._n
        
        return self._v == other
        
    def __int__(self): # may be overloaded (e.g. sint support for negatives)
        return self._n
    
    def __str__(self):
        return str(self._v)
    
    def __setitem__(self, k, v):
        if isinstance(k, int):
            k = f'_{k}' # array elements as field property instances
        
        setattr(self, k, v)
        
    def __setattr__(self, k, v):
        if k in self.__slots__ or hasattr(self, k):
            super().__setattr__(k, v)
        else:
            raise KeyError(f'{type(self)} does not have attribute {k}')

    def __getattr__(self, k):
        return getattr(self._btype, k)

class btype:
    '''Base class for type classes'''
    _repr:str
    _size:int
    _dim:int = None
    
    def __call__(self, name:str, value:Any=None) -> field:
        mf = self._allocate(name)
        if value is None:
            return mf
        else:
            f = mf([0])
            f._v = value
            return f
        
    def _allocate(self, name, parent:field=None, offset:int=0) -> bound_field:
        ftype = field(name, (type(self)._mixin,), {})
        ftype._parent = parent
        ftype._root = parent._root if parent else ftype
        ftype._size = self._size
        ftype._mask = ((1<<self._size)-1)
        ftype._offset = offset
        ftype._btype = self
        return ftype
   
    def __repr__(self):
        return self._repr
    
    def __getitem__(self, n):
        return array(self, n)

class uint(btype):
    '''unsigned integer with optional enum'''

    def __init__(self, size:int, _enum=None):
        self._size = size
        self._repr = f"uint({size})"
        self._enum = _enum or {}
        self._renum = {v:k for k,v in self._enum.items()}
        
    class _mixin(bound_field):
        @property
        def _v(self) -> Union[int, str]:
            v = int(self)
            try:
                v = self._btype._renum[v] # defaults to raw int if enum is not defined
            except KeyError:
                pass
            return v
            
        @_v.setter        
        def _v(self, v:Union[int, str]):
        
            if isinstance(v, str):
                try:
                    v = self._btype._enum[v]
                except KeyError:
                    try:
                        v = int(v)
                    except ValueError:
                        raise ValueError(f'{f}: undefined enum {v}')
                    
            self._n = v



class sint(uint):
    '''signed integer with optional enum'''

    class _mixin(uint._mixin):
        def __int__(self):
            v = self._n
            if v&(1<<(self._size-1)):
                v = v - (1<<(self._size))
            return v
        
        

class decimal(sint):
    '''fixed point decimal encoded as signed integer
    
    decimal(16, 2) = 16 bits, 2 decimal places (-655.35 <= v <= 655.36)
    decoded values are floating point
    '''

    def __init__(self, size:int, e:int):
        self._e = e
        self._divisor = 10**e
        self._size = size
        self._repr = f"decimal({size, e})"
        self._max = ((1<<size)-1)/self._divisor
        self._min = -self._max

    class _mixin(NumDuck, sint._mixin):
        def __int__(self):
            return int(float(self))
    
        def __float__(self):
            v = self._n
            if v&(1<<(self._size-1)):
                v = v - (1<<(self._size))
            return v/self._divisor

        @property
        def _v(self) -> float:
            return float(self)
            
        @_v.setter        
        def _v(self, v:float):
            try:
                if v<self._min or v>self._max:
                    raise ValueError(f'{type(self)._desc}: value {v} out of range {self._min} <= value <= {self._max}')
            except TypeError as e:
                raise TypeError(f"{type(self)._desc} doesn't support assignment of {type(v)}")
            self._n = int(v*self._divisor)


class struct(btype):
    def __init__(self, *fields):
        self._fields = fields
        self._size = sum(f._size for _,f in fields)
        self._repr = f"struct{fields}"
        
    def _allocate(self, name:str, parent:field=None, offset:int=0) -> field:
        '''allocate a field recursively'''
        ftype = super()._allocate(name, parent, offset)
        z = offset

        for fname, ft in reversed(self._fields):
            setattr(ftype, fname, ft._allocate(f'{name}.{fname}', ftype, z))
            z += ft._size

        return ftype
    
    class _mixin(bound_field):

        @property
        def _v(self) -> dict:
            d = {}
            for k, t in self._btype._fields:
                d[k] = getattr(self, k)._v
            return d
            
        @_v.setter        
        def _v(self, v:Union[int, dict]):
            if isinstance(v, dict):
                for k, fv in v.items():
                    setattr(self, k, fv)
            else:
                self._n = v

        def __iter__(self): 
            for k, t in self._btype._fields:
                yield k

        def __getitem__(self, k):
            try:
                return getattr(self, k)
            except AttributeError as e:
                raise KeyError(f'{type(self)} does not have field "{k}"') from e

class array(struct):
    '''array'''
    
    def __init__(self, etype: btype, dim:int):
        self._etype = etype
        self._dim = dim
        self._size = etype._size*dim
        self._repr = f"{etype}[{dim}]"
        self._fields = tuple((f'_{i}',  etype) for i in range(dim))
        
    class _mixin(struct._mixin):
        @property
        def _v(self) -> list:
            return [self[i]._v for i in range(self._btype._dim)]
            
        @_v.setter        
        def _v(self, v:Union[int, list, tuple]):
            if isinstance(v, int):
                self._n = v
            elif isiter(v):
                for i, fv in enumerate(v):
                    setattr(self, f'_{i}', fv)
            else:
                raise TypeError('assignment to array must be int or iterable')
            
        def __getitem__(self, k):
            if isinstance(k, int):
                try:
                    k = f'_{k}' # array elements as field property instances
                    return getattr(self, k)
                except AttributeError as e:
                    raise IndexError(f'array index {k[1:]} out of range') from e
            elif(isinstance(k, slice)):
                ftype = type(self)[k]
                return ftype(self)
            else:
                super().__getitem__(k)
                
        def __iter__(self):
            for f in iter(type(self)):
                yield f(self)


class bslice(array):
    '''array slice'''
    
    def __init__(self, atype: array, aslice: slice):
        self._atype = atype
        self._etype = atype._etype
        self._slice = aslice
        self._islice = list(range(*aslice.indices(atype._dim)))
        self._dim = len(self._islice)
        self._size = self._etype._size*self._dim
        self._repr = f"{atype}[{aslice}]"

    def _allocate(self, name:str, parent:field, offset:int=0) -> field:
        '''allocate a field recursively'''
        ftype = btype._allocate(self, name, parent, offset)

        for i,j in enumerate(self._islice):
            setattr(ftype, f'_{i}', parent[j])

        return ftype
            


class fn_type(btype):
    def __init__(self, fn: Callable[[int], Any], expr: str):
        self._fn = fn
        self._size = 0
        self._repr = f"fn_type({fn})"        

        
    class _mixin(bound_field):
        @property
        def _v(self) -> Any:
            return self._fn(self._target[0])

        @property
        def _n(self) -> int:
            return int(self._v)




class BTypesTest(unittest.TestCase):
    def test_simple(self):
        u4t = uint(4) # type
        u4i = u4t('u4i') # interface (unbound field)
        u4 = u4i() # bound field
        u4._n = 3 # raw int value

        self.assertEqual(repr(u4t), 'uint(4)')
        self.assertEqual(repr(u4i), 'u4i')
        self.assertEqual(repr(u4), '<3>')
        self.assertEqual(u4._n, 3)
        self.assertEqual(u4, 3)
        u4 += 2
        self.assertEqual(u4, 5)
        u4 *= 2
        self.assertEqual(u4, 10)
        u4 //= 2
        self.assertEqual(u4, 5)

        with self.assertRaises(TypeError):
            u4 /= 2
        
        
    def test_struct(self):
        foo = struct(
            ("a", uint(3)),
            ("b", uint(4)),
        )
        
        bar = struct(
            ("f", foo), # array of 10 foo elements
            ("c", uint(5)),
        )
        
        foobar = struct(
            ("a", uint(3, _enum={"alpha":0, "beta":1, "gamma":2})),  # 3 bit integer with enum
            ("b", sint(4)), # 4 bit integer
            ("bars", bar[5]), # array of 5 bars
        )
        
        f = foobar('f')(0)
        f.a = 'beta'
        f.b = -1
        print (f"f['b'] = {f['b']}")

        self.assertEqual(f.b, -1)
        
        with self.assertRaises(KeyError):
            f['c']
            
        with self.assertRaises(AttributeError):
            f.c
        
    def test_decimal(self):
        foo = decimal(16, 2)('foo')(123.45)
        
        self.assertEqual(foo, 123.45)
        self.assertEqual(foo+1.0, 124.45)

    def test_expr(self):
        foo = struct(
            ("a", uint(3)),
            ("b", uint(4)),
        )('foo')
        
        self.assertEqual(foo.a._expr(), '(n >> 4 & 0x7)')
        self.assertEqual(foo.b._expr(), '(n & 0xf)')
        
        foo.ab = foo._expr_field('a * b')
        
        fd = foo(0xffff)
        
        ab = fd.ab
        self.assertEqual(ab, 105)
        
        self.assertEqual(fd.ab._expr(), '(n >> 4 & 0x7) * (n & 0xf)')
        self.assertEqual(foo.ab._expr(), '(n >> 4 & 0x7) * (n & 0xf)')
        
