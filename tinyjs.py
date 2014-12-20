"""
  tinyjs.py
  ~~~~~~~~~

  simple file javascript interpreter

  :author: atupal
  :email: me@atupal.org
  :time: 12/9/2014
"""

from StringIO import StringIO

from utils import *

TINYJS_H = 1
TINYJS_CALL_STACK = 1
_CRTDBG_MAP_ALLOC = 1

TRACE = 'printf'

TINYJS_LOOP_MAX_ITERATIONS = 8192

s_null = "null"
s_undefined = "undefined"

def TRACE(x):
  print x

def CLEAN(x):
  __v = x
  if __v and not __v.owned:
    del __v

def CREATE_LINK(LINK, VAR):
  import inspect
  import re
  import ast
  import ctypes
  stack = inspect.stack()
  stack_pre = stack[1]
  function_call_string = ';'.join( stack_pre[4] ).strip('\n')
  ret = re.search(r'(%s[ ]*\(.*\))' % CREATE_LINK.func_name, function_call_string)
  striped_function_call_string = ret.group()
  parser = ast.parse(striped_function_call_string)

  function_actual_args = parser.body[0].value.args
  first_arg_name = function_actual_args[0].id

  frame = inspect.currentframe()

  if not LINK or LINK.owned:
    # LINK = CScriptVarLink(VAR)
    iter_frame = frame.f_back
    while iter_frame:
      if first_arg_name in iter_frame.f_locals:
        # make the modify of f_locals(not current frame) permanently
        iter_frame.f_locals[first_arg_name] = CScriptVarLink(VAR)
        ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(iter_frame), ctypes.c_int(0))
        break
  else:
    LINK.replaceWith(VAR)

def ASSERT(x):
  assert(x)

CURR_INT=256
def NEXT_INT():
  global CURR_INT
  CURR_INT += 1
  return CURR_INT

class LEX_TYPES(object):
  LEX_EOF = 0
  LEX_ID =256
  LEX_INT = NEXT_INT()
  LEX_FLOAT = NEXT_INT()
  LEX_STR = NEXT_INT()

  LEX_EQUAL = NEXT_INT()
  LEX_TYPEEQUAL = NEXT_INT()
  LEX_NEQUAL = NEXT_INT()
  LEX_NTYPEEQUAL = NEXT_INT()
  LEX_LEQUAL = NEXT_INT()
  LEX_LSHIFT = NEXT_INT()
  LEX_LSHIFTEQUAL = NEXT_INT()
  LEX_GEQUAL = NEXT_INT()
  LEX_RSHIFT = NEXT_INT()
  LEX_RSHIFTUNSIGNED = NEXT_INT()
  LEX_RSHIFTEQUAL = NEXT_INT()
  LEX_PLUSEQUAL = NEXT_INT()
  LEX_MINUSEQUAL = NEXT_INT()
  LEX_PLUSPLUS = NEXT_INT()
  LEX_MINUSMINUS = NEXT_INT()
  LEX_ANDEQUAL = NEXT_INT()
  LEX_ANDAND = NEXT_INT()
  LEX_OREQUAL = NEXT_INT()
  LEX_OROR = NEXT_INT()
  LEX_XOREQUAL = NEXT_INT()

  #reserved words
  #define LEX_R_LIST_START LEX_R_IF
  LEX_R_LIST_START = -1
  LEX_R_IF = NEXT_INT()
  LEX_R_ELSE = NEXT_INT()
  LEX_R_DO = NEXT_INT()
  LEX_R_WHILE = NEXT_INT()
  LEX_R_FOR = NEXT_INT()
  LEX_R_BREAK = NEXT_INT()
  LEX_R_CONTINUE = NEXT_INT()
  LEX_R_FUNCTION = NEXT_INT()
  LEX_R_RETURN = NEXT_INT()
  LEX_R_VAR = NEXT_INT()
  LEX_R_TRUE = NEXT_INT()
  LEX_R_FALSE = NEXT_INT()
  LEX_R_NULL = NEXT_INT()
  LEX_R_UNDEFINED = NEXT_INT()
  LEX_R_NEW =NEXT_INT()

  LEX_R_LIST_END = NEXT_INT() # always the last entry

LEX_TYPES.LEX_R_LIST_START = LEX_TYPES.LEX_R_IF


class SCRIPTVAR_FLAGS(object):
    SCRIPTVAR_UNDEFINED   = 0
    SCRIPTVAR_FUNCTION    = 1
    SCRIPTVAR_OBJECT      = 2
    SCRIPTVAR_ARRAY       = 4
    SCRIPTVAR_DOUBLE      = 8  # floating point double
    SCRIPTVAR_INTEGER     = 16 # integer number
    SCRIPTVAR_STRING      = 32 # string
    SCRIPTVAR_NULL        = 64 # it seems null is its own data type

    SCRIPTVAR_NATIVE      = 128 # to specify this is a native function
    SCRIPTVAR_NUMERICMASK = SCRIPTVAR_NULL |\
                            SCRIPTVAR_DOUBLE |\
                            SCRIPTVAR_INTEGER
    SCRIPTVAR_VARTYPEMASK = SCRIPTVAR_DOUBLE |\
                            SCRIPTVAR_INTEGER |\
                            SCRIPTVAR_STRING |\
                            SCRIPTVAR_FUNCTION |\
                            SCRIPTVAR_OBJECT |\
                            SCRIPTVAR_ARRAY |\
                            SCRIPTVAR_NULL

TINYJS_RETURN_VAR = "return"
TINYJS_PROTOTYPE_CLASS = "prototype"
TINYJS_TEMP_NAME = "tmp_name"
TINYJS_BLANK_DATA = ""

