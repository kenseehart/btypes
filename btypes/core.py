"""
btypes.core

A framework for packed binary data

Copyright 2020, Ken Seehart
MIT License
https://github.com/kenseehart/btypes
"""


import sys
import unittest
from typing import Union, Any, Callable
from pprint import pprint as std_pprint
import json

from btypes.expressions import CSTNode, cst_expr, cst_source_code, cst_uint, is_identifier
from btypes.numduck import IntDuck, NumDuck

_all_above_excluded = set(locals().keys())

# everything defined below this will be exported to the btypes package

def enum(a:Union[list, str]) -> dict:
    '''return an enum_ dict given an iterable'''
    return {c:i for i,c in enumerate(a)}

def isiter(obj) -> bool:
    '''return `True` if obj is a non-string iterable'''
    return hasattr(obj, '__iter__') and not isinstance(obj, str)


def pprint(v):
    '''
    pretty print customized for btypes usage
    
    dictionaries keep original order (not sorted)
    bound fields are converted to value
    '''
    
    if isinstance(v, field):
        v = v.v_
        
    std_pprint(v, sort_dicts=False)


def field_method(f):
    '''decorator that exposes a metaclass method to an instance of the class'''
    f._is_field_method = True
    return f
    
    
class unbound_field(type):
    '''Unbound field implementing propery protocol'''
    
    def __init__(self, name, bases, dict_):
        super().__init__(name, bases, dict_)
        for k, f in type(self).__dict__.items():
            if getattr(f, '_is_field_method', False):
                setattr(self, k, f)
        

    def __repr__(self):
        return f'<unbound_field: {self.__name__}>'

    def __bool__(self):
        return True
    
    @property
    def desc_(self):
        return f'{type(self.btype_).__name__} {self.__name__}'

    def __get__(self, instance, owner):
        if instance is None: # unbound field
            return self
        else:
            return self(instance) # return the binding of this field to the target

    def __set__(self, instance, value):
        self(instance).v_ = value

    def __getitem__(self, k):
        if isinstance(k, int):
            try:
                return getattr(self, f'_{k}')
            except AttributeError as e:
                if self.btype_.dim_ is not None:
                    raise IndexError(f'{self.desc_} index {k} out of range') from e
                else:
                    raise TypeError(f'{self.desc_} is not subscriptable') from e
        elif(isinstance(k, slice)):
            if self.btype_.dim_ is not None:
                fname = f'{k.start}_{k.stop}_{k.step}'
                try:
                    return getattr(self, fname)
                except AttributeError:
                    ft = bslice(self.btype_, k)
                    f = ft.allocate_(f'{self.__name__}.{fname}', self)
                    setattr(self, fname, f) 
                    return f
            else:
                raise TypeError(f'{self.desc_} is not subscriptable') from e
        else:
            try:
                return getattr(self, k)
            except AttributeError as e:
                raise KeyError(f'{self.__name__}:undefined subfield {k}') from e


    def __iter__(self):
        if self.btype_.dim_ is None:
            raise TypeError(f'{self.desc_} is not iterable')
        
        for i in range(self.btype_.dim_):
            yield self[i]     

    def __len__(self):
        if self.btype_.dim_ is None:
            raise TypeError(f'{self.desc_} has no len()')
        else:
            return self.btype_.dim_


    @property
    def this_(self):
        return self
    
    @field_method
    def cst_(self, expr: str='', word_size: int=0) -> CSTNode:
        '''Return a CSTNode for this field, or an expression  
        '''
        if expr=='':
            return cst_uint(self.offset_, self.mask_, word_size)
        else:
            def resolver(s: str, word_size=word_size) -> CSTNode:
                return self[s].cst_('', word_size)
            
            return cst_expr(expr, resolver, word_size)
            
    
    @field_method
    def expr_(self, expr: str='', word_size: int=0) -> str:
        return cst_source_code(self.cst_(expr, word_size))

    @field_method
    def expr_field_(self, expr: str, word_size: int=0) -> str:
        cst = self.cst_(expr, word_size)
        src = cst_source_code(cst)
        d={}
        exec('def fn(n: int):\n    return '+src, d, d)
        fnf = fn_type(d['fn'], src).allocate_('<expr>', self)
        fnf.expr_ = lambda *a: src
        
        return fnf
    


