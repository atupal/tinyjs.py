import math

k_E =                 math.exp(1.0)
k_PI =               3.1415926535897932384626433832795

def F_ABS(a):
  # ((a)>=0 ? (a) : (-(a)))
  return abs(a)
def F_MIN(a,b):
  # ((a)>(b) ? (b) : (a))
  return min(a, b)
def F_MAX(a,b):
  # ((a)>(b) ? (a) : (b))
  return max(a, b)
def F_SGN(a):
  # ((a)>0 ? 1 : ((a)<0 ? -1 : 0 ))
  if a > 0:
    return 1
  if a < 0:
    return -1
  return 0
def F_RNG(a,min,max):
  # ((a)<(min) ? min : ((a)>(max) ? max : a ))
  if a < min:
    return min
  if a > max:
    return max
  return a
def F_ROUND(a):
  # ((a)>0 ? (int) ((a)+0.5) : (int) ((a)-0.5) )
  return round(a)
 
# CScriptVar shortcut macro
import inspect
def get_local_var(__var_name):
  __frame = inspect.currentframe()
  while __frame:
    if __var_name in __frame.f_locals:
      return __frame.f_locals[__var_name]
    __frame = __frame.f_back
  return None

def scIsInt(a)          : c = get_local_var('c'); return c.getParameter(a).isInt()
def scIsDouble(a)       : c = get_local_var('c'); return c.getParameter(a).isDouble()
def scGetInt(a)         : c = get_local_var('c'); return c.getParameter(a).getInt()
def scGetDouble(a)      : c = get_local_var('c'); return c.getParameter(a).getDouble()
def scReturnInt(a)      : c = get_local_var('c'); return c.getReturnVar().setInt(a)
def scReturnDouble(a)   : c = get_local_var('c'); return c.getReturnVar().setDouble(a)

# Math.abs(x) - returns absolute of given value
def scMathAbs(c, userdata):
  if scIsInt("a"): 
    scReturnInt( F_ABS( scGetInt("a") ) )
  elif scIsDouble("a"):
    scReturnDouble( F_ABS( scGetDouble("a") ) )

# Math.round(a) - returns nearest round of given value
def scMathRound(c, userdata):
  if scIsInt("a"):
    scReturnInt( F_ROUND( scGetInt("a") ) );
  elif scIsDouble("a"):
    scReturnDouble( F_ROUND( scGetDouble("a") ) )

# Math.min(a,b) - returns minimum of two given values 
def scMathMin(c, userdata):
  if (scIsInt("a")) and (scIsInt("b")):
    scReturnInt( F_MIN( scGetInt("a"), scGetInt("b") ) )
  else:
    scReturnDouble( F_MIN( scGetDouble("a"), scGetDouble("b") ) )

# Math.max(a,b) - returns maximum of two given values  
def scMathMax(c, userdata):
  if (scIsInt("a")) and (scIsInt("b")):
    scReturnInt( F_MAX( scGetInt("a"), scGetInt("b") ) )
  else:
    scReturnDouble( F_MAX( scGetDouble("a"), scGetDouble("b") ) )

# Math.range(x,a,b) - returns value limited between two given values  
def scMathRange(c, userdata):
  if (scIsInt("x")):
    scReturnInt( F_RNG( scGetInt("x"), scGetInt("a"), scGetInt("b") ) )
  else:
    scReturnDouble( F_RNG( scGetDouble("x"), scGetDouble("a"), scGetDouble("b") ) )

# Math.sign(a) - returns sign of given value (-1==negative,0=zero,1=positive)
def scMathSign(c, userdata):
  if scIsInt("a"):
    scReturnInt( F_SGN( scGetInt("a") ) )
  elif scIsDouble("a"):
    scReturnDouble( F_SGN( scGetDouble("a") ) )

# Math.PI() - returns PI value
def scMathPI(c, userdata):
    scReturnDouble(k_PI)

# Math.toDegrees(a) - returns degree value of a given angle in radians
def scMathToDegrees(c, userdata):
  scReturnDouble( (180.0/k_PI)*( scGetDouble("a") ) )

# Math.toRadians(a) - returns radians value of a given angle in degrees
def scMathToRadians(c, userdata):
  scReturnDouble( (k_PI/180.0)*( scGetDouble("a") ) )

# Math.sin(a) - returns trig. sine of given angle in radians
def scMathSin(c, userdata):
  scReturnDouble( sin( scGetDouble("a") ) )

# Math.asin(a) - returns trig. arcsine of given angle in radians
def scMathASin(c, userdata):
  scReturnDouble( asin( scGetDouble("a") ) )

# Math.cos(a) - returns trig. cosine of given angle in radians
def scMathCos(c, userdata):
  scReturnDouble( cos( scGetDouble("a") ) )

# Math.acos(a) - returns trig. arccosine of given angle in radians
def scMathACos(c, userdata):
  scReturnDouble( acos( scGetDouble("a") ) )

