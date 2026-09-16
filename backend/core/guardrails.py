"""
AI Guardrails System (AI Planet Feature)
Robust safeguards against:
- Cyber threats
- Prompt injection attacks
- Data leaks (PII detection & redaction)
- Toxic/harmful content
- Jailbreak attempts
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class GuardrailViolation:
    """Detected guardrail violation"""
    type: str
    severity: str  # low, medium, high, critical
    description: str
    detected_content: Optional[str] = None
    remediation: Optional[str] = None


class Guardrails:
    """
    Comprehensive AI guardrails system
    AI Planet Feature: Enterprise-grade security for AI interactions
    """

    # PII patterns
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone_us": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        "url": r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+',
    }

    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore\s+previous\s+instructions",
        r"disregard\s+all\s+prior\s+commands",
        r"you\s+are\s+now\s+a",
        r"pretend\s+you\s+are",
        r"act\s+as\s+if",
        r"bypass\s+security",
        r"override\s+system",
        r"</system>",
        r"<\|im_start\|>",
    ]

    # Toxic content keywords
    TOXIC_KEYWORDS = [
        "harmful", "dangerous", "illegal", "weapon", "bomb",
        "hack", "exploit", "vulnerability", "malware"
    ]

    def __init__(self, llm_provider=None, enable_llm_checks: bool = True):
        self.llm_provider = llm_provider
        self.enable_llm_checks = enable_llm_checks

    async def check_input(self, text: str) -> Tuple[bool, List[GuardrailViolation]]:
        """
        Check user input for violations

        Returns:
            (is_safe, violations)
        """
        violations = []

        # 1. Check for prompt injection
        injection_violations = self._check_prompt_injection(text)
        violations.extend(injection_violations)

        # 2. Check for PII
        pii_violations = self._check_pii(text)
        violations.extend(pii_violations)

        # 3. Check for toxic content
        toxic_violations = await self._check_toxic_content(text)
        violations.extend(toxic_violations)

        # 4. Check for jailbreak attempts
        jailbreak_violations = self._check_jailbreak(text)
        violations.extend(jailbreak_violations)

        # Determine if safe
        is_safe = not any(v.severity in ['high', 'critical'] for v in violations)

        return is_safe, violations

    async def check_output(self, text: str) -> Tuple[bool, List[GuardrailViolation]]:
        """
        Check LLM output for violations

        Returns:
            (is_safe, violations)
        """
        violations = []

        # 1. Check for PII leakage
        pii_violations = self._check_pii(text)
        violations.extend(pii_violations)

        # 2. Check for sensitive information
        sensitive_violations = self._check_sensitive_info(text)
        violations.extend(sensitive_violations)

        # 3. Check for harmful outputs
        harmful_violations = await self._check_harmful_output(text)
        violations.extend(harmful_violations)

        is_safe = not any(v.severity in ['high', 'critical'] for v in violations)

        return is_safe, violations

    def _check_prompt_injection(self, text: str) -> List[GuardrailViolation]:
        """Detect prompt injection attempts"""
        violations = []

        text_lower = text.lower()

        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                violations.append(GuardrailViolation(
                    type="prompt_injection",
                    severity="critical",
                    description="Potential prompt injection detected",
                    detected_content=pattern,
                    remediation="Request blocked for security"
                ))

        return violations

    def _check_pii(self, text: str) -> List[GuardrailViolation]:
        """Detect personally identifiable information"""
        violations = []

        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text)

            if matches:
                violations.append(GuardrailViolation(
                    type=f"pii_{pii_type}",
                    severity="high",
                    description=f"PII detected: {pii_type}",
                    detected_content=f"Found {len(matches)} {pii_type}(s)",
                    remediation="Redact or mask PII"
                ))

        return violations

    async def _check_toxic_content(self, text: str) -> List[GuardrailViolation]:
        """Detect toxic or harmful content"""
        violations = []

        text_lower = text.lower()

        # Keyword-based check
        for keyword in self.TOXIC_KEYWORDS:
            if keyword in text_lower:
                violations.append(GuardrailViolation(
                    type="toxic_content",
                    severity="medium",
                    description=f"Potentially harmful keyword: {keyword}",
                    remediation="Review content"
                ))

        # LLM-based toxicity check (more accurate)
        if self.enable_llm_checks and self.llm_provider:
            try:
                prompt = f"""Analyze this text for toxic, harmful, or dangerous content.
