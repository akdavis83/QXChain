"""
Post-Quantum Digital Signature System for QXChain
Implements CRYSTALS-Dilithium for quantum-resistant signatures
"""

import hashlib
import os
from typing import Tuple, List
import json
from .kyber import Kyber1024


class QuantumSignature:
    """
    Quantum-resistant digital signature system using Dilithium-like construction
    """
    
    # Dilithium parameters (simplified)
    N = 256
    Q = 8380417
    K = 4  # Security level 2
    L = 4
    ETA = 2
    TAU = 39
    BETA = 78
    GAMMA1 = 1 << 17
    GAMMA2 = (Q - 1) // 88
    
    @classmethod
    def keygen(cls) -> Tuple[bytes, bytes]:
        """
        Generate quantum-resistant signature key pair
        Returns: (public_key, private_key)
        """
        # Generate random seed
        seed = os.urandom(32)
        
        # Expand seed
        rho = cls._shake256(seed, 32)
        rhoprime = cls._shake256(seed + b'\x01', 64)
        K_seed = cls._shake256(seed + b'\x02', 32)
        
        # Generate matrix A
        A = cls._expand_A(rho)
        
        # Sample secret vectors
        s1 = cls._sample_in_ball(rhoprime[:32], cls.L)
        s2 = cls._sample_in_ball(rhoprime[32:], cls.K)
        
        # Compute t = As1 + s2
        t = cls._matrix_vector_mul(A, s1)
        t = cls._vector_add(t, s2)
        
        # Pack keys
        pk = cls._pack_public_key(rho, t)
        sk = cls._pack_private_key(rho, K_seed, s1, s2, t)
        
        return pk, sk
    
    @classmethod
    def sign(cls, message: bytes, sk: bytes) -> bytes:
        """
        Sign a message with quantum-resistant signature
        """
        # Unpack private key
        rho, K_seed, s1, s2, t = cls._unpack_private_key(sk)
        
        # Hash message
        mu = cls._sha3_256(message)
        
        # Generate randomness
        kappa = 0
        while True:
            # Sample mask
            rhoprime = cls._shake256(K_seed + mu + kappa.to_bytes(2, 'little'), 64)
            y = cls._sample_mask(rhoprime, cls.L)
            
            # Compute w = Ay
            A = cls._expand_A(rho)
            w = cls._matrix_vector_mul(A, y)
            w1 = cls._high_bits(w)
            
            # Compute challenge
            c_tilde = cls._sha3_256(mu + cls._pack_w1(w1))
            c = cls._sample_in_ball(c_tilde, cls.TAU)
            
            # Compute z = y + cs1
            z = cls._vector_add(y, cls._scalar_vector_mul(c, s1))
            
            # Check bounds
            if cls._infinity_norm(z) >= cls.GAMMA1 - cls.BETA:
                kappa += 1
                continue
            
            # Compute hint
            r0 = cls._low_bits(cls._vector_sub(w, cls._scalar_vector_mul(c, s2)))
            if cls._infinity_norm(r0) >= cls.GAMMA2 - cls.BETA:
                kappa += 1
                continue
            
            h = cls._make_hint(-c, w, cls._scalar_vector_mul(c, s2))
            
            # Pack signature
            return cls._pack_signature(c_tilde, z, h)
    
    @classmethod
    def verify(cls, message: bytes, signature: bytes, pk: bytes) -> bool:
        """
        Verify a quantum-resistant signature
        """
        try:
            # Unpack public key and signature
            rho, t = cls._unpack_public_key(pk)
            c_tilde, z, h = cls._unpack_signature(signature)
            
            # Check signature bounds
            if cls._infinity_norm(z) >= cls.GAMMA1 - cls.BETA:
                return False
            
            # Reconstruct challenge
            c = cls._sample_in_ball(c_tilde, cls.TAU)
            
            # Compute w' = Az - ct
            A = cls._expand_A(rho)
            w_prime = cls._vector_sub(
                cls._matrix_vector_mul(A, z),
                cls._scalar_vector_mul(c, t)
            )
            
            # Use hint to recover w1
            w1 = cls._use_hint(h, w_prime)
            
            # Verify challenge
            mu = cls._sha3_256(message)
            c_tilde_prime = cls._sha3_256(mu + cls._pack_w1(w1))
            
            return c_tilde == c_tilde_prime
            
        except Exception:
            return False
    
    @staticmethod
    def _shake256(data: bytes, length: int) -> bytes:
        """SHAKE-256 extendable output function"""
        from hashlib import shake_256
        return shake_256(data).digest(length)
    
    @staticmethod
    def _sha3_256(data: bytes) -> bytes:
        """SHA3-256 hash function"""
        return hashlib.sha3_256(data).digest()
    
    @classmethod
    def _expand_A(cls, rho: bytes) -> List[List[List[int]]]:
        """Expand matrix A from seed"""
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
    def _sample_uniform_poly(cls, seed: bytes) -> List[int]:
        """Sample uniform polynomial"""
        poly = [0] * cls.N
        stream = cls._shake256(seed, 5 * cls.N)
        
        j = 0
        for i in range(0, len(stream), 5):
            if j >= cls.N:
                break
            
            # Extract coefficient
            coeff = 0
            for k in range(5):
                if i + k < len(stream):
                    coeff += stream[i + k] << (8 * k)
            
            coeff = coeff % cls.Q
            if coeff < cls.Q:
                poly[j] = coeff
                j += 1
        
        return poly
    
    @classmethod
    def _sample_in_ball(cls, seed: bytes, tau: int) -> List[int]:
        """Sample polynomial with coefficients in {-1, 0, 1}"""
        poly = [0] * cls.N
        stream = cls._shake256(seed, 8 + tau)
        
        signs = stream[0]
        pos = 8
        
        for i in range(cls.N - tau, cls.N):
            j = stream[pos] % (i + 1)
            pos += 1
            
            poly[i] = poly[j]
            poly[j] = 1 if (signs >> (i - (cls.N - tau))) & 1 else -1
        
        return poly
    
    @classmethod
    def _sample_mask(cls, seed: bytes, l: int) -> List[List[int]]:
        """Sample masking polynomials"""
        polys = []
        for i in range(l):
            poly_seed = seed + bytes([i])
            stream = cls._shake256(poly_seed, cls.N * 3)
            poly = []
            
            for j in range(cls.N):
                # Sample from [-GAMMA1, GAMMA1]
                coeff = 0
                for k in range(3):
                    if j * 3 + k < len(stream):
                        coeff += stream[j * 3 + k] << (8 * k)
                
                coeff = coeff % (2 * cls.GAMMA1)
                coeff -= cls.GAMMA1
                poly.append(coeff)
            
            polys.append(poly)
        
        return polys
    
    @classmethod
    def _matrix_vector_mul(cls, A: List[List[List[int]]], v: List[List[int]]) -> List[List[int]]:
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
    def _vector_add(cls, a: List[List[int]], b: List[List[int]]) -> List[List[int]]:
        """Vector addition"""
        return [cls._poly_add(a[i], b[i]) for i in range(len(a))]
    
    @classmethod
    def _vector_sub(cls, a: List[List[int]], b: List[List[int]]) -> List[List[int]]:
        """Vector subtraction"""
        return [cls._poly_sub(a[i], b[i]) for i in range(len(a))]
    
    @classmethod
    def _scalar_vector_mul(cls, c: List[int], v: List[List[int]]) -> List[List[int]]:
        """Scalar-vector multiplication"""
        return [cls._poly_mul(c, v[i]) for i in range(len(v))]
    
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
        """Polynomial multiplication"""
        result = [0] * cls.N
        for i in range(cls.N):
            for j in range(cls.N):
                if i + j < cls.N:
                    result[i + j] = (result[i + j] + a[i] * b[j]) % cls.Q
                else:
                    result[i + j - cls.N] = (result[i + j - cls.N] - a[i] * b[j]) % cls.Q
        return result
    
    @classmethod
    def _infinity_norm(cls, v: List[List[int]]) -> int:
        """Compute infinity norm of vector"""
        max_norm = 0
        for poly in v:
            for coeff in poly:
                norm = abs(coeff)
                if norm > max_norm:
                    max_norm = norm
        return max_norm
    
    @classmethod
    def _high_bits(cls, v: List[List[int]]) -> List[List[int]]:
        """Extract high bits"""
        return [[coeff // (2 * cls.GAMMA2) for coeff in poly] for poly in v]
    
    @classmethod
    def _low_bits(cls, v: List[List[int]]) -> List[List[int]]:
        """Extract low bits"""
        return [[coeff % (2 * cls.GAMMA2) for coeff in poly] for poly in v]
    
    @classmethod
    def _make_hint(cls, c: List[int], w: List[List[int]], cs2: List[List[int]]) -> List[int]:
        """Make hint for signature"""
        # Simplified hint generation
        hint = []
        for i in range(len(w)):
            poly_hint = []
            for j in range(cls.N):
                # Check if high bits change
                w_high = w[i][j] // (2 * cls.GAMMA2)
                w_cs2_high = (w[i][j] - cs2[i][j]) // (2 * cls.GAMMA2)
                poly_hint.append(1 if w_high != w_cs2_high else 0)
            hint.extend(poly_hint)
        return hint
    
    @classmethod
    def _use_hint(cls, h: List[int], w: List[List[int]]) -> List[List[int]]:
        """Use hint to recover high bits"""
        result = []
        hint_idx = 0
        
        for i in range(len(w)):
            poly = []
            for j in range(cls.N):
                if hint_idx < len(h) and h[hint_idx]:
                    # Adjust high bits using hint
                    high = w[i][j] // (2 * cls.GAMMA2)
                    poly.append(high + 1)
                else:
                    poly.append(w[i][j] // (2 * cls.GAMMA2))
                hint_idx += 1
            result.append(poly)
        
        return result
    
    @classmethod
    def _pack_public_key(cls, rho: bytes, t: List[List[int]]) -> bytes:
        """Pack public key"""
        data = rho
        for poly in t:
            for coeff in poly:
                data += coeff.to_bytes(4, 'little')
        return data
    
    @classmethod
    def _unpack_public_key(cls, pk: bytes) -> Tuple[bytes, List[List[int]]]:
        """Unpack public key"""
        rho = pk[:32]
        t = []
        offset = 32
        
        for i in range(cls.K):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(pk[offset:offset+4], 'little')
                poly.append(coeff)
                offset += 4
            t.append(poly)
        
        return rho, t
    
    @classmethod
    def _pack_private_key(cls, rho: bytes, K_seed: bytes, s1: List[List[int]], 
                         s2: List[List[int]], t: List[List[int]]) -> bytes:
        """Pack private key"""
        data = rho + K_seed
        
        for poly in s1:
            for coeff in poly:
                data += coeff.to_bytes(4, 'little', signed=True)
        
        for poly in s2:
            for coeff in poly:
                data += coeff.to_bytes(4, 'little', signed=True)
        
        for poly in t:
            for coeff in poly:
                data += coeff.to_bytes(4, 'little')
        
        return data
    
    @classmethod
    def _unpack_private_key(cls, sk: bytes) -> Tuple[bytes, bytes, List[List[int]], List[List[int]], List[List[int]]]:
        """Unpack private key"""
        rho = sk[:32]
        K_seed = sk[32:64]
        offset = 64
        
        # Unpack s1
        s1 = []
        for i in range(cls.L):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(sk[offset:offset+4], 'little', signed=True)
                poly.append(coeff)
                offset += 4
            s1.append(poly)
        
        # Unpack s2
        s2 = []
        for i in range(cls.K):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(sk[offset:offset+4], 'little', signed=True)
                poly.append(coeff)
                offset += 4
            s2.append(poly)
        
        # Unpack t
        t = []
        for i in range(cls.K):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(sk[offset:offset+4], 'little')
                poly.append(coeff)
                offset += 4
            t.append(poly)
        
        return rho, K_seed, s1, s2, t
    
    @classmethod
    def _pack_signature(cls, c_tilde: bytes, z: List[List[int]], h: List[int]) -> bytes:
        """Pack signature"""
        data = c_tilde
        
        for poly in z:
            for coeff in poly:
                data += coeff.to_bytes(4, 'little', signed=True)
        
        # Pack hint as bits
        hint_bytes = bytearray((len(h) + 7) // 8)
        for i, bit in enumerate(h):
            if bit:
                hint_bytes[i // 8] |= 1 << (i % 8)
        
        data += bytes(hint_bytes)
        return data
    
    @classmethod
    def _unpack_signature(cls, sig: bytes) -> Tuple[bytes, List[List[int]], List[int]]:
        """Unpack signature"""
        c_tilde = sig[:32]
        offset = 32
        
        # Unpack z
        z = []
        for i in range(cls.L):
            poly = []
            for j in range(cls.N):
                coeff = int.from_bytes(sig[offset:offset+4], 'little', signed=True)
                poly.append(coeff)
                offset += 4
            z.append(poly)
        
        # Unpack hint
        hint_size = cls.K * cls.N
        hint_bytes = sig[offset:offset + (hint_size + 7) // 8]
        h = []
        
        for i in range(hint_size):
            byte_idx = i // 8
            bit_idx = i % 8
            if byte_idx < len(hint_bytes):
                bit = (hint_bytes[byte_idx] >> bit_idx) & 1
                h.append(bit)
            else:
                h.append(0)
        
        return c_tilde, z, h
    
    @classmethod
    def _pack_w1(cls, w1: List[List[int]]) -> bytes:
        """Pack w1 for hashing"""
        data = b''
        for poly in w1:
            for coeff in poly:
                data += coeff.to_bytes(2, 'little')
        return data


class QuantumWallet:
    """
    Quantum-resistant wallet implementation
    """
    
    def __init__(self):
        self.signature_keys = {}  # address -> (pk, sk)
        self.encryption_keys = {}  # address -> (pk, sk)
    
    def create_address(self) -> str:
        """Create a new quantum-resistant address"""
        # Generate signature keys
        sig_pk, sig_sk = QuantumSignature.keygen()
        
        # Generate encryption keys
        enc_pk, enc_sk = Kyber1024.keygen()
        
        # Create address from public keys
        combined_pk = sig_pk + enc_pk
        address_hash = hashlib.sha3_256(combined_pk).digest()
        address = self._encode_address(address_hash[:20])
        
        # Store keys
        self.signature_keys[address] = (sig_pk, sig_sk)
        self.encryption_keys[address] = (enc_pk, enc_sk)
        
        return address
    
    def sign_transaction(self, address: str, transaction_data: dict) -> bytes:
        """Sign a transaction with quantum-resistant signature"""
        if address not in self.signature_keys:
            raise ValueError("Address not found in wallet")
        
        _, sig_sk = self.signature_keys[address]
        message = json.dumps(transaction_data, sort_keys=True).encode()
        
        return QuantumSignature.sign(message, sig_sk)
    
    def get_public_key(self, address: str) -> bytes:
        """Get the signature public key for an address"""
        if address not in self.signature_keys:
            raise ValueError("Address not found in wallet")
        
        sig_pk, _ = self.signature_keys[address]
        return sig_pk
    
    def verify_signature(self, address: str, transaction_data: dict, signature: bytes) -> bool:
        """Verify a quantum-resistant signature"""
        if address not in self.signature_keys:
            return False
        
        sig_pk, _ = self.signature_keys[address]
        message = json.dumps(transaction_data, sort_keys=True).encode()
        
        return QuantumSignature.verify(message, signature, sig_pk)
    
    @staticmethod
    def _encode_address(address_bytes: bytes) -> str:
        """Encode address bytes to string"""
        import base58
        return base58.b58encode_check(address_bytes).decode()
    
    @staticmethod
    def _decode_address(address: str) -> bytes:
        """Decode address string to bytes"""
        import base58
        return base58.b58decode_check(address)