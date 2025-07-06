"""
Kyber1024 Post-Quantum Key Encapsulation Mechanism
Adapted from QuantumR-Chain implementation for QXChain
"""

import os
import hashlib
from typing import Tuple, List
import numpy as np


class Kyber1024:
    """
    Kyber1024 implementation for quantum-resistant key encapsulation
    """
    
    # Kyber1024 parameters
    N = 256
    Q = 3329
    K = 4  # Kyber1024 uses k=4
    ETA1 = 2
    ETA2 = 2
    DU = 11
    DV = 5
    
    # Polynomial ring operations
    ZETA = [2285, 2571, 2970, 1812, 1493, 1422, 287, 202, 3158, 622, 1577, 182, 962, 2127, 1855, 1468, 573, 2004, 264, 383, 2500, 1458, 1727, 3199, 2648, 1017, 732, 608, 1787, 411, 3124, 1758, 1223, 652, 2777, 1015, 2036, 1491, 3047, 1785, 516, 3321, 3009, 2663, 1711, 2167, 126, 1469, 2476, 3239, 3058, 830, 107, 1908, 3082, 2378, 2931, 961, 1821, 2604, 448, 2264, 677, 2054, 2226, 430, 555, 843, 2078, 871, 1550, 105, 422, 587, 177, 3094, 3038, 2869, 1574, 1653, 3083, 778, 1159, 3182, 2552, 1483, 2727, 1119, 1739, 644, 2457, 349, 418, 329, 3173, 3254, 817, 1097, 603, 610, 1322, 2044, 1864, 384, 2114, 3193, 1218, 1994, 2455, 220, 2142, 1670, 2144, 1799, 2051, 794, 1819, 2475, 2459, 478, 3221, 3021, 996, 991, 958, 1869, 1522, 1628]
    
    @classmethod
    def keygen(cls) -> Tuple[bytes, bytes]:
        """
        Generate a Kyber1024 key pair
        Returns: (public_key, private_key)
        """
        # Generate random seed
        seed = os.urandom(32)
        
        # Derive keys from seed using SHAKE-128
        rho = cls._shake128(seed, 32)
        sigma = cls._shake128(seed + b'\x01', 32)
        
        # Generate matrix A from rho
        A = cls._gen_matrix(rho)
        
        # Generate secret vector s and error vector e
        s = cls._sample_poly_cbd(sigma, cls.ETA1, cls.K)
        e = cls._sample_poly_cbd(sigma + b'\x01', cls.ETA1, cls.K)
        
        # Compute t = As + e
        t = cls._matrix_vector_mul(A, s)
        t = cls._vector_add(t, e)
        
        # Pack keys
        pk = cls._pack_public_key(t, rho)
        sk = cls._pack_private_key(s)
        
        return pk, sk
    
    @classmethod
    def encaps(cls, pk: bytes) -> Tuple[bytes, bytes]:
        """
        Encapsulate a shared secret using the public key
        Returns: (ciphertext, shared_secret)
        """
        # Unpack public key
        t, rho = cls._unpack_public_key(pk)
        
        # Generate random message
        m = os.urandom(32)
        
        # Hash message to get randomness
        r = cls._shake128(m, 32)
        
        # Generate matrix A from rho
        A = cls._gen_matrix(rho)
        
        # Sample polynomials
        r_vec = cls._sample_poly_cbd(r, cls.ETA1, cls.K)
        e1 = cls._sample_poly_cbd(r + b'\x01', cls.ETA2, cls.K)
        e2 = cls._sample_poly_cbd(r + b'\x02', cls.ETA2, 1)[0]
        
        # Compute ciphertext
        u = cls._matrix_transpose_vector_mul(A, r_vec)
        u = cls._vector_add(u, e1)
        
        v = cls._vector_dot_product(t, r_vec)
        v = cls._poly_add(v, e2)
        v = cls._poly_add(v, cls._decode_message(m))
        
        # Pack ciphertext
        ct = cls._pack_ciphertext(u, v)
        
        # Derive shared secret
        ss = cls._kdf(m + cls._sha3_256(ct))
        
        return ct, ss
    
    @classmethod
    def decaps(cls, ct: bytes, sk: bytes) -> bytes:
        """
        Decapsulate the shared secret using the private key
        Returns: shared_secret
        """
        # Unpack private key and ciphertext
        s = cls._unpack_private_key(sk)
        u, v = cls._unpack_ciphertext(ct)
        
        # Decrypt message
        m_prime = cls._vector_dot_product(s, u)
        m_prime = cls._poly_sub(v, m_prime)
        m = cls._encode_message(m_prime)
        
        # Derive shared secret
        ss = cls._kdf(m + cls._sha3_256(ct))
        
        return ss
    
    @staticmethod
    def _shake128(data: bytes, length: int) -> bytes:
        """SHAKE-128 extendable output function"""
        from hashlib import shake_128
        return shake_128(data).digest(length)
    
    @staticmethod
    def _sha3_256(data: bytes) -> bytes:
        """SHA3-256 hash function"""
        return hashlib.sha3_256(data).digest()
    
    @staticmethod
    def _kdf(data: bytes) -> bytes:
        """Key derivation function"""
        return hashlib.sha3_256(data).digest()
    
    @classmethod
    def _gen_matrix(cls, rho: bytes) -> List[List[List[int]]]:
        """Generate matrix A from seed rho"""
        A = []
        for i in range(cls.K):
            row = []
            for j in range(cls.K):
                seed = rho + bytes([j, i])
                poly = cls._sample_uniform_poly(seed)
                row.append(poly)
            A.append(row)
        return A
    
    @classmethod
    def _sample_uniform_poly(cls, seed: bytes) -> List[int]:
        """Sample a uniform polynomial from seed"""
        poly = [0] * cls.N
        stream = cls._shake128(seed, 3 * cls.N)
        
        j = 0
        for i in range(0, len(stream), 3):
            if j >= cls.N:
                break
            
            d1 = stream[i] + 256 * (stream[i + 1] % 16)
            d2 = (stream[i + 1] // 16) + 16 * stream[i + 2]
            
            if d1 < cls.Q:
                poly[j] = d1
                j += 1
            if d2 < cls.Q and j < cls.N:
                poly[j] = d2
                j += 1
        
        return poly
    
    @classmethod
    def _sample_poly_cbd(cls, seed: bytes, eta: int, k: int) -> List[List[int]]:
        """Sample polynomials from centered binomial distribution"""
        polys = []
        for i in range(k):
            poly_seed = seed + bytes([i])
            stream = cls._shake128(poly_seed, 64 * eta)
            poly = cls._cbd(stream, eta)
            polys.append(poly)
        return polys
    
    @classmethod
    def _cbd(cls, stream: bytes, eta: int) -> List[int]:
        """Centered binomial distribution sampling"""
        poly = [0] * cls.N
        for i in range(cls.N):
            a = 0
            b = 0
            for j in range(eta):
                bit_pos = 2 * eta * i + j
                byte_pos = bit_pos // 8
                bit_offset = bit_pos % 8
                if byte_pos < len(stream):
                    a += (stream[byte_pos] >> bit_offset) & 1
                
                bit_pos = 2 * eta * i + eta + j
                byte_pos = bit_pos // 8
                bit_offset = bit_pos % 8
                if byte_pos < len(stream):
                    b += (stream[byte_pos] >> bit_offset) & 1
            
            poly[i] = (a - b) % cls.Q
        return poly
    
    @classmethod
    def _matrix_vector_mul(cls, A: List[List[List[int]]], v: List[List[int]]) -> List[List[int]]:
        """Matrix-vector multiplication in polynomial ring"""
        result = []
        for i in range(len(A)):
            poly_sum = [0] * cls.N
            for j in range(len(v)):
                poly_prod = cls._poly_mul(A[i][j], v[j])
                poly_sum = cls._poly_add(poly_sum, poly_prod)
            result.append(poly_sum)
        return result
    
    @classmethod
    def _matrix_transpose_vector_mul(cls, A: List[List[List[int]]], v: List[List[int]]) -> List[List[int]]:
        """Matrix transpose-vector multiplication"""
        result = []
        for j in range(len(A[0])):
            poly_sum = [0] * cls.N
            for i in range(len(A)):
                poly_prod = cls._poly_mul(A[i][j], v[i])
                poly_sum = cls._poly_add(poly_sum, poly_prod)
            result.append(poly_sum)
        return result
    
    @classmethod
    def _vector_add(cls, a: List[List[int]], b: List[List[int]]) -> List[List[int]]:
        """Vector addition"""
        return [cls._poly_add(a[i], b[i]) for i in range(len(a))]
    
    @classmethod
    def _vector_dot_product(cls, a: List[List[int]], b: List[List[int]]) -> List[int]:
        """Vector dot product"""
        result = [0] * cls.N
        for i in range(len(a)):
            poly_prod = cls._poly_mul(a[i], b[i])
            result = cls._poly_add(result, poly_prod)
        return result
    
    @classmethod
    def _poly_add(cls, a: List[int], b: List[int]) -> List[int]:
        """Polynomial addition"""
        return [(a[i] + b[i]) % cls.Q for i in range(cls.N)]
    
    @classmethod
    def _poly_sub(cls, a: List[int], b: List[int]) -> List[int]:
        """Polynomial subtraction"""
        return [(a[i] - b[i]) % cls.Q for i in range(cls.N)]
    
    @classmethod
    def _poly_mul(cls, a: List[int], b: List[int]) -> List[int]:
        """Polynomial multiplication using NTT"""
        # Simplified polynomial multiplication (should use NTT for efficiency)
        result = [0] * cls.N
        for i in range(cls.N):
            for j in range(cls.N):
                if i + j < cls.N:
                    result[i + j] = (result[i + j] + a[i] * b[j]) % cls.Q
                else:
                    # Reduction by x^n + 1
                    result[i + j - cls.N] = (result[i + j - cls.N] - a[i] * b[j]) % cls.Q
        return result
    
    @classmethod
    def _decode_message(cls, m: bytes) -> List[int]:
        """Decode message to polynomial"""
        poly = [0] * cls.N
        for i in range(32):
            for j in range(8):
                bit = (m[i] >> j) & 1
                if i * 8 + j < cls.N:
                    poly[i * 8 + j] = bit * (cls.Q // 2)
        return poly
    
    @classmethod
    def _encode_message(cls, poly: List[int]) -> bytes:
        """Encode polynomial to message"""
        m = bytearray(32)
        for i in range(cls.N):
            bit = 1 if poly[i] > cls.Q // 2 else 0
            byte_pos = i // 8
            bit_pos = i % 8
            if byte_pos < 32:
                m[byte_pos] |= bit << bit_pos
        return bytes(m)
    
    @classmethod
    def _pack_public_key(cls, t: List[List[int]], rho: bytes) -> bytes:
        """Pack public key"""
        # Simplified packing (should compress polynomials)
        data = rho
        for poly in t:
            for coeff in poly:
                data += coeff.to_bytes(2, 'little')
        return data
    
    @classmethod
    def _unpack_public_key(cls, pk: bytes) -> Tuple[List[List[int]], bytes]:
        """Unpack public key"""
        rho = pk[:32]
        t = []
        offset = 32
        for i in range(cls.K):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(pk[offset:offset+2], 'little')
                poly.append(coeff)
                offset += 2
            t.append(poly)
        return t, rho
    
    @classmethod
    def _pack_private_key(cls, s: List[List[int]]) -> bytes:
        """Pack private key"""
        data = b''
        for poly in s:
            for coeff in poly:
                data += coeff.to_bytes(2, 'little')
        return data
    
    @classmethod
    def _unpack_private_key(cls, sk: bytes) -> List[List[int]]:
        """Unpack private key"""
        s = []
        offset = 0
        for i in range(cls.K):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(sk[offset:offset+2], 'little')
                poly.append(coeff)
                offset += 2
            s.append(poly)
        return s
    
    @classmethod
    def _pack_ciphertext(cls, u: List[List[int]], v: List[int]) -> bytes:
        """Pack ciphertext"""
        data = b''
        for poly in u:
            for coeff in poly:
                data += coeff.to_bytes(2, 'little')
        for coeff in v:
            data += coeff.to_bytes(2, 'little')
        return data
    
    @classmethod
    def _unpack_ciphertext(cls, ct: bytes) -> Tuple[List[List[int]], List[int]]:
        """Unpack ciphertext"""
        u = []
        offset = 0
        for i in range(cls.K):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(ct[offset:offset+2], 'little')
                poly.append(coeff)
                offset += 2
            u.append(poly)
        
        v = []
        for j in range(cls.N):
            coeff = int.from_bytes(ct[offset:offset+2], 'little')
            v.append(coeff)
            offset += 2
        
        return u, v