class CScriptException(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class CScriptLex(object):

  # for debug:
  def _dump(self):
    return vars(self)
  # end for debug

  # all member variables
  def __initAllVars__(self):
    self.currCh = None
    self.nextCh = None
    self.tk = None # The type of the token that we have
    self.tokenStart = None # Position in the data at the beginning of the token we have here
    self.tokenEnd = None # Position in the data at the last character of the token we have here
    self.tokenLastEnd = None # Position in the data at the last character of the last token
    self.tkStr = None # Data contained in the token we have here
    self.data = None # Data string to get tokens from
    self.dataStart = None
    self.dataEnd = None # Start and end position in data string
    self.dataOwned = None # Do we own this data string?
    self.dataPos = None # Position in data (we CAN go past the end of the string here)

  # public method
  def __init__(self, *args):
    self.__initAllVars__()
    if len(args) == 3 and\
        isinstance(args[0], CScriptLex) and\
        isinstance(args[1], (int, long)) and\
        isinstance(args[2], (int, long)):
      owner = args[0]
      startChar = args[1]
      endChar = args[2]
      """   /* When we go into a loop, we use getSubLex to get a lexer for just the sub-part of the
             relevant string. This doesn't re-allocate and copy the string, but instead copies
             the data pointer and sets dataOwned to false, and dataStart/dataEnd to the relevant things. */
      """
      self.data = owner.data
      self.dataOwned = False
      self.dataStart = startChar
      self.dataEnd = endChar
    elif len(args) == 1 and\
        isinstance(args[0], basestring):
      input = args[0]
      self.data = input
      self.dataOwned = True
      self.dataStart = 0
      self.dataEnd = len(self.data)
    self.reset()

  def __del__(self):
    pass

  def match(self, expected_tk):
    """Lexical match wotsit

    raise CScriptException
    """

    if self.tk != expected_tk:
      errorString = StringIO()
      print >>errorString, 'Got', self.getTokenStr(self.tk), 'expected' , self.getTokenStr(expected_tk),\
            'at', self.getPosition(self.tokenStart),
      raise CScriptException(errorString.getvalue())

    self.getNextToken()

  @classmethod
  def getTokenStr(cls, token):
    """ Get the string representation of the given token
    """

    if token > 32 and token < 128: return "'%s'" % chr(token)
    if token == LEX_TYPES.LEX_EOF : return "EOF";
    if token == LEX_TYPES.LEX_ID : return "ID";
    if token == LEX_TYPES.LEX_INT : return "INT";
    if token == LEX_TYPES.LEX_FLOAT : return "FLOAT";
    if token == LEX_TYPES.LEX_STR : return "STRING";
    if token == LEX_TYPES.LEX_EQUAL : return "==";
    if token == LEX_TYPES.LEX_TYPEEQUAL : return "===";
    if token == LEX_TYPES.LEX_NEQUAL : return "!=";
    if token == LEX_TYPES.LEX_NTYPEEQUAL : return "!==";
    if token == LEX_TYPES.LEX_LEQUAL : return "<=";
    if token == LEX_TYPES.LEX_LSHIFT : return "<<";
    if token == LEX_TYPES.LEX_LSHIFTEQUAL : return "<<=";
    if token == LEX_TYPES.LEX_GEQUAL : return ">=";
    if token == LEX_TYPES.LEX_RSHIFT : return ">>";
    if token == LEX_TYPES.LEX_RSHIFTUNSIGNED : return ">>>";
    if token == LEX_TYPES.LEX_RSHIFTEQUAL : return ">>=";
    if token == LEX_TYPES.LEX_PLUSEQUAL : return "+=";
    if token == LEX_TYPES.LEX_MINUSEQUAL : return "-=";
    if token == LEX_TYPES.LEX_PLUSPLUS : return "++";
    if token == LEX_TYPES.LEX_MINUSMINUS : return "--";
    if token == LEX_TYPES.LEX_ANDEQUAL : return "&=";
    if token == LEX_TYPES.LEX_ANDAND : return "&&";
    if token == LEX_TYPES.LEX_OREQUAL : return "|=";
    if token == LEX_TYPES.LEX_OROR : return "||";
    if token == LEX_TYPES.LEX_XOREQUAL : return "^=";
    # // reserved words
    if token == LEX_TYPES.LEX_R_IF : return "if";
    if token == LEX_TYPES.LEX_R_ELSE : return "else";
    if token == LEX_TYPES.LEX_R_DO : return "do";
    if token == LEX_TYPES.LEX_R_WHILE : return "while";
    if token == LEX_TYPES.LEX_R_FOR : return "for";
    if token == LEX_TYPES.LEX_R_BREAK : return "break";
    if token == LEX_TYPES.LEX_R_CONTINUE : return "continue";
    if token == LEX_TYPES.LEX_R_FUNCTION : return "function";
    if token == LEX_TYPES.LEX_R_RETURN : return "return";
    if token == LEX_TYPES.LEX_R_VAR : return "var";
    if token == LEX_TYPES.LEX_R_TRUE : return "true";
    if token == LEX_TYPES.LEX_R_FALSE : return "false";
    if token == LEX_TYPES.LEX_R_NULL : return "null";
    if token == LEX_TYPES.LEX_R_UNDEFINED : return "undefined";
    if token == LEX_TYPES.LEX_R_NEW : return "new";

    return "?[%d]" % ord(token)

  def reset(self):
    """ Reset this lex so we can start again
    """

    self.dataPos = self.dataStart
    self.tokenStart = 0
    self.tokenEnd = 0
    self.tokenLastEnd = 0
    self.tk = 0
    self.tkStr = ''
    self.getNextCh()
    self.getNextCh()
    self.getNextToken()

  def getSubString(self, lastPosition):
    """ Return a sub-string from the given position up until right now
    """

    lastCharIdx = self.tokenLastEnd+1
    if lastCharIdx < self.dataEnd:
      """
      /* save a memory alloc by using our data array to create the
         substring */
      """
      return self.data[lastPosition:lastCharIdx]
    else:
      return self.data[lastPosition:]

  def getSubLex(self, lastPosition):
    """ Return a sub-lexer from the given position up until right now
    """

    lastCharIdx = self.tokenLastEnd+1
    if lastCharIdx < self.dataEnd:
      return CScriptLex(self, lastPosition, lastCharIdx)
    else:
      return CScriptLex(self, lastPosition, self.dataEnd)

  def getPosition(self, pos=-1):
    """ Return a string representing the position in lines and columns of the character pos given
    """

    if pos<0: pos=self.tokenLastEnd
    line, col = 1, 1
    for i in xrange(pos):
      if i < self.dataEnd:
        ch = self.data[i]
      else:
        ch = chr(0)
      col += 1
      if ch=='\n':
        line+=1
        col = 0

    return '(line: %d, col: %d)' % (line, col)

  # protect method
  def getNextCh(self):
    self.currCh = self.nextCh
    if self.dataPos < self.dataEnd:
      self.nextCh = self.data[self.dataPos]
    else:
      self.nextCh = 0
    self.dataPos += 1

  def getNextToken(self):
    """ Get the text token from our text string
    """

    self.tk = LEX_TYPES.LEX_EOF
    self.tkStr = ''
    while self.currCh and isWhitespace(self.currCh):
      self.getNextCh()
    # newline comments
    if self.currCh == '/' and self.nextCh == '/':
      while self.currCh and self.currCh != '\n':
        self.getNextCh()
      self.getNextCh()
      self.getNextToken()
      return
    # block comments
    if self.currCh == '/' and self.nextCh == '*':
      while self.currCh and (self.currCh != '*' or self.nextCh != '/'):
        self.getNextCh()
      self.getNextCh()
      self.getNextCh()
      self.getNextToken()
      return;
    # record beginning of this token
    self.tokenStart = self.dataPos - 2
    # tokens
    if isAlpha(self.currCh):  # IDs
      while isAlpha(self.currCh) or isNumeric(self.currCh):
        self.tkStr += self.currCh
        self.getNextCh()
      self.tk = LEX_TYPES.LEX_ID
      if self.tkStr=="if": self.tk = LEX_TYPES.LEX_R_IF
      elif self.tkStr=="else": self.tk = LEX_TYPES.LEX_R_ELSE
      elif self.tkStr=="do": self.tk = LEX_TYPES.LEX_R_DO
      elif self.tkStr=="while": self.tk = LEX_TYPES.LEX_R_WHILE
      elif self.tkStr=="for": self.tk = LEX_TYPES.LEX_R_FOR
      elif self.tkStr=="break": self.tk = LEX_TYPES.LEX_R_BREAK
      elif self.tkStr=="continue": self.tk = LEX_TYPES.LEX_R_CONTINUE
      elif self.tkStr=="function": self.tk = LEX_TYPES.LEX_R_FUNCTION
      elif self.tkStr=="return": self.tk = LEX_TYPES.LEX_R_RETURN
      elif self.tkStr=="var": self.tk = LEX_TYPES.LEX_R_VAR
      elif self.tkStr=="true": self.tk = LEX_TYPES.LEX_R_TRUE
      elif self.tkStr=="false": self.tk = LEX_TYPES.LEX_R_FALSE
      elif self.tkStr=="null": self.tk = LEX_TYPES.LEX_R_NULL
      elif self.tkStr=="undefined": self.tk = LEX_TYPES.LEX_R_UNDEFINED
      elif self.tkStr=="new": self.tk = LEX_TYPES.LEX_R_NEW
    elif isNumeric(self.currCh):
      isHex = False
      if self.currCh == '0':
        self.tkStr += self.currCh
        self.getNextCh()
      if self.currCh == 'x':
        isHex = True
        self.tkStr += self.currCh
        self.getNextCh()
      self.tk = LEX_TYPES.LEX_INT
      while isNumeric(self.currCh) or (isHex and isHexadecimal(self.currCh)):
        self.tkStr += self.currCh
        self.getNextCh()
      if not isHex and self.currCh == '.':
        self.tk = LEX_TYPES.LEX_FLOAT
        self.tkStr += '.'
        self.getNextCh()
        while isNumeric(self.currCh):
          self.tkStr += self.currCh
          self.getNextCh()
      # do fancy e-style floating point
      if not isHex and (self.currCh == 'e' or self.currCh=='E'):
        self.tk = LEX_TYPES.LEX_FLOAT
        self.tkStr += self.currCh
        self.getNextCh()
        if self.currCh=='-':
          self.tkStr += self.currCh
          self.getNextCh()
        while isNumeric(self.currCh):
          self.tkStr += self.currCh
          self.getNextCh()
    elif self.currCh == '"':
      # strings...
      self.getNextCh()
      while self.currCh and self.currCh!='"':
        if self.currCh == '\\':
          self.getNextCh()
          if self.currCh == 'n' : self.tkStr += '\n'
          elif self.currCh == '"' : self.tkStr += '"'
          elif self.currCh == '\\': self.tkStr += '\\'
          else: self.tkStr += self.currCh
        else:
          self.tkStr += self.currCh
        self.getNextCh()
      self.getNextCh()
      self.tk = LEX_TYPES.LEX_STR
    elif self.currCh=='\'':
      # strings again...
      self.getNextCh()
      while self.currCh and self.currCh!='\'':
        if self.currCh == '\\':
          self.getNextCh()
          if self.currCh == 'n' : self.tkStr += '\n'
          elif self.currCh == 'a' : self.tkStr += '\a'
          elif self.currCh == 'r' : self.tkStr += '\r'
          elif self.currCh == 't' : self.tkStr += '\t'
          elif self.currCh == '\'' : self.tkStr += '\''
          elif self.currCh == '\\' : self.tkStr += '\\'
          elif self.currCh == 'x' :  # hex digits
            self.getNextCh()
            buf = self.currCh
            self.getNextCh()
            buf += self.currCh
            self.tkStr += chr(int(buf, 16))
          else:
            if self.currCh>='0' and self.currCh<='7':
              # octal digits
              buf = self.currCh
              self.getNextCh()
              buf += self.currCh
              self.getNextCh()
              buf += self.currCh
              self.tkStr += chr(int(buf, 8))
            else:
              self.tkStr += self.currCh
        else:
          self.tkStr += self.currCh
        self.getNextCh()
      self.getNextCh()
      self.tk = LEX_TYPES.LEX_STR
    else:
      # single chars
      self.tk = self.currCh
      if self.currCh: self.getNextCh()
      if self.tk=='=' and self.currCh=='=': # ==
        self.tk = LEX_TYPES.LEX_EQUAL
        self.getNextCh()
        if self.currCh=='=': # ===
          self.tk = LEX_TYPES.LEX_TYPEEQUAL
          self.getNextCh()
      elif self.tk=='!' and self.currCh=='=': # // !=
        self.tk = LEX_TYPES.LEX_NEQUAL
        self.getNextCh()
        if self.currCh=='=': # // !==
          self.tk = LEX_TYPES.LEX_NTYPEEQUAL
          self.getNextCh()
      elif self.tk=='<' and self.currCh=='=':
        self.tk = LEX_TYPES.LEX_LEQUAL
        self.getNextCh()
      elif self.tk=='<' and self.currCh=='<':
        self.tk = LEX_TYPES.LEX_LSHIFT
        self.getNextCh()
        if self.currCh=='=': # // <<=
          self.tk = LEX_TYPES.LEX_LSHIFTEQUAL
          self.getNextCh()
      elif self.tk=='>' and self.currCh=='=':
        self.tk = LEX_TYPES.LEX_GEQUAL
        self.getNextCh()
      elif self.tk=='>' and self.currCh=='>':
        self.tk = LEX_TYPES.LEX_RSHIFT
        self.getNextCh()
        if self.currCh=='=': # // >>=
          self.tk = LEX_TYPES.LEX_RSHIFTEQUAL
          self.getNextCh()
        elif self.currCh=='>': # // >>>
          self.tk = LEX_TYPES.LEX_RSHIFTUNSIGNED
          self.getNextCh()
      elif self.tk=='+' and self.currCh=='=':
        self.tk = LEX_TYPES.LEX_PLUSEQUAL
        self.getNextCh()
      elif self.tk=='-' and self.currCh=='=':
        self.tk = LEX_TYPES.LEX_MINUSEQUAL
        self.getNextCh()
      elif self.tk=='+' and self.currCh=='+':
        self.tk = LEX_TYPES.LEX_PLUSPLUS
        self.getNextCh()
      elif self.tk=='-' and self.currCh=='-':
        self.tk = LEX_TYPES.LEX_MINUSMINUS
        self.getNextCh()
      elif self.tk=='&' and self.currCh=='=':
        self.tk = LEX_TYPES.LEX_ANDEQUAL
        self.getNextCh()
      elif self.tk=='&' and self.currCh=='&':
        self.tk = LEX_TYPES.LEX_ANDAND
        self.getNextCh()
      elif self.tk=='|' and self.currCh=='=':
        self.tk = LEX_TYPES.LEX_OREQUAL
        self.getNextCh()
      elif self.tk=='|' and self.currCh=='|':
        self.tk = LEX_TYPES.LEX_OROR
        self.getNextCh()
      elif self.tk=='^' and self.currCh=='=':
        self.tk = LEX_TYPES.LEX_XOREQUAL
        self.getNextCh()

    # /* This isn't quite right yet */
    self.tokenLastEnd = self.tokenEnd
    self.tokenEnd = self.dataPos-3


class CScriptVarLink(object):

  # for debug:
  def _dump(self):
    return vars(self)
  # end for debug

  def __initAllVars__(self):
    self.name = None
    self.nextSibling = None
    self.prevSibling = None
    self.var = None
    self.owned = None

  # public
  def __init__(self, *args):
    self.__initAllVars__()
    if len(args) >= 1 and\
        isinstance(args[0], CScriptVar):
      if len(args) == 2 and isinstance(args[1], basestring):
        name = args[1]
      else:
        name = TINYJS_TEMP_NAME
      var = args[0]
      self.name = name
      self.nextSibling = 0
      self.prevSibling = 0
      self.var = var.ref()
      self.owned = False
    elif len(args) == 1 and\
        isinstance(args[0], CScriptVarLink):
      link = args[0]
      self.name = link.name
      self.nextSibling = 0
      self.prevSibling = 0
      self.var = link.var.ref()
      self.owned = False

  def __del__(self):
    pass
 
  def replaceWith(self, newVar):
    """ Replace the Variable pointed to
    """
    if isinstance(newVar, CScriptVar):
      oldVar = self.var
      self.var = newVar.ref()
      oldVar.unref()
    elif isinstance(newVar, CScriptVarLink):
      if newVar:
        self.replaceWith(newVar.var)
      else:
        self.replaceWith(CScriptVar())

  def getIntName(self):
    """ Get the name as an integer (for arrays)
    """
    return int(self.name)

  def setIntName(self, n):
    """ Set the name as an integer (for arrays)
    """
    self.name = str(n)

class CScriptVar(object):
  """ Variable class (containing a doubly-linked list of children)
  """

  # for debug:
  def _dump(self):
    return vars(self)
  # end for debug

  def __initAllVars__(self):
    self.firstChild = None
    self.lastChild = None
    self.refs = None # The number of references held to this - used for garbage collection
    self.data = None # The contents of this variable if it is a string
    self.intData = None # The contents of this variable if it is an int
    self.doubleData = None # The contents of this variable if it is a double
    self.flags = None # the flags determine the type of the variable - int/double/string/etc
    self.jsCallback = None # Callback for native functions
    self.jsCallbackUserData = None # user data passed as second argument to native functions

  # public
  def __init__(self, *args):
    self.__initAllVars__()
    if len(args) == 0:
      self.refs = 0
      self.init()
      self.flags = SCRIPTVAR_FLAGS.SCRIPTVAR_UNDEFINED
    elif len(args) == 1 and\
        isinstance(args[0], basestring):
      str = args[0]
      self.refs = 0
      self.init()
      self.flags = SCRIPTVAR_FLAGS.SCRIPTVAR_STRING
      self.data = str
    elif len(args) == 2 and\
        isinstance(args[0], basestring) and\
        isinstance(args[1], (int, long)):
      varData = args[0]
      varFlags = args[1]
      self.refs = 0
      self.init()
      self.flags = varFlags
      if varFlags & SCRIPTVAR_FLAGS.SCRIPTVAR_INTEGER:
        try:
          self.intData = int(varData)
          if len(varData) > 1 and varData[0] == '0':
            self.intData = int(varData, 8)
        except:
          self.intData = int(varData, 16)
      elif varFlags & SCRIPTVAR_FLAGS.SCRIPTVAR_DOUBLE:
        self.doubleData = float(varData)
      else:
        self.data = varData
    elif len(args) == 1 and\
        isinstance(args[0], float):
      val = args[0]
      self.refs = 0
      self.init()
      self.setDouble(val)
    elif len(args) == 1 and\
        isinstance(args[0], (int, long)):
      val = args[0]
      self.refs = 0
      self.init()
      self.setInt(val)

  def __del__(self):
    self.removeAllChildren()

  def getReturnVar(self):
    return self.getParameter(TINYJS_RETURN_VAR)

  def setReturnVar(self, var):
    self.findChildOrCreate(TINYJS_RETURN_VAR).replaceWith(var)

  def getParameter(self, name):
    return self.findChildOrCreate(name).var

  def findChild(self, childName):
    v = self.firstChild
    while v:
      if v.name == childName:
        return v
      v = v.nextSibling
    return 0

  def findChildOrCreate(self, childName, varFlags=SCRIPTVAR_FLAGS.SCRIPTVAR_UNDEFINED):
    l = self.findChild(childName)
    if l: return l

    return self.addChild(childName, CScriptVar(TINYJS_BLANK_DATA, varFlags))

  def findChildOrCreateByPath(self, path):
    p = path.find('.')
    if p == -1:
      return self.findChildOrCreate(path)

    return self.findChildOrCreate(path[:p], SCRIPTVAR_FLAGS.SCRIPTVAR_OBJECT).var.\
              findChildOrCreateByPath(path[p+1:])

  def addChild(self, childName, child=None):
    if self.isUndefined():
      self.flags = SCRIPTVAR_FLAGS.SCRIPTVAR_OBJECT
    # if no child supplied, create one
    if not child:
      child = CScriptVar()

    link = CScriptVarLink(child, childName)
    link.owned = True
    if self.lastChild:
      self.lastChild.nextSibling = link
      link.prevSibling = self.lastChild
      self.lastChild = link
    else:
      self.firstChild = link
      self.lastChild = link

    return link
 
  def addChildNoDup(self, childName, child=None):
    if not child:
      child = CScriptVar()

    v = self.findChild(childName)
    if v:
      v.replaceWith(child)
    else:
      v = self.addChild(childName, child)

    return v

  def removeChild(self, child):
    link = self.firstChild
    while link:
      if link.var == child:
        break
      link = link.nextSibling
    ASSERT(link)
    self.removeLink(link)

  def removeLink(self, link):
    if not link: return
    if link.nextSibling:
      link.nextSibling.prevSibling = link.prevSibling
    if link.prevSibling:
      link.nextSibling = link.nextSibling
    if self.lastChild == link:
      self.lastChild = link.prevSibling
    if self.firstChild == link:
      self.firstChild = link.nextSibling
    del link

  def removeAllChildren(self):
    c = self.firstChild
    while c:
      t = c.nextSibling
      del c
      c = t
    self.firstChild = 0
    self.lastChild = 0

  def getArrayIndex(self, idx):
    sIdx = '%d' % idx
    link = self.findChild(sIdx)
    if link: return link.var
    else: return CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_NULL) # undefined

  def setArrayIndex(self, idx, value):
    sIdx = '%d' % idx
    link = self.findChild(sIdx)

    if link:
      if value.isUndefined():
        self.removeLink(link)
      else:
        link.replaceWith(value)
    else:
      if not value.isUndefined():
        self.addChild(sIdx, value)
  
  def getArrayLength(self):
    highest = -1;
    if not self.isArray(): return 0

    link = self.firstChild
    while link:
      if isNumber(link.name):
        val = int(link.name)
        if val > highest: highest = val
      link = link.nextSibling
    return highest+1

  def getChildren(self):
    n = 0
    link = self.firstChild
    while link:
      n += 1
      link = link.nextSibling
    return n;

  def getInt(self):
    """ strtol understands about hex and octal
    """

    if self.isInt(): return self.intData
    if self.isNull(): return 0
    if self.isUndefined(): return 0
    if self.isDouble(): return int(self.doubleData)
    return 0;

  def getBool(self):
    return self.getInt() != 0

  def getDouble(self):
    if self.isDouble(): return self.doubleData
    if self.isInt(): return self.intData
    if self.isNull(): return 0
    if self.isUndefined(): return 0
    return 0 # or NaN?

  def getString(self):
    """ Because we can't return a string that is generated on demand.
        I should really just use char* :)
    """

    if self.isInt():
      buffer = '%d' % self.intData
      self.data = buffer
      return self.data
    if self.isDouble():
      buffer = '%f' % self.doubleData
      self.data = buffer
      return self.data
    if self.isNull(): return s_null
    if self.isUndefined(): return s_undefined
    # are we just a string here?
    return str(self.data)

  def getParsableString(self):
    # get Data as a parsable javascript string
    # Numbers can just be put in directly
    if self.isNumeric():
      return self.getString()
    if self.isFunction():
      funcStr = "function ("
      # get list of parameters
      link = self.firstChild
      while link:
        funcStr += link.name
        if link.nextSibling: funcStr += ","
        link = link.nextSibling
      # add function body
      funcStr += ") %s" % self.getString()
      return funcStr
    #if it is a string then we quote it
    if self.isString():
      return getJSString(self.getString())
    if self.isNull():
      return "null"
    return "undefined"

  def setInt(self, val):
    self.flags = (self.flags&~SCRIPTVAR_FLAGS.SCRIPTVAR_VARTYPEMASK) | SCRIPTVAR_FLAGS.SCRIPTVAR_INTEGER
    self.intData = val
    self.doubleData = 0
    self.data = TINYJS_BLANK_DATA

  def setDouble(self, val):
    self.flags = (self.flags&~SCRIPTVAR_FLAGS.SCRIPTVAR_VARTYPEMASK) | SCRIPTVAR_FLAGS.SCRIPTVAR_DOUBLE
    self.doubleData = val
    self.intData = 0
    self.data = TINYJS_BLANK_DATA

  def setString(self, str):
    # name sure it's not still a number or integer
    self.flags = (self.flags&~SCRIPTVAR_FLAGS.SCRIPTVAR_VARTYPEMASK) | SCRIPTVAR_FLAGS.SCRIPTVAR_STRING
    self.data = str
    self.intData = 0
    self.doubleData = 0

  def setUndefined(self):
    # name sure it's not still a number or integer
    self.flags = (self.flags&~SCRIPTVAR_FLAGS.SCRIPTVAR_VARTYPEMASK) | SCRIPTVAR_FLAGS.SCRIPTVAR_UNDEFINED
    self.data = TINYJS_BLANK_DATA
    self.intData = 0
    self.doubleData = 0
    self.removeAllChildren()

  def setArray(self):
    # name sure it's not still a number or integer
    self.flags = (self.flags&~SCRIPTVAR_FLAGS.SCRIPTVAR_VARTYPEMASK) | SCRIPTVAR_FLAGS.SCRIPTVAR_ARRAY
    self.data = TINYJS_BLANK_DATA
    self.intData = 0
    self.doubleData = 0
    self.removeAllChildren()

  def equals(self, v):
    resV = self.mathsOp(v, LEX_TYPES.LEX_EQUAL)
    res = resV.getBool()
    del resV
    return res

  def isInt(self):
    return self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_INTEGER!=0

  def isDouble(self):
    return self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_DOUBLE!=0

  def isString(self):
    return self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_STRING!=0

  def isNumeric(self):
    return self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_NUMERICMASK!=0

  def isFunction(self):
    return self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_FUNCTION!=0

  def isObject(self):
    return self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_OBJECT!=0
  def isArray(self):
    return self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_ARRAY!=0

  def isNative(self):
    return self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_NATIVE!=0

  def isUndefined(self):
    return self.flags & SCRIPTVAR_FLAGS.SCRIPTVAR_VARTYPEMASK == SCRIPTVAR_FLAGS.SCRIPTVAR_UNDEFINED

  def isNull(self):
    return self.flags & SCRIPTVAR_FLAGS.SCRIPTVAR_NULL !=0

  def isBasic(self):
    return self.firstChild==0 # ///< Is this *not* an array/object/etc

  def mathsOp(self, b, op):
    """ do a maths op with another script variable
    """

    a = self
    # Type equality check
    if op == LEX_TYPES.LEX_TYPEEQUAL or op == LEX_TYPES.LEX_NTYPEEQUAL:
      # check type first, then call again to check data
      eql = (a.flags & SCRIPTVAR_FLAGS.SCRIPTVAR_VARTYPEMASK) ==\
                  (b.flags & SCRIPTVAR_FLAGS.SCRIPTVAR_VARTYPEMASK)
      if eql:
        contents = a.mathsOp(b, LEX_TYPES.LEX_EQUAL)
        if not contents.getBool(): eql = false
        if not contents.refs: del contents
      if op == LEX_TYPES.LEX_TYPEEQUAL:
        return CScriptVar(eql)
      else:
        return CScriptVar(not eql)
    # do maths...
    if a.isUndefined() and b.isUndefined():
      if op == LEX_TYPES.LEX_EQUAL: return CScriptVar(True)
      elif op == LEX_TYPES.LEX_NEQUAL: return CScriptVar(False)
      else: return CScriptVar() # undefined
    elif (a.isNumeric() or a.isUndefined()) and\
               (b.isNumeric() or b.isUndefined()):
      if not a.isDouble() and not b.isDouble():
        # use ints
        da = a.getInt()
        db = b.getInt()
        if op == '+': return CScriptVar(da+db)
        elif op == '-': return CScriptVar(da-db)
        elif op == '*': return CScriptVar(da*db)
        elif op == '/': return CScriptVar(da/db)
        elif op == '&': return CScriptVar(da&db)
        elif op == '|': return CScriptVar(da|db)
        elif op == '^': return CScriptVar(da^db)
        elif op == '%': return CScriptVar(da%db)
        elif op == LEX_TYPES.LEX_EQUAL:     return CScriptVar(da==db)
        elif op == LEX_TYPES.LEX_NEQUAL:    return CScriptVar(da!=db)
        elif op == '<':     return CScriptVar(da<db)
        elif op == LEX_TYPES.LEX_LEQUAL:    return CScriptVar(da<=db)
        elif op == '>':     return CScriptVar(da>db)
        elif op == LEX_TYPES.LEX_GEQUAL:    return CScriptVar(da>=db)
        else: raise CScriptException("Operation "+CScriptLex.getTokenStr(op)+" not supported on the Int datatype")
      else:
        # use doubles
        da = a.getDouble()
        db = b.getDouble()
        if op == '+': return CScriptVar(da+db)
        elif op == '-': return CScriptVar(da-db)
        elif op == '*': return CScriptVar(da*db)
        elif op == '/': return CScriptVar(da/db)
        elif op == LEX_TYPES.LEX_EQUAL:     return CScriptVar(da==db)
        elif op == LEX_TYPES.LEX_NEQUAL:    return CScriptVar(da!=db)
        elif op == '<':     return CScriptVar(da<db)
        elif op == LEX_TYPES.LEX_LEQUAL:    return CScriptVar(da<=db)
        elif op == '>':     return CScriptVar(da>db)
        elif op == LEX_TYPES.LEX_GEQUAL:    return CScriptVar(da>=db)
        else: raise CScriptException("Operation "+CScriptLex.getTokenStr(op)+" not supported on the Double datatype")
    elif a.isArray():
      # Just check pointers
      if op == LEX_TYPES.LEX_EQUAL: return CScriptVar(a==b)
      elif op == LEX_TYPES.LEX_NEQUAL: return CScriptVar(a!=b)
      else: raise CScriptException("Operation "+CScriptLex.getTokenStr(op)+" not supported on the Array datatype")
    elif a.isObject():
      # Just check pointers
      if op == LEX_TYPES.LEX_EQUAL: return CScriptVar(a==b)
      elif op == LEX_TYPES.LEX_NEQUAL: return CScriptVar(a!=b)
      else: raise CScriptException("Operation "+CScriptLex.getTokenStr(op)+" not supported on the Object datatype")
    else:
       da = a.getString();
       db = b.getString();
       # use strings
       if op == '+':           return CScriptVar(da+db, SCRIPTVAR_FLAGS.SCRIPTVAR_STRING)
       elif op == LEX_TYPES.LEX_EQUAL:     return CScriptVar(da==db)
       elif op == LEX_TYPES.LEX_NEQUAL:    return CScriptVar(da!=db)
       elif op == '<':     return CScriptVar(da<db)
       elif op == LEX_TYPES.LEX_LEQUAL:    return CScriptVar(da<=db)
       elif op == '>':     return CScriptVar(da>db)
       elif op == LEX_TYPES.LEX_GEQUAL:    return CScriptVar(da>=db)
       else: raise CScriptException("Operation "+CScriptLex.getTokenStr(op)+" not supported on the string datatype");
    ASSERT(0)
    return 0

  def copyValue(self, val):
    # copy the value from the value given
    if val:
      self.copySimpleData(val)
      # remove all current children
      self.removeAllChildren()
      # copy children of 'val'
      child = val.firstChild
      while child:
        # don't copy the 'parent' object...
        if child.name != TINYJS_PROTOTYPE_CLASS:
          copied = child.var.deepCopy()
        else:
          copied = child.var

        self.addChild(child.name, copied)

        child = child.nextSibling
    else:
      self.setUndefined()

  def deepCopy(self):
    # deep copy this node and return the result
    newVar = CScriptVar()
    newVar.copySimpleData(self)
    # copy children
    child = self.firstChild
    while child:
      # don't copy the 'parent' object...
      if child.name != TINYJS_PROTOTYPE_CLASS:
        copied = child.var.deepCopy()
      else:
        copied = child.var

      newVar.addChild(child.name, copied)
      child = child.nextSibling
    return newVar;

  def trace(self, indentStr = "", name = ""):
    # Dump out the contents of this using trace
    TRACE("%s'%s' = '%s' %s" % (
        indentStr,
        name,
        self.getString(),
        self.getFlagsAsString()))
    indent = indentStr+" "
    link = self.firstChild
    while link:
      link.var.trace(indent, link.name)
      link = link.nextSibling

  def getFlagsAsString(self):
    # For debugging - just dump a string version of the flags
    flagstr = ""
    if self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_FUNCTION: flagstr = flagstr + "FUNCTION "
    if self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_OBJECT: flagstr = flagstr + "OBJECT "
    if self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_ARRAY: flagstr = flagstr + "ARRAY "
    if self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_NATIVE: flagstr = flagstr + "NATIVE "
    if self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_DOUBLE: flagstr = flagstr + "DOUBLE "
    if self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_INTEGER: flagstr = flagstr + "INTEGER "
    if self.flags&SCRIPTVAR_FLAGS.SCRIPTVAR_STRING: flagstr = flagstr + "STRING "
    return flagstr

  def getJSON(self, destination, linePrefix=""):
    # Write out all the JS code needed to recreate this script variable to the stream (as JSON)
    if self.isObject():
      indentedLinePrefix = linePrefix+"  "
      # children - handle with bracketed list
      destination += "{ \n"
      link = self.firstChild
      while link:
        destination += indentedLinePrefix
        destination += getJSString(link.name)
        destination += " : "
        destination = link.var.getJSON(destination, indentedLinePrefix)
        link = link.nextSibling
        if link:
          destination += ",\n"
      destination += "\n" + linePrefix + "}"
    elif self.isArray():
      indentedLinePrefix = linePrefix+"  "
      destination += "[\n"
      len = self.getArrayLength()
      if len>10000: len=10000 # we don't want to get stuck here!

      for i in xrange(len):
        destination = self.getArrayIndex(i).getJSON(destination, indentedLinePrefix)
        if i<len-1: destination += ",\n"

      destination += "\n" + linePrefix + "]"
    else:
      # no children or a function... just write value directly
      destination += self.getParsableString()
    return destination

  def setCallback(self, callback, userdata):
    # Set the callback for native functions
    self.jsCallback = callback
    self.jsCallbackUserData = userdata

  # /// For memory management/garbage collection
  def ref(self):
    # Add reference to this variable
    self.refs+=1
    return self

  def unref(self):
    # Remove a reference, and delete this variable if required
    if self.refs<=0: print("OMFG, we have unreffed too far!")
    self.refs -= 1
    if self.refs==0:
      del self

  def getRefs(self):
    # Get the number of references to this script variable
    return self.refs;

  # protect:
  def init(self):
    """ initialisation of data members
    """

    self.firstChild = 0
    self.lastChild = 0
    self.flags = 0
    self.jsCallback = 0
    self.jsCallbackUserData = 0
    self.data = TINYJS_BLANK_DATA
    self.intData = 0
    self.doubleData = 0

  # /** Copy the basic data and flags from the variable given, with no
  # * children. Should be used internally only - by copyValue and deepCopy */
  def copySimpleData(self, val):
    self.data = val.data
    self.intData = val.intData
    self.doubleData = val.doubleData
    self.flags = (self.flags & ~SCRIPTVAR_FLAGS.SCRIPTVAR_VARTYPEMASK) | (val.flags & SCRIPTVAR_FLAGS.SCRIPTVAR_VARTYPEMASK)


