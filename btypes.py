import unittest
from typing import Union, Any

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
        self(instance._target)._v = value

    def __getitem__(self, k):
        if isinstance(k, int):
            k = f'_{k}' # array elements as field property instances
            
        return getattr(self, k)
    

class bound_field(IntDuck, metaclass=field):
    '''Bound field'''
    _offset:int
    _mask:int
    __slots__ = ('_target',)
    
    def __init__(self, target:Union[int, list]=0):
        '''bind a field to a target list consisting of a single integer'''
        if isinstance(target, int):
            self._target = [target]
        elif isinstance(target, list):
            self._target = target
        else:
            raise TypeError(f'{type(self)} initializer must be int or list of one int')
        
    def __repr__(self):
        return repr(self._v)
    
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
            

class btype:
    '''Base class for type classes'''
    _repr:str
    _size:int
    
    def __call__(self, name, value:Any=None):
        mf = self._allocate(name, 0)
        if value is None:
            return mf
        else:
            f = mf([0])
            f._v = value
            return f
        
    def _allocate(self, name, offset:int=0) -> bound_field:
        ftype = field(name, (type(self)._mixin,), {})
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
        def _v(self) -> dict:
            v = int(self)
            try:
                v = self._btype._renum[v] # defaults to raw int if enum is not defined
            except KeyError:
                pass
            return v
            
        @_v.setter        
        def _v(self, v:Union[int, dict]):
        
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
        
        
class struct(btype):
    def __init__(self, *fields):
        self._fields = fields
        self._size = sum(f._size for _,f in fields)
        self._repr = f"struct{fields}"
        
    def _allocate(self, name:str, offset:int=0) -> field:
        '''allocate a field recursively'''
        ftype = super()._allocate(name, offset)
        z = offset

        for fname, ft in reversed(self._fields.items()):
            setattr(ftype, fname, ft._allocate(f'{name}.{fname}', z))
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

        def __len__(self): 
            return len(self._btype._fields)
      
        def __iter__(self): 
            for k, t in self._btype._fields:
                yield k

        def __getitem__(self, k):
            if isinstance(k, int):
                k = f'_{k}' # array elements as field property instances            

            return getattr(self, k)

    


class array(struct):
    '''array'''
    def __init__(self, etype: btype, dim:int):
        self._etype = etype
        self._dim = dim
        self._size = etype._size*dim
        self._repr = f"{etype}[{dim}]"
        self._fields = {f'_{i}': etype for i in range(dim)}
        
    class _mixin(struct._mixin):
        @property
        def _v(self) -> list:
            return [self[i] for i in range(self._btype._dim)]
            
        @_v.setter        
        def _v(self, v:Union[int, list, tuple]):
            if isinstance(v, (list, tuple)):
                for i, fv in enumerate(v):
                    setattr(self, f'_{i}', fv)
            elif isinstance(v, int):
                self._n = v
            
            
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
        
        bats = uint(5)[3]('bats')
        b = bats(0)
        b[0]=3
        b[1]=2
        print (b)
        
        
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
            ("bars", array(bar, 5)),
        )
        
       
        f = foo('foo')(0)
        f.a = 'beta'
        f.b = -1
        
        print (f)
        
            