# Math.tan(a) - returns trig. tangent of given angle in radians
def scMathTan(c, userdata):
  scReturnDouble( tan( scGetDouble("a") ) )

# Math.atan(a) - returns trig. arctangent of given angle in radians
def scMathATan(c, userdata):
  scReturnDouble( atan( scGetDouble("a") ) )

# Math.sinh(a) - returns trig. hyperbolic sine of given angle in radians
def scMathSinh(c, userdata):
  scReturnDouble( sinh( scGetDouble("a") ) )

# Math.asinh(a) - returns trig. hyperbolic arcsine of given angle in radians
def scMathASinh(c, userdata):
  scReturnDouble( asinh( scGetDouble("a") ) )

# Math.cosh(a) - returns trig. hyperbolic cosine of given angle in radians
def scMathCosh(c, userdata):
  scReturnDouble( cosh( scGetDouble("a") ) )

# Math.acosh(a) - returns trig. hyperbolic arccosine of given angle in radians
def scMathACosh(c, userdata):
  scReturnDouble( acosh( scGetDouble("a") ) )

# Math.tanh(a) - returns trig. hyperbolic tangent of given angle in radians
def scMathTanh(c, userdata):
  scReturnDouble( tanh( scGetDouble("a") ) )

# Math.atan(a) - returns trig. hyperbolic arctangent of given angle in radians
def scMathATanh(c, userdata):
  scReturnDouble( atan( scGetDouble("a") ) )

# Math.E() - returns E Neplero value
def scMathE(c, userdata):
  scReturnDouble(k_E)

# Math.log(a) - returns natural logaritm (base E) of given value
def scMathLog(c, userdata):
  scReturnDouble( log( scGetDouble("a") ) )

# Math.log10(a) - returns logaritm(base 10) of given value
def scMathLog10(c, userdata):
  scReturnDouble( log10( scGetDouble("a") ) )

# Math.exp(a) - returns e raised to the power of a given number
def scMathExp(c, userdata):
  scReturnDouble( exp( scGetDouble("a") ) )

# Math.pow(a,b) - returns the result of a number raised to a power (a)^(b)
def scMathPow(c, userdata):
  scReturnDouble( pow( scGetDouble("a"), scGetDouble("b") ) )

# Math.sqr(a) - returns square of given value
def scMathSqr(c, userdata):
  scReturnDouble( ( scGetDouble("a") * scGetDouble("a") ) )

# Math.sqrt(a) - returns square root of given value
def scMathSqrt(c, userdata):
  scReturnDouble( sqrtf( scGetDouble("a") ) )

# ----------------------------------------------- Register Functions
def registerMathFunctions(tinyJS):
     
  # --- Math and Trigonometry functions ---
  tinyJS.addNative("function Math.abs(a)", scMathAbs, 0)
  tinyJS.addNative("function Math.round(a)", scMathRound, 0)
  tinyJS.addNative("function Math.min(a,b)", scMathMin, 0)
  tinyJS.addNative("function Math.max(a,b)", scMathMax, 0)
  tinyJS.addNative("function Math.range(x,a,b)", scMathRange, 0)
  tinyJS.addNative("function Math.sign(a)", scMathSign, 0)
  
  tinyJS.addNative("function Math.PI()", scMathPI, 0)
  tinyJS.addNative("function Math.toDegrees(a)", scMathToDegrees, 0)
  tinyJS.addNative("function Math.toRadians(a)", scMathToRadians, 0)
  tinyJS.addNative("function Math.sin(a)", scMathSin, 0)
  tinyJS.addNative("function Math.asin(a)", scMathASin, 0)
  tinyJS.addNative("function Math.cos(a)", scMathCos, 0)
  tinyJS.addNative("function Math.acos(a)", scMathACos, 0)
  tinyJS.addNative("function Math.tan(a)", scMathTan, 0)
  tinyJS.addNative("function Math.atan(a)", scMathATan, 0)
  tinyJS.addNative("function Math.sinh(a)", scMathSinh, 0)
  tinyJS.addNative("function Math.asinh(a)", scMathASinh, 0)
  tinyJS.addNative("function Math.cosh(a)", scMathCosh, 0)
  tinyJS.addNative("function Math.acosh(a)", scMathACosh, 0)
  tinyJS.addNative("function Math.tanh(a)", scMathTanh, 0)
  tinyJS.addNative("function Math.atanh(a)", scMathATanh, 0)
     
  tinyJS.addNative("function Math.E()", scMathE, 0)
  tinyJS.addNative("function Math.log(a)", scMathLog, 0)
  tinyJS.addNative("function Math.log10(a)", scMathLog10, 0)
  tinyJS.addNative("function Math.exp(a)", scMathExp, 0)
  tinyJS.addNative("function Math.pow(a,b)", scMathPow, 0)
  
  tinyJS.addNative("function Math.sqr(a)", scMathSqr, 0)
  tinyJS.addNative("function Math.sqrt(a)", scMathSqrt, 0)
