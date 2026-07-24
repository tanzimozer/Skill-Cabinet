# Cryptographic System Audit — Diagnostic Test Template

This template outlines the Python structure for a reusable diagnostic test suite for cryptographic systems. Adapt the tests, measurement strategy, and output format to your specific vault/crypto implementation.

## Import Structure

```python
import json
import time
import hashlib
import secrets
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
```

## Core Test Classes

### 1. EncryptionPerformanceTest

```python
class EncryptionPerformanceTest:
    """Measure encryption/decryption latency across payload sizes."""
    
    def __init__(self, vault_engine, iterations=10):
        self.vault = vault_engine
        self.iterations = iterations
        self.results = {}
    
    def test_latency(self, payload_sizes: Dict[str, bytes]):
        """
        Args:
            payload_sizes: {'small': b'...', 'medium': b'...', 'large': b'...'}
        
        Returns:
            {
                'small': {'encrypt_times': [...], 'decrypt_times': [...], ...},
                'medium': {...},
                'large': {...}
            }
        """
        for size_name, payload in payload_sizes.items():
            encrypt_times = []
            decrypt_times = []
            
            for _ in range(self.iterations):
                # Encryption latency
                start = time.perf_counter()
                ciphertext = self.vault.encrypt(payload)
                encrypt_times.append((time.perf_counter() - start) * 1000)  # ms
                
                # Decryption latency
                start = time.perf_counter()
                plaintext = self.vault.decrypt(ciphertext)
                decrypt_times.append((time.perf_counter() - start) * 1000)  # ms
                
                assert plaintext == payload, f"Roundtrip failed for {size_name}"
            
            self.results[size_name] = {
                'payload_size': len(payload),
                'encrypt': {
                    'times': encrypt_times,
                    'mean': statistics.mean(encrypt_times),
                    'median': statistics.median(encrypt_times),
                    'stdev': statistics.stdev(encrypt_times) if len(encrypt_times) > 1 else 0,
                    'min': min(encrypt_times),
                    'max': max(encrypt_times),
                },
                'decrypt': {
                    'times': decrypt_times,
                    'mean': statistics.mean(decrypt_times),
                    'median': statistics.median(decrypt_times),
                    'stdev': statistics.stdev(decrypt_times) if len(decrypt_times) > 1 else 0,
                    'min': min(decrypt_times),
                    'max': max(decrypt_times),
                }
            }
        
        return self.results
    
    def verify_performance(self, max_acceptable_latency_ms=100.0):
        """Check if all operations are within acceptable latency."""
        violations = []
        for size, data in self.results.items():
            if data['encrypt']['mean'] > max_acceptable_latency_ms:
                violations.append(f"{size} encrypt mean {data['encrypt']['mean']:.3f}ms exceeds {max_acceptable_latency_ms}ms")
            if data['decrypt']['mean'] > max_acceptable_latency_ms:
                violations.append(f"{size} decrypt mean {data['decrypt']['mean']:.3f}ms exceeds {max_acceptable_latency_ms}ms")
        return len(violations) == 0, violations
```

### 2. VerificationProtocolTest

```python
class VerificationProtocolTest:
    """Validate verification logic (MFA, Q&A, challenge-response)."""
    
    def test_answer_verification(self, question: str, correct_answer: str, vault_engine):
        """Test case-insensitive answer matching."""
        test_cases = [
            (correct_answer, True, "Exact match"),
            (correct_answer.lower(), True, "Lowercase"),
            (correct_answer.upper(), True, "Uppercase"),
            (f"  {correct_answer}  ", True, "Whitespace"),
            ("wrong", False, "Incorrect"),
        ]
        
        results = []
        for user_answer, expected, description in test_cases:
            verified = vault_engine.verify_answer(question, user_answer)
            passed = verified == expected
            results.append({
                'test': description,
                'passed': passed,
                'user_answer': user_answer,
                'expected': expected,
                'got': verified
            })
        
        return results
    
    def test_answer_uniqueness(self, questions: List[Dict]):
        """Ensure all answers are unique."""
        answers = [q['answer'] for q in questions]
        unique_count = len(set(answers))
        total_count = len(answers)
        return unique_count == total_count, unique_count, total_count
    
    def test_encryption_roundtrip(self, vault_engine):
        """Test answer encryption/decryption correctness."""
        test_answer = "TestAnswer123"
        encrypted = vault_engine.encrypt_answer(test_answer)
        decrypted = vault_engine.decrypt_answer(encrypted)
        return decrypted == test_answer, encrypted, decrypted
    
    def test_3_of_3_enforcement(self, vault_engine, questions: List[Dict]):
        """Verify that exactly 3/3 correct answers are required."""
        # Test with 2/3 correct (should fail)
        answers_2of3 = [q['answer'] for q in questions[:2]] + ['wrong']
        passed_2of3 = vault_engine.verify_challenge(answers_2of3)
        
        # Test with 3/3 correct (should pass)
        answers_3of3 = [q['answer'] for q in questions]
        passed_3of3 = vault_engine.verify_challenge(answers_3of3)
        
        return {
            '2_of_3_rejected': not passed_2of3,
            '3_of_3_accepted': passed_3of3,
            'enforcement_correct': (not passed_2of3) and passed_3of3
        }
```

