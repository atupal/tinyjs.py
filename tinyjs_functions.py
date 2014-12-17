
from random import random, randint
from tinyjs import CScriptVar

#  ----------------------------------------------- Actual Functions
def scTrace(c, userdata):
  js = userdata
  js.root.trace()

def scObjectDump(c, *args):
  c.getParameter("this").trace("> ")

def scObjectClone(c, *args):
  obj = c.getParameter("this")
  c.getReturnVar().copyValue(obj)

def scMathRand(c, *args):
  c.getReturnVar().setDouble(random())

def scMathRandInt(c, *args):
  min = c.getParameter("min").getInt()
  max = c.getParameter("max").getInt()
  c.getReturnVar().setInt(randint(min, max))

def scCharToInt(c, *args):
  str = c.getParameter("ch").getString();
  val = 0
  if len(str)>0:
    val = ord(str[0])
  c.getReturnVar().setInt(val)

def scStringIndexOf(c, *args):
  str = c.getParameter("this").getString()
  search = c.getParameter("search").getString()
  p = str.find(search)
  c.getReturnVar().setInt(p)

def scStringSubstring(c, *args):
  str = c.getParameter("this").getString()
  lo = c.getParameter("lo").getInt()
  hi = c.getParameter("hi").getInt()

  c.getReturnVar().setString(str[lo:l])

def scStringCharAt(c, *args):
  str = c.getParameter("this").getString()
  p = c.getParameter("pos").getInt()
  if p>=0 and p<len(str):
    c.getReturnVar().setString(str[p])
  else:
    c.getReturnVar().setString("")

def scStringCharCodeAt(c, *args):
    str = c.getParameter("this").getString()
    p = c.getParameter("pos").getInt()
    if p>=0 and p<len(str):
      c.getReturnVar().setInt(ord(str[p]))
    else:
      c.getReturnVar().setInt(0)

def scStringSplit(c, *args):
  str = c.getParameter("this").getString()
  sep = c.getParameter("separator").getString()
  result = c.getReturnVar()
  result.setArray()
  length = 0

  sp = str.split(sep)
  for s in sp:
    result.setArrayIndex(length, CScriptVar(s))
    length += 1

def scStringFromCharCode(c, *args):
  str = chr(c.getParameter("char").getInt())
  c.getReturnVar().setString(str);

def scIntegerParseInt(c, *args):
  str = c.getParameter("str").getString();
  c.getReturnVar().setInt(int(str))

def scIntegerValueOf(c, *args):
  str = c.getParameter("str").getString()

  val = 0
  if len(str)==1:
    val = ord(str[0])
  c.getReturnVar().setInt(val)

def scJSONStringify(c, *args):
  # TODO std::ostringstream result;
  c.getParameter("obj").getJSON(result);
  c.getReturnVar().setString(result.str())

def scExec(c, data):
  tinyJS = data
  str = c.getParameter("jsCode").getString()
  tinyJS.execute(str)

def scEval(c, data):
  tinyJS = data
  str = c.getParameter("jsCode").getString()
  c.setReturnVar(tinyJS.evaluateComplex(str).var)

def scArrayContains(c, data):
  obj = c.getParameter("obj")
  v = c.getParameter("this").firstChild

  contains = False
  while v:
    if (v.var.equals(obj)):
      contains = True
      break
    v = v.nextSibling

  c.getReturnVar().setInt(contains)

def scArrayRemove(c, data):
  obj = c.getParameter("obj")
  removedIndices = []
  # remove
  v = c.getParameter("this").firstChild
  while v:
    if v.var.equals(obj):
      removedIndices.append(v.getIntName())
    v = v.nextSibling
  # renumber
  v = c.getParameter("this").firstChild
  while v:
    n = v.getIntName()
    newn = n
    for i in xrange(len(removedIndices)):
      if n>=removedIndices[i]:
        newn -= 1
    if newn!=n:
      v.setIntName(newn)
    v = v.nextSibling

def scArrayJoin(c, data):
  sep = c.getParameter("separator").getString()
  arr = c.getParameter("this")

  tmp_arr = []
  l = arr.getArrayLength()
  for i in xrange(l):
    tmp_arr.append(arr.getArrayIndex(i).getString())

  c.getReturnVar().setString(sep.join(tmp_arr));

# ----------------------------------------------- Register Functions
def registerFunctions(tinyJS):
    tinyJS.addNative("function exec(jsCode)", scExec, tinyJS) # execute the given code
    tinyJS.addNative("function eval(jsCode)", scEval, tinyJS) # execute the given string (an expression) and return the result
    tinyJS.addNative("function trace()", scTrace, tinyJS)
    tinyJS.addNative("function Object.dump()", scObjectDump, 0)
    tinyJS.addNative("function Object.clone()", scObjectClone, 0)
    tinyJS.addNative("function Math.rand()", scMathRand, 0)
    tinyJS.addNative("function Math.randInt(min, max)", scMathRandInt, 0)
    tinyJS.addNative("function charToInt(ch)", scCharToInt, 0) #  convert a character to an int - get its value
    tinyJS.addNative("function String.indexOf(search)", scStringIndexOf, 0) # find the position of a string in a string, -1 if not
    tinyJS.addNative("function String.substring(lo,hi)", scStringSubstring, 0)
    tinyJS.addNative("function String.charAt(pos)", scStringCharAt, 0)
    tinyJS.addNative("function String.charCodeAt(pos)", scStringCharCodeAt, 0)
    tinyJS.addNative("function String.fromCharCode(char)", scStringFromCharCode, 0)
    tinyJS.addNative("function String.split(separator)", scStringSplit, 0)
    tinyJS.addNative("function Integer.parseInt(str)", scIntegerParseInt, 0) # string to int
    tinyJS.addNative("function Integer.valueOf(str)", scIntegerValueOf, 0) # value of a single character
    tinyJS.addNative("function JSON.stringify(obj, replacer)", scJSONStringify, 0) # convert to JSON. replacer is ignored at the moment
    # JSON.parse is left out as you can (unsafely!) use eval instead
    tinyJS.addNative("function Array.contains(obj)", scArrayContains, 0)
    tinyJS.addNative("function Array.remove(obj)", scArrayRemove, 0)
    tinyJS.addNative("function Array.join(separator)", scArrayJoin, 0)