# ----------------------------------------------------------------------------------- CSCRIPT

class CTinyJS(object):

  # for debug:
  def _dump(self):
    return vars(self)
  # end for debug

  def __initAllVars__(self):
    self.root = None
    self.l = None
    self.scopes = None
    self.call_stack = None
    self.stringClass = None
    self.objectClass = None
    self.arrayClass = None

  # public:
  def __init__(self, *args):
    self.__initAllVars__()
    self.l = 0
    self.root = CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_OBJECT).ref()
    # Add built-in classes
    self.stringClass = (CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_OBJECT)).ref()
    self.arrayClass = (CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_OBJECT)).ref()
    self.objectClass = (CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_OBJECT)).ref()
    self.root.addChild("String", self.stringClass)
    self.root.addChild("Array", self.arrayClass)
    self.root.addChild("Object", self.objectClass)

  def __del__(self):
    ASSERT(not self.l)
    self.scopes = []
    self.stringClass.unref()
    self.arrayClass.unref()
    se.fobjectClass.unref()
    self.root.unref()

  def execute(self, code):
    oldLex = self.l
    oldScopes = self.scopes
    self.l = CScriptLex(code)
    if TINYJS_CALL_STACK:
      self.call_stack = []
    self.scopes = []
    self.scopes.append(self.root)
    try:
      execute = True
      while self.l.tk: self.statement(execute)
    except CScriptException as e:
        msg = "Error %s" % str(e)
        if  TINYJS_CALL_STACK:
          for i in xrange(len(self.call_stack)-1, -1, -1):
            msg = '%s\n%d: %s' % (msg, i, self.call_stack[i])
        msg = '%s at %s' % (msg, self.l.getPosition())
        del self.l
        self.l = oldLex

        raise CScriptException(msg)
    del self.l
    self.l = oldLex
    self.scopes = oldScopes

  def evaluateComplex(self, code):
    """ Evaluate the given code and return a link to a javascript object,
        useful for (dangerous) JSON parsing. If nothing to return, will return
        'undefined' variable type. CScriptVarLink is returned as this will
        automatically unref the result as it goes out of scope. If you want to
        keep it, you must use ref() and unref() */
    """

    oldLex = self.l
    oldScopes = self.scopes

    self.l = CScriptLex(code)
    if TINYJS_CALL_STACK:
      self.call_stack = []
    self.scopes = []
    self.scopes.append(self.root)
    v = 0
    try:
      execute = True
      while 1:
        CLEAN(v);
        v = self.base(execute)
        if self.l.tk!=LEX_TYPES.LEX_EOF: l.match(';')
        if not self.l.tk != LEX_TYPES.LEX_EOF:
          break
    except CScriptException as e:
      msg = "Error %s" % str(e)
      if TINYJS_CALL_STACK:
        for i in xrange(len(self.call_stack)-1, -1, -1):
          msg = '%s\n%d: %s' % (msg, i, self.call_stack[i])
      msg = "%s at %s" % (msg, self.l.getPosition())
      del self.l
      self.l = oldLex
      raise CScriptException(msg)
    del self.l
    self.l = oldLex
    self.scopes = oldScopes

    if v:
      # r = *v
      r = v
      CLEAN(v)
      return r
    # return undefined...
    return CScriptVarLink(CScriptVar())

  def evaluate(self, code):
    """  Evaluate the given code and return a string. If nothing to return, will return
         'undefined' */
    """

    return self.evaluateComplex(code).var.getString()

  def addNative(self, funcDesc, ptr, userdata):
    """ add a native function to be called from TinyJS
        example:
           \code
               void scRandInt(CScriptVar *c, void *userdata) { ... }
               tinyJS->addNative("function randInt(min, max)", scRandInt, 0);
           \endcode

           or

           \code
               void scSubstring(CScriptVar *c, void *userdata) { ... }
               tinyJS->addNative("function String.substring(lo, hi)", scSubstring, 0);
           \endcode
    """

    oldLex = self.l
    self.l = CScriptLex(funcDesc)

    base = self.root

    self.l.match(LEX_TYPES.LEX_R_FUNCTION)
    funcName = self.l.tkStr
    self.l.match(LEX_TYPES.LEX_ID)
    # Check for dots, we might want to do something like function String.substring ... 
    while self.l.tk == '.':
      self.l.match('.')
      link = base.findChild(funcName)
      # if it doesn't exist, make an object class
      if not link: link = base.addChild(funcName, CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_OBJECT))
      base = link.var
      funcName = self.l.tkStr
      self.l.match(LEX_TYPES.LEX_ID)

    funcVar = CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_FUNCTION | SCRIPTVAR_FLAGS.SCRIPTVAR_NATIVE)
    funcVar.setCallback(ptr, userdata)
    self.parseFunctionArguments(funcVar)
    del self.l
    self.l = oldLex

    base.addChild(funcName, funcVar)

  # Get the given variable specified by a path (var1.var2.etc), or return 0
  def getScriptVariable(self, path):
    # traverse path
    prevIdx = 0
    thisIdx = path.find('.')
    if thisIdx == -1: thisIdx = len(path)
    var = self.root
    while var and prevIdx<len(path):
      el = path[prevIdx: prevIdx]
      varl = var.findChild(el)
      var = varl.var if varl else 0
      prevIdx = thisIdx+1
      thisIdx = path[prevIdx+1:].find('.')
      if thisIdx == -1: thisIdx = len(path)
    return var

  # Get the value of the given variable, or return 0
  def getVariable(self, path):
    var = self.getScriptVariable(path)
    # return result
    if var:
        return var.getString()
    else:
        return 0

  # set the value of the given variable, return trur if it exists and gets set
  def setVariable(self, path, varData):
    var = self.getScriptVariable(path)
    # return result
    if var:
      if var.isInt():
        var.setInt(int(varData))
      elif var.isDouble():
        var.setDouble(float(varData))
      else:
        var.setString(varData)
      return True
    else:
      return False

  # Send all variables to stdout
  def trace(self):
    self.root.trace()

  # private:
  # parsing - in order of precedence
  def functionCall(self, execute, function, parent):
    """ Handle a function call (assumes we've parsed the function name and we're
        on the start bracket). 'parent' is the object that contains this method,
        if there was one (otherwise it's just a normnal function).
    """

    if execute:
      if not function.var.isFunction():
        errorMsg = "Expecting '"
        errorMsg = errorMsg + function.name + "' to be a function"
        raise CScriptException(errorMsg)
      self.l.match('(')
      # create a new symbol table entry for execution of this function
      functionRoot = CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_FUNCTION)
      if parent:
        functionRoot.addChildNoDup("this", parent)
      # grab in all parameters
      v = function.var.firstChild
      while v:
        value = self.base(execute)
        if execute:
          if value.var.isBasic():
            # pass by value
            functionRoot.addChild(v.name, value.var.deepCopy())
          else:
            # pass by reference
            functionRoot.addChild(v.name, value.var)
        CLEAN(value)
        if self.l.tk!=')': self.l.match(',')
        v = v.nextSibling
      self.l.match(')')
      # setup a return variable
      returnVar = None
      # execute function!
      # add the function's execute space to the symbol table so we can recurse
      returnVarLink = functionRoot.addChild(TINYJS_RETURN_VAR)
      self.scopes.append(functionRoot)
      if TINYJS_CALL_STACK:
        self.call_stack.append(function.name + " from " + self.l.getPosition())

      if function.var.isNative():
        ASSERT(function.var.jsCallback)
        function.var.jsCallback(functionRoot, function.var.jsCallbackUserData)
      else:
        # we just want to execute the block, but something could
        # have messed up and left us with the wrong ScriptLex, so
        # we want to be careful here...
        exception = None
        oldLex = self.l
        newLex = CScriptLex(function.var.getString())
        self.l = newLex
        try:
          self.block(execute)
          # because return will probably have called this, and set execute to false
          execute = True
        except CScriptException as e:
          exception = e
        del newLex
        self.l = oldLex

        if exception:
          raise exception
        if  TINYJS_CALL_STACK:
          if not self.call_stack: self.call_stack.pop(-1)
      self.scopes.pop(-1)
      # get the real return var before we remove it from our function
      returnVar = CScriptVarLink(returnVarLink.var)
      functionRoot.removeLink(returnVarLink)
      del functionRoot
      if returnVar:
        return returnVar
      else:
        return CScriptVarLink(CScriptVar())
    else:
      # function, but not executing - just parse args and be done
      self.l.match('(')
      while self.l.tk != ')':
        value = self.base(execute)
        CLEAN(value)
        if self.l.tk!=')': self.l.match(',')
      self.l.match(')')
      if self.l.tk == '{' : # TODO: why is this here?
        self.block(execute)
      # function will be a blank scriptvarlink if we're not executing,
      # so just return it rather than an alloc/free
      return function

  def factor(self, execute):
    if self.l.tk=='(':
      self.l.match('(')
      a = self.base(execute)
      self.l.match(')')
      return a
    if self.l.tk==LEX_TYPES.LEX_R_TRUE:
      self.l.match(LEX_TYPES.LEX_R_TRUE)
      return CScriptVarLink(CScriptVar(1))
    if self.l.tk==LEX_TYPES.LEX_R_FALSE:
      self.l.match(LEX_TYPES.LEX_R_FALSE)
      return CScriptVarLink(CScriptVar(0))
    if self.l.tk==LEX_TYPES.LEX_R_NULL:
      self.l.match(LEX_TYPES.LEX_R_NULL)
      return CScriptVarLink(CScriptVar(TINYJS_BLANK_DATA,SCRIPTVAR_FLAGS.SCRIPTVAR_NULL))
    if self.l.tk==LEX_TYPES.LEX_R_UNDEFINED:
      self.l.match(LEX_TYPES.LEX_R_UNDEFINED)
      return CScriptVarLink(CScriptVar(TINYJS_BLANK_DATA,SCRIPTVAR_FLAGS.SCRIPTVAR_UNDEFINED))
    if self.l.tk==LEX_TYPES.LEX_ID:
      a = self.findInScopes(self.l.tkStr) if execute else CScriptVarLink(CScriptVar())
      # printf("0x%08X for %s at %s\n", (unsigned int)a, l->tkStr.c_str(), l->getPosition().c_str());
      # The parent if we're executing a method call
      parent = 0

      if execute and not a:
        # Variable doesn't exist! JavaScript says we should create it
        # (we won't add it here. This is done in the assignment operator)
        a = CScriptVarLink(CScriptVar(), self.l.tkStr)
      self.l.match(LEX_TYPES.LEX_ID)
      while self.l.tk=='(' or self.l.tk=='.' or self.l.tk=='[':
        if self.l.tk=='(':  # ------------------------------------- Function Call
          a = self.functionCall(execute, a, parent)
        elif self.l.tk == '.': # ------------------------------------- Record Access
          self.l.match('.')
          if execute:
            name = self.l.tkStr
            child = a.var.findChild(name)
            if not child: child = self.findInParentClasses(a.var, name)
            if not child:
              # if we haven't found this defined yet, use the built-in
              #  'length' properly
              if a.var.isArray() and name == "length":
                l = a.var.getArrayLength()
                child = CScriptVarLink(CScriptVar(l))
              elif a.var.isString() and name == "length":
                l = len(a.var.getString())
                child = CScriptVarLink(CScriptVar(l))
              else:
                child = a.var.addChild(name)
            parent = a.var
            a = child
          self.l.match(LEX_TYPES.LEX_ID)
        elif self.l.tk == '[': # ------------------------------------- Array Access
          self.l.match('[')
          index = self.base(execute)
          self.l.match(']')
          if execute:
            child = a.var.findChildOrCreate(index.var.getString())
            parent = a.var
            a = child
          CLEAN(index);
        else: ASSERT(0)
      return a
    if self.l.tk==LEX_TYPES.LEX_INT or self.l.tk==LEX_TYPES.LEX_FLOAT:
      a = CScriptVar(self.l.tkStr,
          (SCRIPTVAR_FLAGS.SCRIPTVAR_INTEGER if (self.l.tk==LEX_TYPES.LEX_INT) else SCRIPTVAR_FLAGS.SCRIPTVAR_DOUBLE))
      self.l.match(self.l.tk)
      return CScriptVarLink(a)
    if self.l.tk==LEX_TYPES.LEX_STR:
      a = CScriptVar(self.l.tkStr, SCRIPTVAR_FLAGS.SCRIPTVAR_STRING)
      self.l.match(LEX_TYPES.LEX_STR)
      return CScriptVarLink(a)
    if self.l.tk=='{':
      contents = CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_OBJECT)
      # JSON-style object definition
      self.l.match('{')
      while self.l.tk != '}':
        id = self.l.tkStr
        # we only allow strings or IDs on the left hand side of an initialisation
        if self.l.tk==LEX_TYPES.LEX_STR: self.l.match(LEX_TYPES.LEX_STR)
        else: self.l.match(LEX_TYPES.LEX_ID)
        self.l.match(':')
        if execute:
          a = self.base(execute)
          contents.addChild(id, a.var)
          CLEAN(a)
        # no need to clean here, as it will definitely be used
        if self.l.tk != '}': self.l.match(',')

      self.l.match('}')
      return CScriptVarLink(contents)
    if self.l.tk=='[':
      contents = CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_ARRAY)
      # JSON-style array
      self.l.match('[')
      idx = 0
      while self.l.tk != ']':
        if execute:
          idx_str = '%d' % idx

          a = self.base(execute)
          contents.addChild(idx_str, a.var)
          CLEAN(a)
        # no need to clean here, as it will definitely be used
        if self.l.tk != ']': self.l.match(',')
        idx+=1
      self.l.match(']')
      return CScriptVarLink(contents)
    if self.l.tk==LEX_TYPES.LEX_R_FUNCTION:
      funcVar = self.parseFunctionDefinition()
      if funcVar.name != TINYJS_TEMP_NAME:
        TRACE("Functions not defined at statement-level are not meant to have a name")
      return funcVar
    if self.l.tk==LEX_TYPES.LEX_R_NEW:
      # new -> create a new object
      self.l.match(LEX_TYPES.LEX_R_NEW)
      className = self.l.tkStr
      if execute:
        objClassOrFunc = self.findInScopes(className)
        if not objClassOrFunc:
          TRACE("%s is not a valid class name" % className)
          return CScriptVarLink(CScriptVar())
        self.l.match(LEX_TYPES.LEX_ID)
        obj = CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_OBJECT)
        objLink = CScriptVarLink(obj)
        if objClassOrFunc.var.isFunction():
          CLEAN(self.functionCall(execute, objClassOrFunc, obj))
        else:
          obj.addChild(TINYJS_PROTOTYPE_CLASS, objClassOrFunc.var)
          if self.l.tk == '(':
            self.l.match('(')
            self.l.match(')')
        return objLink
      else:
        self.l.match(LEX_TYPES.LEX_ID)
        if self.l.tk == '(':
          self.l.match('(')
          self.l.match(')')
    # Nothing we can do here... just hope it's the end...
    self.l.match(LEX_TYPES.LEX_EOF)
    return 0

  def unary(self, execute):
    if self.l.tk=='!':
      self.l.match('!') # // binary not
      a = self.factor(execute)
      if execute:
        zero = CScriptVar(0)
        res = a.var.mathsOp(zero, LEX_TYPES.LEX_EQUAL)
        CREATE_LINK(a, res)
    else:
      a = self.factor(execute)
    return a

  def term(self, execute):
    a = self.unary(execute)
    while self.l.tk=='*' or self.l.tk=='/' or self.l.tk=='%':
      op = self.l.tk
      self.l.match(self.l.tk)
      b = self.unary(execute)
      if execute:
        res = a.var.mathsOp(b.var, op)
        CREATE_LINK(a, res)
      CLEAN(b)
    return a

  def expression(self, execute):
    negate = False
    if self.l.tk=='-':
        self.l.match('-')
        negate = True
    a = self.term(execute)
    if negate:
      zero = CScriptVar(0)
      res = zero.mathsOp(a.var, '-')
      CREATE_LINK(a, res)

    while self.l.tk=='+' or self.l.tk=='-' or\
      self.l.tk==LEX_TYPES.LEX_PLUSPLUS or self.l.tk==LEX_TYPES.LEX_MINUSMINUS:
      op = self.l.tk
      self.l.match(self.l.tk)
      if op==LEX_TYPES.LEX_PLUSPLUS or op==LEX_TYPES.LEX_MINUSMINUS:
        if execute:
          one = CScriptVar(1)
          res = a.var.mathsOp(one, '+' if op==LEX_TYPES.LEX_PLUSPLUS else '-')
          oldValue = CScriptVarLink(a.var)
          # in-place add/subtract
          a.replaceWith(res)
          CLEAN(a)
          a = oldValue
      else:
        b = self.term(execute)
        if execute:
          # not in-place, so just replace
          res = a.var.mathsOp(b.var, op)
          CREATE_LINK(a, res)
        CLEAN(b)
    return a

  def shift(self, execute):
    a = self.expression(execute)
    if self.l.tk==LEX_TYPES.LEX_LSHIFT or self.l.tk==LEX_TYPES.LEX_RSHIFT or self.l.tk==LEX_TYPES.LEX_RSHIFTUNSIGNED:
      op = self.l.tk
      self.l.match(op)
      b = self.base(execute)
      shift = b.var.getInt() if execute else 0
      CLEAN(b)
      if execute:
        if op==LEX_TYPES.LEX_LSHIFT: a.var.setInt(a.var.getInt() << shift)
        if op==LEX_TYPES.LEX_RSHIFT: a.var.setInt(a.var.getInt() >> shift)
        #if (op==LEX_RSHIFTUNSIGNED) a->var->setInt(((unsigned int)a->var->getInt()) >> shift);
        import ctypes
        uint_a = ctypes.c_uint(a.var.getInt())
        if op==LEX_TYPES.LEX_RSHIFTUNSIGNED: a.var.setInt(uint_a.value >> shift)
    return a

  def condition(self, execute):
    a = self.shift(execute)
    while self.l.tk==LEX_TYPES.LEX_EQUAL or self.l.tk==LEX_TYPES.LEX_NEQUAL or\
         self.l.tk==LEX_TYPES.LEX_TYPEEQUAL or self.l.tk==LEX_TYPES.LEX_NTYPEEQUAL or\
         self.l.tk==LEX_TYPES.LEX_LEQUAL or self.l.tk==LEX_TYPES.LEX_GEQUAL or\
         self.l.tk=='<' or self.l.tk=='>':
      op = self.l.tk
      self.l.match(self.l.tk)
      b = self.shift(execute)
      if execute:
        res = a.var.mathsOp(b.var, op)
        CREATE_LINK(a,res)
      CLEAN(b)
    return a

  def logic(self, execute):
    a = self.condition(execute)
    while self.l.tk=='&' or self.l.tk=='|' or self.l.tk=='^' or\
      self.l.tk==LEX_TYPES.LEX_ANDAND or self.l.tk==LEX_TYPES.LEX_OROR:
      noexecute = False
      op = self.l.tk
      self.l.match(self.l.tk)
      shortCircuit = False
      boolean = False
      # if we have short-circuit ops, then if we know the outcome
      # we don't bother to execute the other op. Even if not
      # we need to tell mathsOp it's an & or |
      if op==LEX_TYPES.LEX_ANDAND:
        op = '&'
        shortCircuit = not a.var.getBool()
        boolean = True
      elif op==LEX_TYPES.LEX_OROR:
        op = '|'
        shortCircuit = a.var.getBool()
        boolean = True
      b = self.condition(noexecute if shortCircuit else execute)
      if execute and not shortCircuit:
        if boolean:
          newa = CScriptVar(a.var.getBool())
          newb = CScriptVar(b.var.getBool())
          CREATE_LINK(a, newa)
          CREATE_LINK(b, newb)
        res = a.var.mathsOp(b.var, op)
        CREATE_LINK(a, res)
      CLEAN(b)
    return a

  def ternary(self, execute):
    lhs = self.logic(execute)
    noexec = False
    if self.l.tk=='?':
      self.l.match('?')
      if not execute:
        CLEAN(lhs)
        CLEAN(base(noexec))
        self.l.match(':')
        CLEAN(base(noexec))
      else:
        first = lhs.var.getBool()
        CLEAN(lhs)
        if first:
          lhs = self.base(execute)
          self.l.match(':')
          CLEAN(self.base(noexec))
        else:
          CLEAN(self.base(noexec))
          self.l.match(':')
          lhs = self.base(execute)

    return lhs

  def base(self, execute):
    lhs = self.ternary(execute)
    if self.l.tk=='=' or self.l.tk==LEX_TYPES.LEX_PLUSEQUAL or self.l.tk==LEX_TYPES.LEX_MINUSEQUAL:
      # If we're assigning to this and we don't have a parent,
      # add it to the symbol table root as per JavaScript. */
      if execute and not lhs.owned:
        if len(lhs.name)>0:
          realLhs = self.root.addChildNoDup(lhs.name, lhs.var)
          CLEAN(lhs)
          lhs = realLhs
        else:
          TRACE("Trying to assign to an un-named type\n")

      op = self.l.tk
      self.l.match(self.l.tk)
      rhs = self.base(execute)
      if execute:
        if op=='=':
          lhs.replaceWith(rhs)
        elif op==LEX_TYPES.LEX_PLUSEQUAL:
          res = lhs.var.mathsOp(rhs.var, '+')
          lhs.replaceWith(res)
        elif op==LEX_TYPES.LEX_MINUSEQUAL:
          res = lhs.var.mathsOp(rhs.var, '-')
          lhs.replaceWith(res)
        else: ASSERT(0)
      
      CLEAN(rhs)
    return lhs

  def block(self, execute):
    self.l.match('{')
    if execute:
      while self.l.tk and self.l.tk!='}':
        self.statement(execute)
      self.l.match('}')
    else:
      # fast skip of blocks
      brackets = 1
      while self.l.tk and brackets:
        if self.l.tk == '{': brackets+=1
        if self.l.tk == '}': brackets-=1
        self.l.match(self.l.tk)

  def statement(self, execute):
    if (self.l.tk==LEX_TYPES.LEX_ID or
        self.l.tk==LEX_TYPES.LEX_INT or
        self.l.tk==LEX_TYPES.LEX_FLOAT or
        self.l.tk==LEX_TYPES.LEX_STR or
        self.l.tk=='-'):
      # Execute a simple statement that only contains basic arithmetic...
      CLEAN(self.base(execute))
      self.l.match(';')
    elif self.l.tk=='{':
      # A block of code
      self.block(execute)
    elif self.l.tk==';':
      # Empty statement - to allow things like ;;;
      self.l.match(';')
    elif self.l.tk==LEX_TYPES.LEX_R_VAR:
      # variable creation. TODO - we need a better way of parsing the left
      # hand side. Maybe just have a flag called can_create_var that we
      # set and then we parse as if we're doing a normal equals.
      self.l.match(LEX_TYPES.LEX_R_VAR)
      while self.l.tk != ';':
        a = 0
        if execute:
          a = self.scopes[-1].findChildOrCreate(self.l.tkStr)
        self.l.match(LEX_TYPES.LEX_ID)
        # now do stuff defined with dots
        while self.l.tk == '.':
          self.l.match('.')
          if execute:
            lastA = a
            a = lastA.var.findChildOrCreate(self.l.tkStr)
          self.l.match(LEX_TYPES.LEX_ID)
        # sort out initialiser
        if self.l.tk == '=':
          self.l.match('=')
          var = self.base(execute)
          if execute:
            a.replaceWith(var)
          CLEAN(var)
        if self.l.tk != ';':
          self.l.match(',')
      self.l.match(';')
    elif self.l.tk==LEX_TYPES.LEX_R_IF:
        self.l.match(LEX_TYPES.LEX_R_IF)
        self.l.match('(')
        var = self.base(execute)
        self.l.match(')')
        cond = execute and var.var.getBool()
        CLEAN(var)
        noexecute = False # because we need to be abl;e to write to it
        self.statement(execute if cond else noexecute)
        if self.l.tk==LEX_TYPES.LEX_R_ELSE:
          self.l.match(LEX_TYPES.LEX_R_ELSE)
          self.statement(noexecute if cond else execute)
    elif self.l.tk==LEX_TYPES.LEX_R_WHILE:
      # We do repetition by pulling out the string representing our statement
      # there's definitely some opportunity for optimisation here
      self.l.match(LEX_TYPES.LEX_R_WHILE);
      self.l.match('(')
      whileCondStart = self.l.tokenStart
      noexecute = False
      cond = self.base(execute)
      loopCond = execute and cond.var.getBool()
      CLEAN(cond)
      whileCond = self.l.getSubLex(whileCondStart)
      self.l.match(')')
      whileBodyStart = self.l.tokenStart
      self.statement(execute if loopCond else noexecute)
      whileBody = self.l.getSubLex(whileBodyStart)
      oldLex = self.l
      loopCount = TINYJS_LOOP_MAX_ITERATIONS
      while loopCond and loopCount:
        whileCond.reset()
        self.l = whileCond
        cond = self.base(execute)
        loopCond = execute and cond.var.getBool()
        CLEAN(cond)
        if loopCond:
          whileBody.reset()
          self.l = whileBody
          self.statement(execute)
        loopCount -= 1
      self.l = oldLex
      del whileCond
      del whileBody

      if loopCount<=0:
          self.root.trace()
          TRACE("WHILE Loop exceeded %d iterations at %s\n" % (TINYJS_LOOP_MAX_ITERATIONS, self.l.getPosition()))
          raise CScriptException("LOOP_ERROR")
    elif self.l.tk==LEX_TYPES.LEX_R_FOR:
      self.l.match(LEX_TYPES.LEX_R_FOR)
      self.l.match('(')
      self.statement(execute) # initialisation
      #l.match(';')
      forCondStart = self.l.tokenStart
      noexecute = False
      cond = self.base(execute) # condition
      loopCond = execute and cond.var.getBool()
      CLEAN(cond)
      forCond = self.l.getSubLex(forCondStart)
      self.l.match(';')
      forIterStart = self.l.tokenStart
      CLEAN(self.base(noexecute)) # iterator
      forIter = self.l.getSubLex(forIterStart)
      self.l.match(')')
      forBodyStart = self.l.tokenStart
      self.statement(execute if loopCond else noexecute)
      forBody = self.l.getSubLex(forBodyStart)
      oldLex = self.l
      if loopCond:
        forIter.reset()
        self.l = forIter
        CLEAN(self.base(execute))
      loopCount = TINYJS_LOOP_MAX_ITERATIONS
      while execute and loopCond and loopCount:
        forCond.reset()
        self.l = forCond
        cond = self.base(execute)
        loopCond = cond.var.getBool()
        CLEAN(cond)
        if execute and loopCond:
          forBody.reset()
          self.l = forBody
          self.statement(execute)
        if execute and loopCond:
          forIter.reset()
          self.l = forIter
          CLEAN(self.base(execute))
        loopCount -= 1
      self.l = oldLex
      del forCond
      del forIter
      del forBody
      if loopCount<=0:
        self.root.trace()
        TRACE("FOR Loop exceeded %d iterations at %s" % (TINYJS_LOOP_MAX_ITERATIONS, self.l.getPosition()))
        raise CScriptException("LOOP_ERROR")
    elif self.l.tk==LEX_TYPES.LEX_R_RETURN:
      self.l.match(LEX_TYPES.LEX_R_RETURN)
      result = 0
      if self.l.tk != ';':
        result = self.base(execute)
      if execute:
        resultVar = self.scopes[-1].findChild(TINYJS_RETURN_VAR)
        if resultVar:
          resultVar.replaceWith(result)
        else:
          TRACE("RETURN statement, but not in a function.")
        execute = False
      CLEAN(result)
      self.l.match(';')
    elif self.l.tk==LEX_TYPES.LEX_R_FUNCTION:
      funcVar = self.parseFunctionDefinition()
      if execute:
        if funcVar.name == TINYJS_TEMP_NAME:
          TRACE("Functions defined at statement-level are meant to have a name")
        else:
          self.scopes[-1].addChildNoDup(funcVar.name, funcVar.var)
      CLEAN(funcVar)
    else: self.l.match(LEX_TYPES.LEX_EOF)

  # parsing utility functions
  def parseFunctionDefinition(self):
    # actually parse a function...
    self.l.match(LEX_TYPES.LEX_R_FUNCTION)
    funcName = TINYJS_TEMP_NAME
    # we can have functions without names
    if self.l.tk==LEX_TYPES.LEX_ID:
      funcName = self.l.tkStr
      self.l.match(LEX_TYPES.LEX_ID)
    funcVar = CScriptVarLink(CScriptVar(TINYJS_BLANK_DATA, SCRIPTVAR_FLAGS.SCRIPTVAR_FUNCTION), funcName)
    self.parseFunctionArguments(funcVar.var)
    funcBegin = self.l.tokenStart
    noexecute = False
    self.block(noexecute)
    funcVar.var.data = self.l.getSubString(funcBegin)
    return funcVar

  def parseFunctionArguments(self, funcVar):
    self.l.match('(')
    while self.l.tk!=')':
      funcVar.addChildNoDup(self.l.tkStr)
      self.l.match(LEX_TYPES.LEX_ID)
      if self.l.tk!=')': self.l.match(',')
    self.l.match(')')

  # Finds a child, looking recursively up the scopes
  def findInScopes(self, childName):
    for s in xrange(len(self.scopes)-1, -1, -1):
      v = self.scopes[s].findChild(childName)
      if v: return v
    return None

  # Look up in any parent classes of the given object
  def findInParentClasses(self, object, name):
    # Look for links to actual parent classes
    parentClass = object.findChild(TINYJS_PROTOTYPE_CLASS)
    while parentClass:
      implementation = parentClass.var.findChild(name)
      if implementation: return implementation
      parentClass = parentClass.var.findChild(TINYJS_PROTOTYPE_CLASS)
    # else fake it for strings and finally objects
    if object.isString():
      implementation = self.stringClass.findChild(name)
      if implementation: return implementation
    if object.isArray():
      implementation = self.arrayClass.findChild(name)
      if implementation: return implementation
    implementation = self.objectClass.findChild(name)
    if implementation: return implementation

    return 0;

def test():
  pass

if __name__ == '__main__':
  test()