### 3. ObfuscationCollisionTest

```python
class ObfuscationCollisionTest:
    """Test obfuscation uniqueness and collision resistance."""
    
    def test_collision_resistance(self, vault_engine, service_names: List[str], uuid_str: str):
        """
        Generate obfuscated keys and check for collisions.
        
        Returns:
            {
                'keys': {service: obfuscated_key},
                'collisions': count,
                'unique_count': count,
                'theoretical_space': 2^n,
                'collision_probability': float
            }
        """
        keys = {}
        for service in service_names:
            keys[service] = vault_engine.obfuscate_service_name(service, uuid_str)
        
        unique_keys = set(keys.values())
        collision_count = len(service_names) - len(unique_keys)
        
        # Estimate theoretical space (e.g., 12 hex chars = 48 bits = 2^48)
        key_length = len(list(keys.values())[0])
        theoretical_bits = key_length * 4  # 4 bits per hex char
        theoretical_space = 2 ** theoretical_bits
        
        # Birthday paradox: P(collision) ≈ N²/2^(k+1)
        collision_prob = (len(service_names) ** 2) / (2 ** (theoretical_bits + 1))
        
        return {
            'keys': keys,
            'collisions_observed': collision_count,
            'unique_count': len(unique_keys),
            'total_keys': len(service_names),
            'key_length': key_length,
            'theoretical_bits': theoretical_bits,
            'theoretical_space': theoretical_space,
            'collision_probability': collision_prob,
            'passed': collision_count == 0
        }
    
    def test_hardware_binding(self, vault_engine, service: str, uuid1: str, uuid2: str):
        """Verify that different UUIDs produce different obfuscation keys."""
        key1 = vault_engine.obfuscate_service_name(service, uuid1)
        key2 = vault_engine.obfuscate_service_name(service, uuid2)
        return key1 != key2, key1, key2
    
    def test_determinism(self, vault_engine, service: str, uuid_str: str, iterations=5):
        """Verify that same input always produces same obfuscation key."""
        keys = [vault_engine.obfuscate_service_name(service, uuid_str) for _ in range(iterations)]
        all_same = len(set(keys)) == 1
        return all_same, keys
```

### 4. AccessLoggingTest

```python
class AccessLoggingTest:
    """Validate audit trail functionality."""
    
    def test_log_file_permissions(self, log_path: Path, expected_mode: int = 0o600):
        """Check log file exists and has correct permissions."""
        exists = log_path.exists()
        if exists:
            mode = log_path.stat().st_mode & 0o777
            correct = mode == expected_mode
            return exists, correct, oct(mode)
        return False, False, None
    
    def test_access_logging(self, vault_engine, service: str):
        """Verify access is logged."""
        log_before = vault_engine.get_access_log()
        vault_engine.get_credential(service)
        log_after = vault_engine.get_access_log()
        
        logged = log_after.get('access_count', 0) > log_before.get('access_count', 0)
        return logged, log_before, log_after
    
    def test_failure_logging(self, vault_engine):
        """Verify failed auth attempts are logged."""
        log_before = vault_engine.get_access_log()
        try:
            vault_engine.verify_challenge(['wrong', 'wrong', 'wrong'])
        except:
            pass
        log_after = vault_engine.get_access_log()
        
        logged = log_after.get('failed_attempts', 0) > log_before.get('failed_attempts', 0)
        return logged, log_before, log_after
    
    def assess_granularity(self, log_structure: Dict) -> str:
        """
        Assess log granularity.
        
        Returns: 'detailed' | 'aggregated' | 'missing'
        """
        if not log_structure:
            return 'missing'
        if 'operations' in log_structure:
            return 'detailed'
        if 'access_count' in log_structure:
            return 'aggregated'
        return 'unknown'
```

### 5. SecurityGapAnalysis

