"""
  tinyjs.py
  ~~~~~~~~~

  author: atupal
  email: me@atupal.org
  time: 12/9/2014
"""

TINYJS_H = 1
TINYJS_CALL_STACK = 1
_CRTDBG_MAP_ALLOC = 1

TRACE = 'printf'

TINYJS_LOOP_MAX_ITERATIONS = 8192

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

  LEX_R_LIST_END = -1# always the last entry


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
  def __init__(self):
    super(CScriptException, self).__init__()

class CScriptLex(object):

  # public method
  def __init__(self, ):
    pass

  def match(self, pos):
    pass

  @classmethod
  def getTokenStr(self, token):
    pass

  def rest(self):
    pass

  def getSubString(self, pos):
    pass

  def getSubLex(self, lastPosition):
    pass

  def getPosition(self, lastPosition):
    pass

  # protect method
  def getNextCh(self):
    pass

  def getNextToken(self):
    pass

class CScriptVar(object):

  def __init__(self):
    pass

class CScriptVarLink(object):

  # public
  def __init__(self):
    pass

  def replaceWith(self, newVar):
    pass

  def getIntName(self):
    pass

  def setIntName(self, n):
    pass

class CScriptVar(object):

  # public
  def __init__(self):
    pass

  def getReturnVar(self):
    pass

  def setReturnVar(self, var):
    pass

  def getParameter(self, name):
    pass

  def findChild(childName):
    pass

  def findChildOrCreate(childName, varFlags=SCRIPTVAR_FLAGS.SCRIPTVAR_UNDEFINED):
    pass

  def findChildOrCreateByPath(self, path):
    pass

  def addChild(self, childName, child=None):
    pass

  def addChildNoDup(self, childName, child=None):
    pass

  def removeChild(self, child):
    pass

  def removeLink(self, link):
    pass

  def removeAllChildren():
    pass

  def getArrayIndex(self, idx):
    pass

  def setArrayIndex(self, idx, value):
    pass
  
  def getArrayLength(self):
    pass

  def getChildren(self):
    pass

  def getInt(self):
    pass

  def getBool(self):
    return self.getInt() != 0

  def getDouble(self):
    pass

  def getString(self):
    pass

  def getParsableString(self):
    pass # ///< get Data as a parsable javascript string

  def setInt(self, num):
    pass

  def setDouble(self, val):
    pass

  def setString(self, str):
    pass

  def setUndefined(self):
    pass

  def setArray(self):
    pass

  def equals(self, v):
    pass

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
    pass # ///< do a maths op with another script variable

  def copyValue(val):
    pass # ///< copy the value from the value given

  def deepCopy(self):
    pass # ///< deep copy this node and return the result

  def trace(indentStr = "", name = ""):
    pass # ///< Dump out the contents of this using trace

  def getFlagsAsString(self):
    pass # ///< For debugging - just dump a string version of the flags

  def getJSON(destination, linePrefix=""):
    pass # ///< Write out all the JS code needed to recreate this script variable to the stream (as JSON)

  def setCallback(callback, userdata):
    pass # ///< Set the callback for native functions

  # /// For memory management/garbage collection
  def ref(self):
    pass # ///< Add reference to this variable

  def unref(self):
    pass # ///< Remove a reference, and delete this variable if required

  def getRefs(self):
    pass # ///< Get the number of references to this script variable

  # protect

  def init(self):
    pass # ///< initialisation of data members

  # /** Copy the basic data and flags from the variable given, with no
  # * children. Should be used internally only - by copyValue and deepCopy */
  def copySimpleData(val):
    pass


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

