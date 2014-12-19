import sys
import os

from tinyjs_functions import registerFunctions
from tinyjs_math_functions import registerMathFunctions
from tinyjs import CTinyJS, CScriptVar, CScriptException, SCRIPTVAR_FLAGS

def run_test(filename):
  print "TEST %s " % filename,
  try:
    file = open(filename)
    buffer = file.read()
  except:
    print "Unable to open file! '%s'" % filename
    return False
  finally:
    file.close()

  s = CTinyJS()
  registerFunctions(s)
  registerMathFunctions(s)
  s.root.addChild("result", CScriptVar("0",SCRIPTVAR_FLAGS.SCRIPTVAR_INTEGER))
  try:
    s.execute(buffer)
  except CScriptException as e:
    print 'ERROR: %s' % e
  pass_test = s.root.getParameter("result").getBool()

  if pass_test:
    print 'PASS'
  else:
    fn = '%s.fail.js' % filename
    with open(fn, "wt") as f:
      symbols = ''
      symbols = s.root.getJSON(symbols)
      f.write(symbols)

    print 'FAIL - symbols written to %s' % fn

  return pass_test

def main():
  print 'TinyJS test runner'
  print 'USAGE:'
  print '   ./run_tests test.js       : run just one test'
  print '   ./run_tests               : run all tests'
  if len(sys.argv)==2:
    return not run_test(sys.argv[1])

  test_num = 1
  count = 0
  passed = 0

  while test_num<1000:
    fn = 'tests/test%03d.js' % test_num
    # check if the file exists - if not, assume we're at the end of our tests
    if not os.path.exists(fn):
      break

    if run_test(fn):
      passed += 1
    count += 1
    test_num += 1

  print 'Done. %d tests, %d pass, %d fail' % ( count, passed, count-passed )

  return 0


if __name__ == '__main__':
  exit(main())
