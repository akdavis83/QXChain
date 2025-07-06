"""
Post-Quantum Digital Signature System for QXChain
Implements Dilithium-like signature scheme for quantum resistance
"""

import hashlib
import os
from typing import Tuple, Optional
import json
from .kyber import Kyber1024


class QuantumSignature:
    """
    Post-quantum digital signature implementation
    Based on lattice-based cryptography principles
    """
    
    # Signature parameters
    N = 256
    Q = 8380417
    K = 4  # Number of polynomials in public key
    L = 4  # Number of polynomials in private key
    ETA = 2
    TAU = 39
    BETA = 78
    GAMMA1 = 1 << 17
    GAMMA2 = (Q - 1) // 88
    
    @classmethod
    def keygen(cls) -> Tuple[bytes, bytes]:
        """
        Generate a quantum-resistant key pair for digital signatures
        Returns: (public_key, private_key)
        """
        # Generate random seed
        seed = os.urandom(32)
        
        # Derive randomness
        rho = cls._shake256(seed, 32)
        rhoprime = cls._shake256(seed + b'\x01', 64)
        K_bytes = cls._shake256(seed + b'\x02', 32)
        
        # Generate matrix A
        A = cls._expand_matrix(rho)
        
        # Sample secret vectors
        s1 = cls._sample_in_ball(rhoprime[:32], cls.L)
        s2 = cls._sample_in_ball(rhoprime[32:], cls.K)
        
        # Compute t = As1 + s2
        t = cls._matrix_vector_mul(A, s1)
        t = cls._vector_add(t, s2)
        
        # Pack keys
        pk = cls._pack_public_key(rho, t)
        sk = cls._pack_private_key(rho, K_bytes, s1, s2, t)
        
        return pk, sk
    
    @classmethod
    def sign(cls, message: bytes, private_key: bytes) -> bytes:
        """
        Sign a message using the private key
        Returns: signature
        """
        # Unpack private key
        rho, K_bytes, s1, s2, t = cls._unpack_private_key(private_key)
        
        # Generate matrix A
        A = cls._expand_matrix(rho)
        
        # Hash message
        mu = cls._shake256(message + cls._pack_public_key(rho, t), 64)
        
        # Rejection sampling loop
        nonce = 0
        while True:
            # Sample mask
            y = cls._sample_mask(K_bytes + nonce.to_bytes(2, 'little'))
            
            # Compute w = Ay
            w = cls._matrix_vector_mul(A, y)
            w1 = cls._high_bits(w)
            
            # Compute challenge
            c = cls._sample_challenge(mu + cls._pack_w1(w1))
            
            # Compute z = y + cs1
            z = cls._vector_add(y, cls._scalar_vector_mul(c, s1))
            
            # Check bounds
            if cls._check_bounds(z, cls.GAMMA1 - cls.BETA):
                continue
            
            # Compute r0 = low_bits(w - cs2)
            cs2 = cls._scalar_vector_mul(c, s2)
            w_minus_cs2 = cls._vector_sub(w, cs2)
            r0 = cls._low_bits(w_minus_cs2)
            
            if cls._check_bounds(r0, cls.GAMMA2 - cls.BETA):
                continue
            
            # Valid signature found
            break
        
        return cls._pack_signature(c, z)
    
    @classmethod
    def verify(cls, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """
        Verify a signature using the public key
        Returns: True if valid, False otherwise
        """
        try:
            # Unpack public key and signature
            rho, t = cls._unpack_public_key(public_key)
            c, z = cls._unpack_signature(signature)
            
            # Check signature bounds
            if not cls._check_bounds(z, cls.GAMMA1 - cls.BETA):
                return False
            
            # Generate matrix A
            A = cls._expand_matrix(rho)
            
            # Hash message
            mu = cls._shake256(message + public_key, 64)
            
            # Compute Az - ct
            Az = cls._matrix_vector_mul(A, z)
            ct = cls._scalar_vector_mul(c, t)
            w_prime = cls._vector_sub(Az, ct)
            
            # Compute w1'
            w1_prime = cls._high_bits(w_prime)
            
            # Recompute challenge
            c_prime = cls._sample_challenge(mu + cls._pack_w1(w1_prime))
            
            return c == c_prime
            
        except Exception:
            return False
    
    @staticmethod
    def _shake256(data: bytes, length: int) -> bytes:
        """SHAKE-256 extendable output function"""
        from hashlib import shake_256
        return shake_256(data).digest(length)
    
    @classmethod
    def _expand_matrix(cls, rho: bytes) -> list:
        """Expand matrix A from seed rho"""
        A = []
        for i in range(cls.K):
            row = []
            for j in range(cls.L):
                seed = rho + bytes([j, i])
                poly = cls._sample_uniform_poly(seed)
                row.append(poly)
            A.append(row)
        return A
    
    @classmethod
    def _sample_uniform_poly(cls, seed: bytes) -> list:
        """Sample a uniform polynomial"""
        poly = [0] * cls.N
        stream = cls._shake256(seed, 3 * cls.N)
        
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
    def _sample_in_ball(cls, seed: bytes, length: int) -> list:
        """Sample polynomials with coefficients in {-eta, ..., eta}"""
        polys = []
        for i in range(length):
            poly_seed = seed + bytes([i])
            stream = cls._shake256(poly_seed, 64)
            poly = cls._cbd(stream, cls.ETA)
            polys.append(poly)
        return polys
    
    @classmethod
    def _sample_mask(cls, seed: bytes) -> list:
        """Sample mask polynomials"""
        polys = []
        for i in range(cls.L):
            poly_seed = seed + bytes([i])
            stream = cls._shake256(poly_seed, 5 * cls.N)
            poly = cls._sample_gamma1(stream)
            polys.append(poly)
        return polys
    
    @classmethod
    def _sample_challenge(cls, seed: bytes) -> list:
        """Sample challenge polynomial"""
        stream = cls._shake256(seed, 32)
        poly = [0] * cls.N
        
        # Sample TAU positions for non-zero coefficients
        positions = set()
        i = 0
        while len(positions) < cls.TAU and i < len(stream):
            pos = stream[i] % cls.N
            if pos not in positions:
                positions.add(pos)
                poly[pos] = 1 if (stream[i] >> 7) else -1
            i += 1
        
        return poly
    
    @classmethod
    def _cbd(cls, stream: bytes, eta: int) -> list:
        """Centered binomial distribution"""
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
    def _sample_gamma1(cls, stream: bytes) -> list:
        """Sample polynomial with coefficients in [-gamma1, gamma1]"""
        poly = [0] * cls.N
        for i in range(cls.N):
            # Simplified sampling (should use proper rejection sampling)
            byte_idx = i * 5 // 8
            if byte_idx + 4 < len(stream):
                val = int.from_bytes(stream[byte_idx:byte_idx+4], 'little')
                poly[i] = (val % (2 * cls.GAMMA1 + 1)) - cls.GAMMA1
        return poly
    
    @classmethod
    def _matrix_vector_mul(cls, A: list, v: list) -> list:
        """Matrix-vector multiplication"""
        result = []
        for i in range(len(A)):
            poly_sum = [0] * cls.N
            for j in range(len(v)):
                poly_prod = cls._poly_mul(A[i][j], v[j])
                poly_sum = cls._poly_add(poly_sum, poly_prod)
            result.append(poly_sum)
        return result
    
    @classmethod
    def _vector_add(cls, a: list, b: list) -> list:
        """Vector addition"""
        return [cls._poly_add(a[i], b[i]) for i in range(len(a))]
    
    @classmethod
    def _vector_sub(cls, a: list, b: list) -> list:
        """Vector subtraction"""
        return [cls._poly_sub(a[i], b[i]) for i in range(len(a))]
    
    @classmethod
    def _scalar_vector_mul(cls, c: list, v: list) -> list:
        """Scalar-vector multiplication"""
        return [cls._poly_mul(c, poly) for poly in v]
    
    @classmethod
    def _poly_add(cls, a: list, b: list) -> list:
        """Polynomial addition"""
        return [(a[i] + b[i]) % cls.Q for i in range(cls.N)]
    
    @classmethod
    def _poly_sub(cls, a: list, b: list) -> list:
        """Polynomial subtraction"""
        return [(a[i] - b[i]) % cls.Q for i in range(cls.N)]
    
    @classmethod
    def _poly_mul(cls, a: list, b: list) -> list:
        """Polynomial multiplication (simplified)"""
        result = [0] * cls.N
        for i in range(cls.N):
            for j in range(cls.N):
                if i + j < cls.N:
                    result[i + j] = (result[i + j] + a[i] * b[j]) % cls.Q
                else:
                    result[i + j - cls.N] = (result[i + j - cls.N] - a[i] * b[j]) % cls.Q
        return result
    
    @classmethod
    def _high_bits(cls, v: list) -> list:
        """Extract high bits"""
        return [cls._decompose_high(poly) for poly in v]
    
    @classmethod
    def _low_bits(cls, v: list) -> list:
        """Extract low bits"""
        return [cls._decompose_low(poly) for poly in v]
    
    @classmethod
    def _decompose_high(cls, poly: list) -> list:
        """Decompose polynomial to high bits"""
        return [(coeff + cls.GAMMA2) // (2 * cls.GAMMA2) for coeff in poly]
    
    @classmethod
    def _decompose_low(cls, poly: list) -> list:
        """Decompose polynomial to low bits"""
        return [coeff % (2 * cls.GAMMA2) - cls.GAMMA2 for coeff in poly]
    
    @classmethod
    def _check_bounds(cls, v: list, bound: int) -> bool:
        """Check if vector coefficients are within bounds"""
        for poly in v:
            for coeff in poly:
                if abs(coeff) >= bound:
                    return True
        return False
    
    @classmethod
    def _pack_public_key(cls, rho: bytes, t: list) -> bytes:
        """Pack public key"""
        data = rho
        for poly in t:
            for coeff in poly:
                data += coeff.to_bytes(3, 'little')
        return data
    
    @classmethod
    def _unpack_public_key(cls, pk: bytes) -> Tuple[bytes, list]:
        """Unpack public key"""
        rho = pk[:32]
        t = []
        offset = 32
        for i in range(cls.K):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(pk[offset:offset+3], 'little')
                poly.append(coeff)
                offset += 3
            t.append(poly)
        return rho, t
    
    @classmethod
    def _pack_private_key(cls, rho: bytes, K_bytes: bytes, s1: list, s2: list, t: list) -> bytes:
        """Pack private key"""
        data = rho + K_bytes
        for poly in s1:
            for coeff in poly:
                data += coeff.to_bytes(2, 'little', signed=True)
        for poly in s2:
            for coeff in poly:
                data += coeff.to_bytes(2, 'little', signed=True)
        for poly in t:
            for coeff in poly:
                data += coeff.to_bytes(3, 'little')
        return data
    
    @classmethod
    def _unpack_private_key(cls, sk: bytes) -> Tuple[bytes, bytes, list, list, list]:
        """Unpack private key"""
        rho = sk[:32]
        K_bytes = sk[32:64]
        
        offset = 64
        s1 = []
        for i in range(cls.L):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(sk[offset:offset+2], 'little', signed=True)
                poly.append(coeff)
                offset += 2
            s1.append(poly)
        
        s2 = []
        for i in range(cls.K):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(sk[offset:offset+2], 'little', signed=True)
                poly.append(coeff)
                offset += 2
            s2.append(poly)
        
        t = []
        for i in range(cls.K):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(sk[offset:offset+3], 'little')
                poly.append(coeff)
                offset += 3
            t.append(poly)
        
        return rho, K_bytes, s1, s2, t
    
    @classmethod
    def _pack_signature(cls, c: list, z: list) -> bytes:
        """Pack signature"""
        data = b''
        for coeff in c:
            data += coeff.to_bytes(1, 'little', signed=True)
        for poly in z:
            for coeff in poly:
                data += coeff.to_bytes(3, 'little', signed=True)
        return data
    
    @classmethod
    def _unpack_signature(cls, sig: bytes) -> Tuple[list, list]:
        """Unpack signature"""
        c = []
        for i in range(cls.N):
            coeff = int.from_bytes(sig[i:i+1], 'little', signed=True)
            c.append(coeff)
        
        offset = cls.N
        z = []
        for i in range(cls.L):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(sig[offset:offset+3], 'little', signed=True)
                poly.append(coeff)
                offset += 3
            z.append(poly)
        
        return c, z
    
    @classmethod
    def _pack_w1(cls, w1: list) -> bytes:
        """Pack w1 for hashing"""
        data = b''
        for poly in w1:
            for coeff in poly:
                data += coeff.to_bytes(1, 'little')
        return data