```python
class SecurityGapAnalysis:
    """Systematically check for security vulnerabilities."""
    
    def check_key_management(self, vault_engine, config: Dict) -> Dict[str, bool]:
        """Check key management best practices."""
        return {
            'hardware_uuid_binding': 'uuid.getnode()' in str(vault_engine.__class__.__code__),
            'fixed_salt': config.get('kdf_salt') is not None,
            'key_derivation_overhead': config.get('kdf_iterations', 0) > 10000,
            'no_key_rotation': 'rotate_key' not in dir(vault_engine),
        }
    
    def check_data_exposure(self, vault_engine, config: Dict) -> Dict[str, bool]:
        """Check for plaintext data exposure risks."""
        return {
            'credentials_in_ram': hasattr(vault_engine, 'vault_data'),
            'no_lazy_decryption': 'vault_data' in str(vault_engine.get_credential.__code__),
            'services_map_plaintext': Path(config.get('services_map_path', '')).exists(),
            'no_secure_erasure': 'overwrite' not in dir(vault_engine),
        }
    
    def check_authentication(self, vault_engine, config: Dict) -> Dict[str, str]:
        """Assess authentication mechanism strength."""
        auth_type = config.get('mfa_type', 'unknown')
        return {
            'mfa_type': auth_type,
            'strength': {
                'q&a': 'weak',
                'totp': 'medium',
                'webauthn': 'strong'
            }.get(auth_type, 'unknown'),
            'rate_limiting': 'rate_limit' in dir(vault_engine),
            'exponential_backoff': config.get('exponential_backoff', False),
        }
    
    def check_compliance(self, vault_engine, config: Dict) -> Dict[str, str]:
        """Assess compliance readiness."""
        log_granularity = self.assess_log_granularity(vault_engine)
        return {
            'soc2_type_ii': 'partial' if log_granularity == 'aggregated' else 'ready' if log_granularity == 'detailed' else 'fail',
            'hipaa': 'fail' if log_granularity != 'detailed' else 'ready',
            'pci_dss': 'fail' if config.get('mfa_type') == 'q&a' else 'ready',
            'gdpr': 'partial' if log_granularity == 'aggregated' else 'ready' if log_granularity == 'detailed' else 'fail',
        }
```

## Report Generation

```python
def generate_json_report(test_results: Dict[str, Any], issues: List[Dict], recommendations: List[Dict]) -> str:
    """Generate machine-readable JSON report."""
    report = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'tests': [
            {
                'name': test_name,
                'passed': result.get('passed', True),
                'details': str(result)
            }
            for test_name, result in test_results.items()
        ],
        'metrics': {
            'encryption': [
                {'name': 'encrypt_small_mean', 'value': str(test_results.get('latency_small', {}).get('encrypt', {}).get('mean', 0)), 'unit': 'ms'},
                # ... more metrics
            ],
            'compliance': test_results.get('compliance', {})
        },
        'issues': issues,
        'recommendations': recommendations,
        'summary': {
            'tests_passed': len([t for t in test_results.values() if t.get('passed', True)]),
            'tests_total': len(test_results),
            'status': 'PASS' if len([t for t in test_results.values() if not t.get('passed', True)]) == 0 else 'FAIL'
        }
    }
    return json.dumps(report, indent=2)

def generate_markdown_report(test_results: Dict[str, Any], issues: List[Dict]) -> str:
    """Generate human-readable markdown report."""
    report = "# Cryptographic System Audit Report\n\n"
    report += f"**Date:** {datetime.utcnow().isoformat()}Z\n\n"
    
    report += "## Test Results\n\n"
    for test_name, result in test_results.items():
        status = "✅ PASS" if result.get('passed', True) else "❌ FAIL"
        report += f"- {test_name}: {status}\n"
    
    report += "\n## Issues Found\n\n"
    for issue in issues:
        severity = issue.get('severity', 'unknown').upper()
        report += f"- **{severity}:** {issue.get('title', 'Unknown')}\n"
        report += f"  - {issue.get('description', '')}\n\n"
    
    return report
```

## Usage Example

```python
# Initialize vault engine (adapt to your system)
vault = EDITHVault(config_path='/home/hermes/.hermes/.edith/')

# Run all tests
perf_test = EncryptionPerformanceTest(vault)
latency = perf_test.test_latency({
    'small': b'test credential (19 bytes here)',
    'medium': b'x' * 552,
    'large': b'x' * 6164,
})

verification_test = VerificationProtocolTest()
questions = vault.get_verification_questions()
answer_results = verification_test.test_answer_verification(
    questions[0]['q'],
    questions[0]['a'],
    vault
)

obfuscation_test = ObfuscationCollisionTest()
collision_results = obfuscation_test.test_collision_resistance(
    vault,
    ['google', 'github', 'slack', 'aws', 'azure'],
    vault.get_hardware_uuid()
)

# Generate report
all_results = {
    'latency': latency,
    'answers': answer_results,
    'collisions': collision_results,
}

report_json = generate_json_report(all_results, issues, recommendations)
print(report_json)
```

---

**Notes:**
- Adapt class names, methods, and test cases to match your specific cryptographic implementation
- Add more payload sizes/test cases as needed
- Extend SecurityGapAnalysis with domain-specific checks
- Hook into CI/CD by using JSON report output