class field(IntDuck, metaclass=unbound_field):
    '''Bound field'''
    offset_:int
    mask_:int
    __slots__ = ('target_',)
    
    def __init__(self, target_field:'field' = None):
        '''bind a field to a target list consisting of a single integer'''
        if target_field is not None:
            self.target_ = target_field.target_
        else:
            self.target_ = [0]
        
    def __repr__(self):
        return f'<{repr(self.v_)}>'
    
    @property
    def n_(self) -> int:
        '''raw integer value'''
        return (self.target_[0] >> self.offset_) & self.mask_
        
    @n_.setter        
    def n_(self, n:int):
        self.target_[0] = self.target_[0] & ~(self.mask_ << self.offset_) | ((n&self.mask_) << self.offset_)

    @property
    def v_(self) -> int:
        '''overload mixin_field_ to express as a different type'''
        return int(self)
        
    @v_.setter        
    def v_(self, n:int):
        '''overload mixin_field_ to receive other data types'''
        self.n_ = n

    @property
    def json_(self):
        return json.dumps(self.v_)

    @json_.setter
    def json_(self, s):
        self.v_ = json.loads(s)

    def __bool__(self):
        return self.n_ != 0

    def __len__(self):
        return self.btype_.dim_

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

        if isinstance(other, field):
            return self.n_ == other.n_
        
        return self.v_ == other
        
    def __int__(self): # may be overloaded (e.g. sint support for negatives)
        return self.n_
    
    def __str__(self):
        return str(self.v_)
    
    def __setitem__(self, k, v):
        if isinstance(k, int):
            k = f'{k}_' # array elements as field property instances
        
        setattr(self, k, v)
        
    def __setattr__(self, k, v):
        if k in self.__slots__ or hasattr(self, k):
            super().__setattr__(k, v)
        else:
            msg = f'{type(self)} does not have attribute {k}'
            if hasattr(self, k+'_'):
                msg += ': did you mean {k}_ ?'
            raise KeyError(msg)

    def __getattr__(self, k):
        try:
            return getattr(self.btype_, k)
        except AttributeError as e:
            raise AttributeError(f"'{self.name_}' field has no attribute '{k}'") from e
    
class btype:
    '''Base class for type classes'''
    repr_:str
    size_:int
    dim_:int = None
    
    def __call__(self, value:int=0) -> field:
        'Create a new bound interface from this btype'
        ufield = self.allocate_(self.name_)
        f = ufield()
        f.v_ = value
        return f
        
    def allocate_(self, name, parent:unbound_field=None, offset:int=0) -> field:
        'allocate a unbound_field of this btype, into the specified parent if specified, else allocate as the interface root'
        ufield = unbound_field(name, (type(self).mixin_field_,), {})
        ufield.parent_ = parent
        ufield.root_ = parent.root_ if parent else ufield
        ufield.size_ = self.size_
        ufield.mask_ = ((1<<self.size_)-1)
        ufield.offset_ = offset
        ufield.btype_ = self
        return ufield
   
    def __repr__(self):
        return self.repr_
    
    def __getitem__(self, n):
        return array(self, n)

class uint(btype):
    '''unsigned integer with optional enum'''

    def __init__(self, size:int, enum_:dict = None, name_:str = None):
        self.size_ = size
        self.repr_ = f"uint({size})"
        self.enum_ = enum_ or {}
        self.renum_ = {v:k for k,v in self.enum_.items()}
        self.name_ = name_ or f'{type(self).__name__}{size}'
        
    class mixin_field_(field):
        @property
        def v_(self) -> Union[int, str]:
            v = int(self)
            try:
                v = self.btype_.renum_[v] # defaults to raw int if enum is not defined
            except KeyError:
                pass
            return v
            
        @v_.setter        
        def v_(self, v:Union[int, str]):
        
            if isinstance(v, str):
                try:
                    v = self.btype_.enum_[v]
                except KeyError:
                    try:
                        v = int(v)
                    except ValueError:
                        raise ValueError(f'{f}: undefined enum {v}')
                    
            self.n_ = v



class sint(uint):
    '''signed integer with optional enum'''

    class mixin_field_(uint.mixin_field_):
        def __int__(self):
            v = self.n_
            if v&(1<<(self.size_-1)):
                v = v - (1<<(self.size_))
            return v
        
        

class decimal(sint):
    '''fixed point decimal encoded as signed integer
    
    decimal(16, 2) = 16 bits, 2 decimal places (-655.35 <= v <= 655.36)
    decoded values (self.v_) are float
    '''

    def __init__(self, size:int, e:int):
        self.e_ = e
        self.divisor_ = 10**e
        self.size_ = size
        self.repr_ = f"decimal({size, e})"
        self.max_ = ((1<<size)-1)/self.divisor_
        self.min_ = -self.max_
        self.name_ = type(self).__name__

    class mixin_field_(NumDuck, sint.mixin_field_):
        def __int__(self):
            return int(float(self))
    
        def __float__(self):
            v = self.n_
            if v&(1<<(self.size_-1)):
                v = v - (1<<(self.size_))
            return v/self.divisor_

        @property
        def v_(self) -> float:
            return float(self)
            
        @v_.setter        
        def v_(self, v:float):
            try:
                if v<self.min_ or v>self.max_:
                    raise ValueError(f'{type(self).desc_}: value {v} out of range {self.min_} <= value <= {self.max_}')
            except TypeError as e:
                raise TypeError(f"{type(self).desc_} doesn't support assignment of {type(v)}")
            self.n_ = int(v*self.divisor_)


