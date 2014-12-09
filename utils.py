"""
  utils.py
  ~~~~~~~~

  author: atupal
  email: me@atupal.org
  time: 12/9/2014

  some util function for tinyjs.py
"""

def isWhitespace(ch):
  return ch.isspace()

def isNumber(str):
  return str.isdigit()

def isNumeric(ch):
  return isNumber(ch)

def isHexadecimal(ch):
  return (ch >= '0' and ch <= '9') or\
            (ch >= 'a' and ch <= 'f') or\
            (ch >= 'A' and ch <= 'F')

def isAlpha(ch):
  return ch.isalpha() or ch == '_'

def isIDString(s):
  if not len(s):
    return False
  if not isAlpha(s[0]):
    return False
  for i in s[1:]:
    if not isAlpha(i) or not isNumeric(i):
      return False
  return True

def getJSString(str):
  nStr = str
  i = 0
  while i < len(nStr):
    replaceWith = ''
    replace = True

    if nStr[i] == '\\':
      replaceWith = '\\\\'
    elif nStr[i] == '\n':
      replaceWith = '\\n'
    elif nStr[i] == '\r':
      replaceWith = '\\r'
    elif nStr[i] == '\a':
      replaceWith = '\\a'
    elif nStr[i] == '"':
      replaceWith = '\\"'
    else:
      nCh = ord(nStr[i]) & 0xff
      if nCh < 32 or nCh > 127:
        buffer = ''
        print >>buffer, '\\x%02X' % nCh
        replaceWith = buffer
      else:
        replace = False

    if replace:
      nStr = nStr[:i] + replaceWith + nStr[i+1:]
      i += len(replaceWith)-1

    i += 1

  return '"' + nStr + '"'

def isAlphaNum(str):
  if len(str) == 0:
    return True
  if not isAlpha(str[0]):
    return False
  for w in str:
    if not isAlpha(w) or not isNumeric(w):
      return False
  return True

def test():
  print getJSString('"\\\n\r\a')

if __name__ == '__main__':
  test()
