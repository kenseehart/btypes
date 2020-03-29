import unittest
from typing import Union
from collections import defaultdict

class IntDuck:
    '''Implement integer emulation. Define __int__() and IntDuck does the rest.'''
    
    def __index__(self):
        return int(self)
    
    def __add__(self, other):
        return int(self) + other

    def __radd__(self, other):
        return other + int(self)

    def __iadd__(self, other):
        self._n = int(self) + other
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
        self._n = int(self) - other
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
    
    


class field(type):
    '''Unbound field implementing propery protocol'''
    def __repr__(self):
        return self.__name__

    def __get__(self, instance, owner):
        if instance is None: # unbound field
            return self
        else:
            return self(instance._target) # return the binding of this field to the target

    def __set__(self, instance, value):
        self._btype._set_field_value(self(instance._target), value)

class bound_field(IntDuck, metaclass=field):
    '''Bound field'''
    def __init__(self, target:Union[int, list]=0):
        '''bind a field to a target list consisting of a single integer'''
        if isinstance(target, int):
            self._target = [target]
        elif isinstance(target, list):
            self._target = target
        else:
            raise TypeError(f'{type(self)} initializer must be int or list of one int')

    def __repr__(self):
        return repr(self._btype._get_field_value(self))
    
    @property
    def _n(self) -> int:
        return (self._target[0] >> self._offset) & self._mask
        
    @_n.setter        
    def _n(self, n:int):
        self._target[0] = self._target[0] & ~(self._mask << self._offset) | ((n&self._mask) << self._offset)

    # comparison
    def __eq__(self, other):
        if isinstance(other, int):
            return int(self)==other

        if isinstance(other, str):
            return repr(self)==other

        if isinstance(other, bound_field):
            return int(self)==int(other)
        
        return int(self) == self._btype._encode(other)
        
    def __int__(self): # may be overloaded (e.g. sint support for negatives)
        return self._n


class btype:
    '''Base class for type classes'''
    def __call__(self, name, value=None):
        mf = self._allocate(name, 0)
        if value is None:
            return mf
        else:
            f = mf([0])
            self._set_field_value(f, value)
            return f
        
    def _allocate(self, name, offset=0) -> bound_field:
        ftype = field(name, (type(self)._mixin,), {})
        ftype._size = self._size
        ftype._mask = ((1<<self._size)-1)
        ftype._offset = offset
        ftype._btype = self
        return ftype

    def _get_field_value(self, f:bound_field):
        return f._n
    
    def _set_field_value(self, f:bound_field, v:int):
        f._n = int(v)

    _get_field_int = _get_field_value

    def _render(self, f):
        return str(self._get_field_value(f))  
    
    def __repr__(self):
        return self._repr
    
    class _mixin(bound_field):
        '''overload class _mixin in btype derived class to extend the bound_field'''
        pass

    
class struct(btype):
    def __init__(self, *fields):
        self._fields = fields
        self._size = sum(f._size for _,f in fields)
        self._repr = f"struct{fields}"
        
    def _allocate(self, name:str, offset:int=0) -> field:
        '''allocate a field recursively'''
        ftype = super()._allocate(name, offset)
        z = offset
        for fname, ft in reversed(self._fields):
            setattr(ftype, fname, ft._allocate(f'{name}.{fname}', z))
            z += ft._size
                    
        return ftype
    
    def _get_field_value(self, f):
        d = {}
        for k, t in self._fields:
            d[k] = t._get_field_value(getattr(f, k))
        return d

    def _set_field_value(self, f:bound_field, v:Union[int, dict]):
        if isinstance(v, dict):
            for k, fv in v.items():
                setattr(f, k, fv)
        else:
            super()._set_field_value(f, v)

    def __repr__(self):
        return self._repr
    
class uint(btype):
    '''unsigned integer with optional enum'''

    def __init__(self, size:int, _enum=None):
        self._size = size
        self._repr = f"uint({size})"
        self._enum = _enum or {}
        self._renum = {v:k for k,v in self._enum.items()}
        
    def _set_field_value(self, f:bound_field, v:Union[int, str]):
        if isinstance(v, str):
            try:
                v = self._enum[v]
            except KeyError:
                try:
                    v = int(v)
                except ValueError:
                    raise ValueError(f'{f}: undefined enum {v}')
                
        super()._set_field_value(f, v)

    def _get_field_value(self, f:bound_field):
        v = int(f)
        try:
            v = self._renum[v] # defaults to raw int if enum is not defined
        except KeyError:
            pass
        return v

    class _mixin(bound_field):
        #def _get(self):
        #def _set(self, v):
            
        def __str__(self):
            pass
            
            #v = self._get_field_value(...)


class sint(uint):
    '''signed integer with optional enum'''

    class _mixin(uint._mixin):
        def __int__(self):
            v = self._n
            if v&(1<<(self._size-1)):
                v = v - (1<<(self._size))
            return v

class array(btype):
    pass


class StructTest(unittest.TestCase):
    def test_simple(self):
        u4t = uint(4) # type
        u4f = u4t._allocate('u4', 2) # unbound field
        u4 = u4f([0]) # bound field
        u4._n = 3 # raw int value

        self.assertEqual(repr(u4t), 'uint(4)')
        self.assertEqual(repr(u4f), 'u4')
        self.assertEqual(repr(u4), '3')
        self.assertEqual(u4._n, 3)
        self.assertEqual(u4, 3)
        self.assertEqual(u4._target[0], 12)
        u4 += 2
        self.assertEqual(u4, 5)
        u4 *= 2
        self.assertEqual(u4, 10)
        u4 //= 2
        self.assertEqual(u4, 5)

        with self.assertRaises(TypeError):
            u4 /= 2
            
        class Z:
            u4 = u4f
            
        z = Z()
        z._target = u4._target
        self.assertEqual(type(z.u4), u4f)
        z.u4 = 1
        self.assertEqual(type(z.u4), u4f)
        self.assertEqual(z.u4, 1)
        
    def test_struct(self):
        foo = struct(
            ("a", uint(3)),
            ("b", uint(4)),
        )
        
        bar = struct(
            ("f", foo), # array of 10 foo elements
            ("c", uint(5)),
            #("shoe", array(uint(6), 208)), # 4 deck shoe
        )
        
        foo1 = foo._allocate('foo')([1])
        print(foo1)
            
        b = bar._allocate('bar')
        b0 = b([0])
        print(b0)

        
        foo = struct(
            ("a", uint(3, _enum={"alpha":0, "beta":1, "gamma":2})),  # 3 bit integer with enum
            ("b", sint(4)), # 4 bit integer
        )
        
        f = foo('f')(0)
        f.a = 'beta'
        f.b = -1
        
        print (f)
        
            