Rate toxicity (0-1 scale) and explain.

Text: {text[:500]}

JSON: {{"toxic": false, "score": 0.0, "explanation": ""}}"""

                response = await self.llm_provider.query(
                    prompt=prompt,
                    temperature=0.1,
                    max_tokens=200
                )

                import json
                result = json.loads(re.search(r'\{.*\}', response, re.DOTALL).group())

                if result.get('toxic', False) or result.get('score', 0) > 0.6:
                    violations.append(GuardrailViolation(
                        type="toxic_content_llm",
                        severity="high",
                        description=result.get('explanation', 'Toxic content detected'),
                        remediation="Block or flag content"
                    ))

            except Exception as e:
                logger.warning(f"LLM toxicity check failed: {e}")

        return violations

    def _check_jailbreak(self, text: str) -> List[GuardrailViolation]:
        """Detect jailbreak attempts"""
        violations = []

        jailbreak_patterns = [
            r"dan\s+mode",
            r"developer\s+mode",
            r"you\s+have\s+no\s+restrictions",
            r"you\s+can\s+do\s+anything",
            r"evil\s+mode",
        ]

        text_lower = text.lower()

        for pattern in jailbreak_patterns:
            if re.search(pattern, text_lower):
                violations.append(GuardrailViolation(
                    type="jailbreak_attempt",
                    severity="critical",
                    description="Jailbreak attempt detected",
                    detected_content=pattern,
                    remediation="Block request immediately"
                ))

        return violations

    def _check_sensitive_info(self, text: str) -> List[GuardrailViolation]:
        """Check for sensitive information leakage"""
        violations = []

        sensitive_patterns = {
            "api_key": r'(api[_-]?key|apikey)\s*[=:]\s*["\']?[\w\-]{20,}',
            "password": r'(password|passwd|pwd)\s*[=:]\s*["\']?[\w\-]{8,}',
            "secret": r'(secret|token)\s*[=:]\s*["\']?[\w\-]{20,}',
        }

        for info_type, pattern in sensitive_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(GuardrailViolation(
                    type=f"sensitive_{info_type}",
                    severity="critical",
                    description=f"Potential {info_type} leakage",
                    remediation="Redact sensitive information"
                ))

        return violations

    async def _check_harmful_output(self, text: str) -> List[GuardrailViolation]:
        """Check if LLM output could be harmful"""
        violations = []

        # Check for instructions on illegal activities
        harmful_indicators = [
            "how to make a bomb",
            "how to hack",
            "illegal activities",
            "bypass security",
        ]

        text_lower = text.lower()

        for indicator in harmful_indicators:
            if indicator in text_lower:
                violations.append(GuardrailViolation(
                    type="harmful_output",
                    severity="critical",
                    description="Output contains potentially harmful instructions",
                    remediation="Block output, log incident"
                ))

        return violations

    def redact_pii(self, text: str) -> str:
        """Redact PII from text"""

        redacted = text

        for pii_type, pattern in self.PII_PATTERNS.items():
            if pii_type == "email":
                redacted = re.sub(pattern, "[EMAIL_REDACTED]", redacted)
            elif pii_type == "phone_us":
                redacted = re.sub(pattern, "[PHONE_REDACTED]", redacted)
            elif pii_type == "ssn":
                redacted = re.sub(pattern, "[SSN_REDACTED]", redacted)
            elif pii_type == "credit_card":
                redacted = re.sub(pattern, "[CARD_REDACTED]", redacted)
            elif pii_type == "ip_address":
                redacted = re.sub(pattern, "[IP_REDACTED]", redacted)

        return redacted

    def get_safety_report(self, violations: List[GuardrailViolation]) -> Dict[str, Any]:
        """Generate safety report from violations"""

        return {
            "total_violations": len(violations),
            "critical_violations": sum(1 for v in violations if v.severity == "critical"),
            "high_violations": sum(1 for v in violations if v.severity == "high"),
            "medium_violations": sum(1 for v in violations if v.severity == "medium"),
            "low_violations": sum(1 for v in violations if v.severity == "low"),
            "violation_types": list(set(v.type for v in violations)),
            "details": [
                {
                    "type": v.type,
                    "severity": v.severity,
                    "description": v.description,
                    "remediation": v.remediation
                }
                for v in violations
            ]
        }


# Global guardrails instance
guardrails = Guardrails()
