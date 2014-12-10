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

class LEX_TYPES(object):
  LEX_EOF = 0
  LEX_ID =256
  LEX_INT = -1
  LEX_FLOAT = -1
  LEX_STR = -1

  LEX_EQUAL = -1
  LEX_TYPEEQUAL = -1
  LEX_NEQUAL = -1
  LEX_NTYPEEQUAL = -1
  LEX_LEQUAL = -1
  LEX_LSHIFT = -1
  LEX_LSHIFTEQUAL = -1
  LEX_GEQUAL = -1
  LEX_RSHIFT = -1
  LEX_RSHIFTUNSIGNED = -1
  LEX_RSHIFTEQUAL = -1
  LEX_PLUSEQUAL = -1
  LEX_MINUSEQUAL = -1
  LEX_PLUSPLUS = -1
  LEX_MINUSMINUS = -1
  LEX_ANDEQUAL = -1
  LEX_ANDAND = -1
  LEX_OREQUAL = -1
  LEX_OROR = -1
  LEX_XOREQUAL = -1

  #reserved words
  #define LEX_R_LIST_START LEX_R_IF
  LEX_R_IF = -1
  LEX_R_ELSE = -1
  LEX_R_DO = -1
  LEX_R_WHILE = -1
  LEX_R_FOR = -1
  LEX_R_BREAK = -1
  LEX_R_CONTINUE = -1
  LEX_R_FUNCTION = -1
  LEX_R_RETURN = -1
  LEX_R_VAR = -1
  LEX_R_TRUE = -1
  LEX_R_FALSE = -1
  LEX_R_NULL = -1
  LEX_R_UNDEFINED = -1
  LEX_R_NEW = 1

  LEX_R_LIST_END = -1 # always the last entry


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
TINYJS_TEMP_NAME = ""
TINYJS_BLANK_DATA = ""

class CScriptException(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class CScriptLex(object):

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
      print >>errorString, 'Got', self.getTokenStr(tk), 'expected' , self.getTokenStr(expected_tk),\
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
    if token == LEX_TYPES.LEX_RSHIFTUNSIGNED : return ">>";
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

    return "?[%d]" % token

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
      return CScriptLex('', self, lastPosition, lastCharIdx)
    else:
      return CScriptLex('', self, lastPosition, self.dataEnd)

  def getPosition(self, pos):
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

  def __initAllVars__(self):
    self.name = None
    self.nextSibling = None
    self.prevSibling = None
    self.var = None
    self.owned = None

  # public
  def __init__(self, *args):
    self.__initAllVars__()
    if len(args) == 2 and\
        isinstance(args[0], CScriptVar) and\
        isinstance(args[1], basestring):
      var = args[0]
      name = args[1]
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
      self.init()
      self.flags = varFlags
      if varFlags & SCRIPTVAR_FLAGS.SCRIPTVAR_INTEGER:
        self.intData = int(varData)
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
      var = args[0]
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
    return findChildOrCreate(name).var

  def findChild(self, childName):
    v = self.firstChild
    while v:
      if v.name == childName:
        return v
      v = v.nextSibling
    return 0

  def findChildOrCreate(childName, varFlags=SCRIPTVAR_FLAGS.SCRIPTVAR_UNDEFINED):
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
      v = addChild(childName, child)

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

  def removeAllChildren():
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
      if self.isNumber(link.name):
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
      return data
    if self.isDouble():
      buffer = '%f' % self.doubleData
      self.data = buffer
      return data
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
    self.data = TINYJS_BLANK_DATAk
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
    return self.flags&SCRIPTVAR_FLAGS.ORREISCRIPTVAR_INTEGER!=0

  def isDouble(self):
    return self.flags&SCRIPTVAR_FLAGS.EISCRIPTVAR_DOUBLE!=0

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
    return self.flags & ASSCRIPTVAR_NULL !=0

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
        copied
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
      copied
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

class CTinyJS(object):
  # public:
  def __inif__(self):
    pass

  def execute(self, code):
    pass
  """
  /** Evaluate the given code and return a link to a javascript object,
   * useful for (dangerous) JSON parsing. If nothing to return, will return
   * 'undefined' variable type. CScriptVarLink is returned as this will
   * automatically unref the result as it goes out of scope. If you want to
   * keep it, you must use ref() and unref() */
  """

  def evaluateComplex(self, code):
    pass
  """
  /** Evaluate the given code and return a string. If nothing to return, will return
   * 'undefined' */
  """

  def evaluate(self, code):
    pass
  """
  /// add a native function to be called from TinyJS
  /** example:
     \code
         void scRandInt(CScriptVar *c, void *userdata) { ... }
         tinyJS->addNative("function randInt(min, max)", scRandInt, 0);
     \endcode

     or

     \code
         void scSubstring(CScriptVar *c, void *userdata) { ... }
         tinyJS->addNative("function String.substring(lo, hi)", scSubstring, 0);
     \endcode
  */
  """

  def addNative(self, funcDesc, ptr, userdata):
    pass

  # /// Get the given variable specified by a path (var1.var2.etc), or return 0
  def getScriptVariable(self, path):
    pass

  # /// Get the value of the given variable, or return 0
  def getVariable(self, path):
    pass

  # /// set the value of the given variable, return trur if it exists and gets set
  def setVariable(self, path, varData):
    pass

  # /// Send all variables to stdout
  def trace(self):
    pass

  # private:
  # // parsing - in order of precedence
  def functionCall(self, execute, function, parent):
    pass

  def factor(self, execute):
    pass

  def unary(self, execute):
    pass

  def term(self, execute):
    pass

  def expression(self, execute):
    pass

  def shift(self, execute):
    pass

  def condition(self, execute):
    pass

  def logic(self, execute):
    pass

  def ternary(self, execute):
    pass

  def base(self, execute):
    pass

  def block(self, execute):
    pass

  def statement(self, execute):
    pass

  # // parsing utility functions
  def parseFunctionDefinition(self):
    pass

  def parseFunctionArguments(self, funcVar):
    pass

  def findInScopes(self, childName):
    # ///< Finds a child, looking recursively up the scopes
    pass

  # /// Look up in any parent classes of the given object
  def findInParentClasses(object, name):
    pass

