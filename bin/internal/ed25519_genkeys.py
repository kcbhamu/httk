#! /usr/bin/env python
#
# This code is a (slightly modified) version of the code published here:
#   http://ed25519.cr.yp.to/python/ed25519.py (fetched 2015-02-15)
# And described here:
#   http://ed25519.cr.yp.to/software.html (fetched 2015-02-15)
#
# Specifically, the authors state:
# "Copyrights: The Ed25519 software is in the public domain."
#
# The modification made here to the code published at ed25519.cr.yp.to are not regarded 
# by its author to be significant enough to consitute a derivative work, protected on its own,
# and thus the same rights should hold that applies to the published files.

import hashlib

b = 256
q = 2**255 - 19
l = 2**252 + 27742317777372353535851937790883648493

def H(m):
    return hashlib.sha512(m).digest()

def expmod(b,e,m):
    if e == 0: return 1
    t = expmod(b,e/2,m)**2 % m
    if e & 1: t = (t*b) % m
    return t

def inv(x):
    return expmod(x,q-2,q)

d = -121665 * inv(121666)
I = expmod(2,(q-1)/4,q)

def xrecover(y):
    xx = (y*y-1) * inv(d*y*y+1)
    x = expmod(xx,(q+3)/8,q)
    if (x*x - xx) % q != 0: x = (x*I) % q
    if x % 2 != 0: x = q-x
    return x

By = 4 * inv(5)
Bx = xrecover(By)
B = [Bx % q,By % q]

def edwards(P,Q):
    x1 = P[0]
    y1 = P[1]
    x2 = Q[0]
    y2 = Q[1]
    x3 = (x1*y2+x2*y1) * inv(1+d*x1*x2*y1*y2)
    y3 = (y1*y2+x1*x2) * inv(1-d*x1*x2*y1*y2)
    return [x3 % q,y3 % q]

def scalarmult(P,e):
    if e == 0: return [0,1]
    Q = scalarmult(P,e/2)
    Q = edwards(Q,Q)
    if e & 1: Q = edwards(Q,P)
    return Q

def encodeint(y):
    bits = [(y >> i) & 1 for i in range(b)]
    return ''.join([chr(sum([bits[i * 8 + j] << j for j in range(8)])) for i in range(b/8)])

def encodepoint(P):
    x = P[0]
    y = P[1]
    bits = [(y >> i) & 1 for i in range(b - 1)] + [x & 1]
    return ''.join([chr(sum([bits[i * 8 + j] << j for j in range(8)])) for i in range(b/8)])

def bit(h,i):
    return (ord(h[i/8]) >> (i%8)) & 1

def publickey(sk):
    h = H(sk)
    a = 2**(b-2) + sum(2**i * bit(h,i) for i in range(3,b-2))
    A = scalarmult(B,a)
    return encodepoint(A)

def Hint(m):
    h = H(m)
    return sum(2**i * bit(h,i) for i in range(2*b))

def signature(m,sk,pk):
    h = H(sk)
    a = 2**(b-2) + sum(2**i * bit(h,i) for i in range(3,b-2))
    r = Hint(''.join([h[i] for i in range(b/8,b/4)]) + m)
    R = scalarmult(B,r)
    S = (r + Hint(encodepoint(R) + pk + m) * a) % l
    return encodepoint(R) + encodeint(S)

def isoncurve(P):
    x = P[0]
    y = P[1]
    return (-x*x + y*y - 1 - d*x*x*y*y) % q == 0

def decodeint(s):
    return sum(2**i * bit(s,i) for i in range(0,b))

def decodepoint(s):
    y = sum(2**i * bit(s,i) for i in range(0,b-1))
    x = xrecover(y)
    if x & 1 != bit(s,b-1): x = q-x
    P = [x,y]
    if not isoncurve(P): raise Exception("decoding point that is not on curve")
    return P

def checkvalid(s,m,pk):
    if len(s) != b/4: raise Exception("signature length is wrong")
    if len(pk) != b/8: raise Exception("public-key length is wrong")
    R = decodepoint(s[0:b/8])
    A = decodepoint(pk)
    S = decodeint(s[b/8:b/4])
    h = Hint(encodepoint(R) + pk + m)
    if scalarmult(B,S) != edwards(R,scalarmult(A,h)):
        #raise Exception("signature does not pass verification")
        return False
    else:
        return True

# Extra checks
assert b >= 10
assert 8 * len(H("hash input")) == 2 * b
assert expmod(2,q-1,q) == 1
assert q % 4 == 1
assert expmod(2,l-1,l) == 1
assert l >= 2**(b-4)
assert l <= 2**(b-3)
assert expmod(d,(q-1)/2,q) == q-1
assert expmod(I,2,q) == q-1
assert isoncurve(B)
assert scalarmult(B,l) == [0,1]

import base64, sys, os

if len(sys.argv) < 3:
    sys.exit('Usage: %s public-key-file private-key-file' % sys.argv[0])

public_key_path = sys.argv[1]
secret_key_path = sys.argv[2]
if len(sys.argv)>=4:
    comment=sys.argv[3]
else:
    comment=""

try:
    secret_key = os.urandom(64)
except NotImplementedError:
    raise Exception("crypto.generate_keys: Running on a system without a safe random number generator, cannot create safe cryptographic keys on this system.")

public_key = publickey(secret_key)

b64secret_key = base64.b64encode(secret_key)
b64public_key = base64.b64encode(public_key)

pubfile=open(public_key_path,'w')
pubfile.write(b64public_key)
pubfile.write("\n")
pubfile.write(comment)
pubfile.close()

secfile=open(secret_key_path,'w')
secfile.write(b64secret_key)
secfile.close()    

    


