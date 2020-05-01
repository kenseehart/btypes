'''btypes.expressions: Support for high-performance expression processing

The core btypes model is based on python's unbound integers, so by design there is intentionally no concept of word size. However, the rest of the world deals in 32 bit and 64 bit integers.

The primary purpose of the expressions module is to interface with tools built on C/C++, etc., where wide interface data are typically expressed as an array of native integers.

The expressions provided by this module are valid syntax in C/C++ as well as python, and can be used in numpy, scipy, and related tools, or to generate C/C++ code directly.

Also, within pure python, expressions can be recompiled as closed form bitwise expressions on unbounded integers for improved performance. Use default word_size=0 for unbounded integers.

The expressions always represent a function of 'n', the raw interface record. If word_size==0, n is int, not divided into words. If word_size>0, n is int[], an array of unsigned integers of the specified size.

The expression may evaluate to either signed or unsigned integers. It is up to the client to choose appropriate type to consume the result.

Although btypes has no third party requirements, the features supported by this submodule require libcst: pip install libcst


Copyright 2020, Ken Seehart
MIT License
https://github.com/kenseehart/btypes
'''

from typing import Callable

from libcst import *

def cst_ni(i: int) -> CSTNode:
    '''
    n[{i}]
    '''
    return Subscript(
        value=Name(value='n'),
        slice=[
            SubscriptElement(slice=Index(value=Integer(value='0'))),
        ])

def cst_shift_and(node: CSTNode, offset: int, mask: int=-1) -> CSTNode:
    '''
    ({node} >> 7 & 0x1f)
    '''

    if offset:
        lnode = BinaryOperation(
            left=node,
            operator=RightShift(),
            right=Integer(value=str(offset)),
        )
    else:
        lnode = node

    if mask==-1:
        return lnode
    else:
        return BinaryOperation(
            left=lnode,
            operator=BitAnd(),
            right=Integer(hex(mask)),
            lpar=[LeftParen()],
            rpar=[RightParen()],
        )

def cst_or(n0: CSTNode, n1: CSTNode) -> CSTNode:
    '''
    ({n0} | {n1})
    '''
    return BinaryOperation(
        left=n0,
        operator=BitOr(),
        right=n1,
        lpar=[LeftParen()],
        rpar=[RightParen()],
    )


def cst_uint(offset: int, mask: int, word_size: int=0) -> CSTNode:
    '''return a cst node for a uint field

    :param offset: bit offset
    :param mask: bit mask
    :param word_size: native word size in bits (default 0 means unlimited size, suitable for python expressions)

    example: ((n[5]>>7)&0x3f)
    '''

    if word_size:
        if mask > 2**word_size-1:
            raise ValueError('Expression not supported: field expression exceeds word_size')

        j = offset // word_size
        k = offset % word_size
        m1 = mask >> word_size*(j+1)-offset

        if m1: # span two words
            n0 = cst_shift_and(cst_ni(j), k)
            n1 = cst_shift_and(cst_ni(j), 0, mask)
            return cst_or(n0, n1)
        else:
            return cst_shift_and(cst_ni(j), offset, mask)
    else:
        return cst_shift_and(Name(value='n'), offset, mask)
    

class NameTransformer(CSTTransformer):
    def __init__(self, resolver:Callable[[str], CSTNode]):
        self.resolver = resolver

    def leave_Name(self, original_node: Name, updated_node: Name) -> CSTNode:
        return self.resolver(original_node.value)

class NameTransformer(CSTTransformer):
    def __init__(self, resolver:Callable[[str], CSTNode]):
        self.resolver = resolver

    def leave_Name(self, original_node: Name, updated_node: Name) -> CSTNode:
        return self.resolver(original_node.value)


#visitor = TypingCollector()
#stub_tree.visit(visitor)
#transformer = TypingTransformer(visitor.annotations)
#modified_tree = source_tree.visit(transformer)

def cst_expr(expr: str, resolver: Callable[[str], CSTNode], word_size: int=0) -> CSTNode:
    '''return a cst node for a expression

    :param str: expression in field namespace to be translated
    :param resolver: callback function to evaluate a name as a CSTNode
    :param word_size: native word size in bits (default 0 means unlimited size, suitable for python expressions)

    '''
    
    cst = parse_expression(expr)
    visitor = NameTransformer(resolver)
    new_cst = cst.visit(visitor)
    return new_cst
   
def is_identifier(expr):
    cst = parse_expression(expr)
    return isinstance(cst, Name)
    
    
def cst_source_code(cst: CSTNode) -> str:
    '''return source code for a node'''
    return Module(body=[cst]).code


    
