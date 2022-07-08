"""
btypes.numduck

Numberic duck typing for btypes fields

Copyright 2020, Ken Seehart
MIT License
"""


class IntDuck:
    '''Implement integer emulation. Define __int__() and IntDuck does the rest.
    Integer behavior supercedes enum_, including ordering.
    Not suitable for floating point
    '''
    
    def __index__(self):
        return int(self)
    
    def __add__(self, other):
        return int(self) + other

    def __radd__(self, other):
        return other + int(self)

    def __iadd__(self, other):
        self.n_ += other
        return self

    def __mul__(self, other):
        return int(self) * other

    def __rmul__(self, other):
        return other * int(self)

    def __imul__(self, other):
        self.n_ = int(self) * other
        return self

    def __sub__(self, other):
        return int(self) - other

    def __rsub__(self, other):
        return other - int(self)

    def __isub__(self, other):
        self.n_ -= other
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
        self.n_ = int(self) // other
        return self    
    
    def __and__(self, other):
        return self.n_ & other
        
    def __rand__(self, other):
        return other & self.n_
        
    def __iand__(self, other):
        self.n_ &= other
        return self

    def __or__(self, other):
        return self.n_ | other
        
    def __ror__(self, other):
        return other | self.n_

    def __ior__(self, other):
        self.n_ |= other
        return self

    def __rshift__(self, other):
        return self.n_ >> other
    
    def __rrshift__(self, other):
        return other >> self.n_ 
    
    def __irshift__(self, other):
        self.n_ >>= other
        return self
    
    def __lshift__(self, other):
        return self.n_ << other
    
    def __rlshift__(self, other):
        return other << self.n_ 
    
    def __ilshift__(self, other):
        self.n_ <<= other
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
    '''Implement numeric emulation, where self.v_ is expected to be numeric.
    Not suitable for enums.
    '''
    
    def __add__(self, other):
        return self.v_ + other

    def __radd__(self, other):
        return other + self.v_

    def __iadd__(self, other):
        self.v_ += other
        return self

    def __mul__(self, other):
        return self.v_ * other

    def __rmul__(self, other):
        return other * self.v_

    def __imul__(self, other):
        self.v_ *= other
        return self

    def __sub__(self, other):
        return self.v_ - other

    def __rsub__(self, other):
        return other - self.v_

    def __isub__(self, other):
        self.v_ -= other
        return self

    def __div__(self, other):
        return self.v_ / other

    def __rdiv__(self, other):
        return other / self.v_

    def __idiv__(self, other):
        self.v /= other
        return self.v

    def __floordiv__(self, other):
        return self.v_ // other

    def __rfloordiv__(self, other):
        return other // self.v_

    def __ifloordiv__(self, other):
        self.v_ //= other
        return self    
    
    def __lt__(self, other):
        return self.v_ < other

    def __gt__(self, other):
        return self.v_ > other
    
    def __le__(self, other):
        return self.v_ <= other
    
    def __ge__(self, other):
        return self.v_ >= other