class struct(btype):
    def __init__(self, name_:str = None, fields_:list = None, **fields):
        self.name_ = name_ or type(self).__name__
        self.fields_ = (fields_ or list()) + list(fields.items())
        self.size_ = sum(f.size_ for _,f in self.fields_)
        self.repr_ = f"struct(name_='{self.name_}', fields_={fields})"
        
    def allocate_(self, name:str='_root', parent:unbound_field=None, offset:int=0) -> unbound_field:
        '''allocate a field recursively'''
        ftype = super().allocate_(name, parent, offset)
        z = offset

        for fname, ft in reversed(self.fields_):
            if fname.endswith('_'):
                raise ValueError(f'Field names must not end with _: {fname}')
            
            setattr(ftype, fname, ft.allocate_(f'{name}.{fname}', ftype, z))
            z += ft.size_

        return ftype
    
    class mixin_field_(field):

        @property
        def v_(self) -> dict:
            d = {}
            for k, t in self.btype_.fields_:
                d[k] = getattr(self, k).v_
            return d
            
        @v_.setter        
        def v_(self, v:Union[int, dict]):
            if isinstance(v, dict):
                for k, fv in v.items():
                    setattr(self, k, fv)
            else:
                self.n_ = v

        def __iter__(self): 
            for k, t in self.btype_.fields_:
                yield k

        def __getitem__(self, k):
            if isinstance(k, str):
                try:
                    return getattr(self, k)
                except AttributeError as e:
                    if is_identifier(k):
                        raise KeyError(f'{type(self)} does not have field "{k}"') from e

                f=self.expr_field_(k)(self)
                return f
            else:
                raise TypeError(f'{k.btype_.__name__} fields do not support {type(k).__name__} indices')

class array(struct):
    '''array'''
    
    def __init__(self, etype: btype, dim:int):
        self.etype_ = etype
        self.dim_ = dim
        self.size_ = etype.size_*dim
        self.repr_ = f"{etype}[{dim}]"
        self.fields_ = tuple((f'_{i}',  etype) for i in range(dim))
        self.name_ = type(self).__name__
        
    class mixin_field_(struct.mixin_field_):
        @property
        def v_(self) -> list:
            return [self[i].v_ for i in range(self.btype_.dim_)]
            
        @v_.setter        
        def v_(self, v:Union[int, list, tuple]):
            if isinstance(v, int):
                self.n_ = v
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
        self.atype_ = atype
        self.etype_ = atype.etype_
        self.slice_ = aslice
        self.islice_ = list(range(*aslice.indices(atype.dim_)))
        self.dim_ = len(self.islice_)
        self.size_ = self.etype_.size_*self.dim_
        self.repr_ = f"{atype}[{aslice}]"
        self.name_ = type(self).__name__

    def allocate_(self, name:str, parent:unbound_field, offset:int=0) -> unbound_field:
        '''allocate a field recursively'''
        ftype = btype.allocate_(self, name, parent, offset)

        for i,j in enumerate(self.islice_):
            setattr(ftype, f'_{i}', parent[j])

        return ftype
            


class fn_type(btype):
    def __init__(self, fn: Callable[[int], Any], expr: str):
        self.fn_ = fn
        self.size_ = 0
        self.repr_ = f"fn_type({fn})"        
        self.name_ = type(self).__name__

        
    class mixin_field_(field):
        @property
        def v_(self) -> Any:
            return self.fn_(self.target_[0])

        @property
        def n_(self) -> int:
            return int(self.v_)


class BTypesTest(unittest.TestCase):
    def test_simple(self):
        u4t = uint(4) # type
        u4 = u4t() # bound field
        u4.n_ = 3 # raw int value

        self.assertEqual(repr(u4t), 'uint(4)')
        self.assertEqual(repr(u4), '<3>')
        self.assertEqual(u4.n_, 3)
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
        foo = struct(fields_=[
            ("a", uint(3)),
            ("b", uint(4)),
        ])
        
        bar = struct(
            f = foo, # array of 10 foo elements
            c = uint(5),
        )
        
        foobar = struct(
            a = uint(3, enum_={"alpha":0, "beta":1, "gamma":2}),  # 3 bit integer with enum
            b = sint(4), # 4 bit integer
            bars = bar[5], # array of 5 bars
        )
        
        f = foobar(0)
        f.a = 'beta'
        f.b = -1
        print (f"f['b'] = {f['b']}")

        self.assertEqual(f.b, -1)
        
        with self.assertRaises(KeyError):
            f['c']
            
        with self.assertRaises(AttributeError):
            f.c
        
    def test_decimal(self):
        foo = decimal(16, 2)(123.45)
        
        self.assertEqual(foo, 123.45)
        self.assertEqual(foo.n_, 12345)
        self.assertEqual(foo+1.0, 124.45)

    def test_expr(self):
        foo = struct('foo',
            a = uint(3),
            b = uint(4),
        )()
        
        self.assertEqual(foo.a.expr_(), '(n >> 4 & 0x7)')
        self.assertEqual(foo.b.expr_(), '(n & 0xf)')
        
        ab = foo['a * b']
        
        foo.a = 5
        foo.b = 11
        
        self.assertEqual(foo.a, 5)
        self.assertEqual(ab, 55)
        
        self.assertEqual(ab.expr_(), '(n >> 4 & 0x7) * (n & 0xf)')
        self.assertEqual(ab.expr_(), '(n >> 4 & 0x7) * (n & 0xf)')
        


__all__ = list(set([x for x in locals().keys() if not x.startswith('_')]) - _all_above_excluded)
