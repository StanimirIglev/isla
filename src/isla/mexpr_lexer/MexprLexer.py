# Generated from MexprLexer.g4 by ANTLR 4.11.1
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
    from typing import TextIO
else:
    from typing.io import TextIO


def serializedATN():
    return [
        4,0,11,86,6,-1,6,-1,6,-1,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,
        2,5,7,5,2,6,7,6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,
        7,12,1,0,1,0,1,0,1,0,1,1,1,1,1,1,1,1,1,2,4,2,39,8,2,11,2,12,2,40,
        1,3,4,3,44,8,3,11,3,12,3,45,1,3,1,3,1,4,1,4,1,4,1,4,1,5,1,5,1,5,
        5,5,57,8,5,10,5,12,5,60,9,5,1,6,3,6,63,8,6,1,7,1,7,1,8,1,8,1,9,1,
        9,1,10,4,10,72,8,10,11,10,12,10,73,1,10,1,10,1,11,1,11,1,11,1,11,
        1,12,4,12,83,8,12,11,12,12,12,84,0,0,13,3,1,5,2,7,3,9,4,11,5,13,
        6,15,0,17,0,19,7,21,8,23,9,25,10,27,11,3,0,1,2,4,2,0,91,91,123,123,
        4,0,45,46,65,90,95,95,97,122,3,0,9,10,13,13,32,32,1,0,93,93,87,0,
        3,1,0,0,0,0,5,1,0,0,0,0,7,1,0,0,0,0,9,1,0,0,0,1,11,1,0,0,0,1,13,
        1,0,0,0,1,19,1,0,0,0,1,21,1,0,0,0,1,23,1,0,0,0,2,25,1,0,0,0,2,27,
        1,0,0,0,3,29,1,0,0,0,5,33,1,0,0,0,7,38,1,0,0,0,9,43,1,0,0,0,11,49,
        1,0,0,0,13,53,1,0,0,0,15,62,1,0,0,0,17,64,1,0,0,0,19,66,1,0,0,0,
        21,68,1,0,0,0,23,71,1,0,0,0,25,77,1,0,0,0,27,82,1,0,0,0,29,30,5,
        123,0,0,30,31,1,0,0,0,31,32,6,0,0,0,32,4,1,0,0,0,33,34,5,91,0,0,
        34,35,1,0,0,0,35,36,6,1,1,0,36,6,1,0,0,0,37,39,8,0,0,0,38,37,1,0,
        0,0,39,40,1,0,0,0,40,38,1,0,0,0,40,41,1,0,0,0,41,8,1,0,0,0,42,44,
        5,10,0,0,43,42,1,0,0,0,44,45,1,0,0,0,45,43,1,0,0,0,45,46,1,0,0,0,
        46,47,1,0,0,0,47,48,6,3,2,0,48,10,1,0,0,0,49,50,5,125,0,0,50,51,
        1,0,0,0,51,52,6,4,3,0,52,12,1,0,0,0,53,58,3,15,6,0,54,57,3,15,6,
        0,55,57,3,17,7,0,56,54,1,0,0,0,56,55,1,0,0,0,57,60,1,0,0,0,58,56,
        1,0,0,0,58,59,1,0,0,0,59,14,1,0,0,0,60,58,1,0,0,0,61,63,7,1,0,0,
        62,61,1,0,0,0,63,16,1,0,0,0,64,65,2,48,57,0,65,18,1,0,0,0,66,67,
        5,62,0,0,67,20,1,0,0,0,68,69,5,60,0,0,69,22,1,0,0,0,70,72,7,2,0,
        0,71,70,1,0,0,0,72,73,1,0,0,0,73,71,1,0,0,0,73,74,1,0,0,0,74,75,
        1,0,0,0,75,76,6,10,2,0,76,24,1,0,0,0,77,78,5,93,0,0,78,79,1,0,0,
        0,79,80,6,11,3,0,80,26,1,0,0,0,81,83,8,3,0,0,82,81,1,0,0,0,83,84,
        1,0,0,0,84,82,1,0,0,0,84,85,1,0,0,0,85,28,1,0,0,0,10,0,1,2,40,45,
        56,58,62,73,84,4,5,1,0,5,2,0,6,0,0,4,0,0
    ]

class MexprLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    VAR_DECL = 1
    OPTIONAL = 2

    BRAOP = 1
    OPTOP = 2
    TEXT = 3
    NL = 4
    BRACL = 5
    ID = 6
    GT = 7
    LT = 8
    WS = 9
    OPTCL = 10
    OPTTXT = 11

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE", "VAR_DECL", "OPTIONAL" ]

    literalNames = [ "<INVALID>",
            "'{'", "'['", "'}'", "'>'", "'<'", "']'" ]

    symbolicNames = [ "<INVALID>",
            "BRAOP", "OPTOP", "TEXT", "NL", "BRACL", "ID", "GT", "LT", "WS", 
            "OPTCL", "OPTTXT" ]

    ruleNames = [ "BRAOP", "OPTOP", "TEXT", "NL", "BRACL", "ID", "ID_LETTER", 
                  "DIGIT", "GT", "LT", "WS", "OPTCL", "OPTTXT" ]

    grammarFileName = "MexprLexer.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.11.1")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


