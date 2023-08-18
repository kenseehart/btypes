import os
from btypes import enum, uint, unbound_field, field

from pyverilog.vparser.parser import parse

filelist = ['example.v']

os.environ['PYVERILOG_IVERILOG'] = r'C:\iverilog\bin\iverilog.exe'

ast, directives = parse(filelist)
                        #preprocess_include=options.include,
                        #preprocess_define=options.define)

ast.show()

