"""
AI Triage Engine - Error Analysis & Root Cause Detection

Core feature: Analyze error logs and determine if it's an application bug
or infrastructure issue. Shut down developer blame-shifting with technical authority.

Use Cases:
- Developer: "Is this my bug or DevOps' problem?"
- AI: "This is an application error. Stack trace shows NullPointerException..."
- Result: Instant triage, no more wasted DevOps time
"""

import re
from typing import Dict, List, Optional
from enum import Enum


class ErrorCategory(str, Enum):
    """Error classification categories"""
    APPLICATION_BUG = "application_bug"
    INFRASTRUCTURE = "infrastructure"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Error severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TriageResult:
    """Result of error triage analysis"""
    def __init__(
        self,
        category: ErrorCategory,
        severity: Severity,
        confidence: float,
        reasoning: str,
        evidence: List[str],
        responsible_team: str,
        suggested_actions: List[str]
    ):
        self.category = category
        self.severity = severity
        self.confidence = confidence
        self.reasoning = reasoning
        self.evidence = evidence
        self.responsible_team = responsible_team
        self.suggested_actions = suggested_actions

    def to_dict(self) -> Dict:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "responsible_team": self.responsible_team,
            "suggested_actions": self.suggested_actions
        }


class TriageEngine:
    """
    Error triage engine - analyzes logs and determines root cause
    
    Pattern recognition for:
    - Application errors (NPE, unhandled exceptions, logic bugs)
    - Infrastructure issues (OOM, network failures, disk full)
    - Configuration problems (missing env vars, wrong secrets)
    - Dependency failures (external API down, DB connection)
    """

    # Application error patterns
    APP_ERROR_PATTERNS = [
        (r"NullPointerException", "Null pointer dereference in application code"),
        (r"IndexOutOfBoundsException", "Array/list index error in application code"),
        (r"IllegalArgumentException", "Invalid argument passed in application code"),
        (r"ClassCastException", "Type casting error in application code"),
        (r"NumberFormatException", "Number parsing error in application code"),
        (r"UndefinedVariableError", "Undefined variable in application code"),
        (r"NameError:", "Name not defined in Python code"),
        (r"TypeError:", "Type error in application code"),
        (r"AttributeError:", "Attribute access error in application code"),
        (r"KeyError:", "Dictionary key error in application code"),
        (r"ValueError:", "Value error in application code"),
        (r"SyntaxError:", "Syntax error in application code"),
        (r"IndentationError:", "Indentation error in Python code"),
        (r"UnhandledPromiseRejection", "Unhandled promise in JavaScript code"),
        (r"ReferenceError:", "Reference error in JavaScript code"),
        (r"Cannot read property .* of undefined", "Undefined property access in JavaScript"),
        (r"Cannot read property .* of null", "Null property access in JavaScript"),
        (r"\[ERROR\].*test.*failed", "Unit test failure"),
        (r"AssertionError:", "Assertion failed in application code"),
        (r"panic: runtime error:", "Go runtime panic in application code"),
    ]

    # Infrastructure error patterns
    INFRA_ERROR_PATTERNS = [
        (r"OutOfMemoryError", "Container/pod out of memory"),
        (r"OOMKilled", "Kubernetes killed pod due to OOM"),
        (r"CrashLoopBackOff", "Pod repeatedly crashing - check resource limits"),
        (r"ImagePullBackOff", "Cannot pull Docker image - registry issue"),
        (r"ErrImagePull", "Docker image pull failed"),
        (r"Failed to pull image", "Container image pull failure"),
        (r"dial tcp.*connection refused", "Network connection refused - service down"),
        (r"dial tcp.*i/o timeout", "Network timeout - connectivity issue"),
        (r"no space left on device", "Disk space exhausted"),
        (r"too many open files", "File descriptor limit reached"),
        (r"Liveness probe failed", "Kubernetes liveness check failed"),
        (r"Readiness probe failed", "Kubernetes readiness check failed"),
        (r"Back-off restarting failed container", "Container restart limit reached"),
        (r"LoadBalancer.*not found", "Load balancer configuration issue"),
        (r"Ingress.*not found", "Ingress configuration missing"),
        (r"Service.*not found", "Kubernetes service not found"),
        (r"PersistentVolumeClaim.*not found", "Storage volume claim missing"),
        (r"Node.*NotReady", "Kubernetes node not ready"),
    ]

    # Configuration error patterns
    CONFIG_ERROR_PATTERNS = [
        (r"environment variable.*not set", "Missing environment variable"),
        (r"ENV.*undefined", "Environment variable not defined"),
        (r"secret.*not found", "Kubernetes secret missing"),
        (r"configmap.*not found", "Kubernetes ConfigMap missing"),
        (r"connection refused.*:5432", "PostgreSQL connection failed - check config"),
        (r"connection refused.*:3306", "MySQL connection failed - check config"),
        (r"connection refused.*:6379", "Redis connection failed - check config"),
        (r"connection refused.*:27017", "MongoDB connection failed - check config"),
        (r"authentication failed", "Authentication credentials incorrect"),
        (r"permission denied", "Permission/access control issue"),
        (r"Invalid API key", "API key configuration invalid"),
        (r"Invalid credentials", "Credentials configuration invalid"),
    ]

    # Dependency error patterns
    DEPENDENCY_ERROR_PATTERNS = [
        (r"(HTTP|HTTPError).*502", "Upstream service returned 502"),
        (r"(HTTP|HTTPError).*503", "Upstream service unavailable"),
        (r"(HTTP|HTTPError).*504", "Upstream service timeout"),
        (r"Service Unavailable", "External service unavailable"),
        (r"Gateway Timeout", "External service timeout"),
        (r"Bad Gateway", "Upstream gateway error"),
        (r"Connection reset by peer", "Network connection reset"),
        (r"Broken pipe", "Network connection broken"),
        (r"ECONNRESET", "Connection reset by remote host"),
        (r"ETIMEDOUT", "Connection timeout"),
        (r"ConnectTimeout", "Connection timeout to external service"),
        (r"Max retries exceeded", "External service unreachable after retries"),
        (r"External API.*failed", "External API call failed"),
        (r"external.*service.*failed", "External service call failed"),
        (r"Third-party service.*unavailable", "Third-party dependency down"),
    ]

    def analyze(self, error_log: str, context: Optional[Dict] = None) -> TriageResult:
        """
        Analyze error log and return triage result
        
        Args:
            error_log: Raw error log text
            context: Optional context (customer, environment, pod name, etc.)
            
        Returns:
            TriageResult with classification and recommendations
        """
        # Check each pattern category
        app_matches = self._check_patterns(error_log, self.APP_ERROR_PATTERNS)
        infra_matches = self._check_patterns(error_log, self.INFRA_ERROR_PATTERNS)
        config_matches = self._check_patterns(error_log, self.CONFIG_ERROR_PATTERNS)
        dep_matches = self._check_patterns(error_log, self.DEPENDENCY_ERROR_PATTERNS)

        # Determine category based on matches
        if app_matches:
            return self._create_result(
                category=ErrorCategory.APPLICATION_BUG,
                severity=self._determine_severity(error_log, app_matches),
                confidence=0.9,
                matches=app_matches,
                responsible_team="Development Team",
                context=context
            )
        elif config_matches:
            return self._create_result(
                category=ErrorCategory.CONFIGURATION,
                severity=self._determine_severity(error_log, config_matches),
                confidence=0.85,
                matches=config_matches,
                responsible_team="DevOps Team (Configuration)",
                context=context
            )
        elif dep_matches:
            return self._create_result(
                category=ErrorCategory.DEPENDENCY,
                severity=self._determine_severity(error_log, dep_matches),
                confidence=0.8,
                matches=dep_matches,
                responsible_team="Joint (Dev + DevOps)",
                context=context
            )
        elif infra_matches:
            return self._create_result(
                category=ErrorCategory.INFRASTRUCTURE,
                severity=self._determine_severity(error_log, infra_matches),
                confidence=0.9,
                matches=infra_matches,
                responsible_team="DevOps Team (Infrastructure)",
                context=context
            )
        else:
            # Unknown - need more investigation
            return self._create_result(
                category=ErrorCategory.UNKNOWN,
                severity=Severity.MEDIUM,
                confidence=0.3,
                matches=[("No known patterns matched", "Requires manual investigation")],
                responsible_team="Joint Investigation",
                context=context
            )

    def _check_patterns(self, log: str, patterns: List[tuple]) -> List[tuple]:
        """Check log against pattern list and return matches"""
        matches = []
        for pattern, description in patterns:
            if re.search(pattern, log, re.IGNORECASE):
                matches.append((pattern, description))
        return matches

    def _determine_severity(self, log: str, matches: List[tuple]) -> Severity:
        """Determine severity based on log content and matches"""
        log_lower = log.lower()
        
        # Critical indicators
        if any(word in log_lower for word in ['critical', 'fatal', 'oomkilled', 'crash']):
            return Severity.CRITICAL
        
        # High severity indicators
        if any(word in log_lower for word in ['error', 'exception', 'failed', 'panic']):
            return Severity.HIGH
        
        # Medium severity
        if any(word in log_lower for word in ['warning', 'warn', 'deprecated']):
            return Severity.MEDIUM
        
        # Default to high for error matches
        return Severity.HIGH if matches else Severity.LOW

    def _create_result(
        self,
        category: ErrorCategory,
        severity: Severity,
        confidence: float,
        matches: List[tuple],
        responsible_team: str,
        context: Optional[Dict]
    ) -> TriageResult:
        """Create detailed triage result"""
        
        # Extract evidence from matches
        evidence = [description for _, description in matches]
        
        # Build reasoning
        reasoning = self._build_reasoning(category, matches, context)
        
        # Generate suggested actions
        suggested_actions = self._generate_actions(category, matches, context)
        
        return TriageResult(
            category=category,
            severity=severity,
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence,
            responsible_team=responsible_team,
            suggested_actions=suggested_actions
        )

    def _build_reasoning(self, category: ErrorCategory, matches: List[tuple], context: Optional[Dict]) -> str:
        """Build human-readable reasoning for the classification"""
        
        if category == ErrorCategory.APPLICATION_BUG:
            return (
                "This is an APPLICATION ERROR. The stack trace shows runtime exceptions "
                "that are caused by bugs in the application code, not infrastructure issues. "
                f"Evidence: {', '.join([desc for _, desc in matches[:3]])}. "
                "This is the development team's responsibility to fix."
            )
        elif category == ErrorCategory.INFRASTRUCTURE:
            return (
                "This is an INFRASTRUCTURE ISSUE. The error indicates problems with "
                "the underlying platform (Kubernetes, networking, resources, etc.). "
                f"Evidence: {', '.join([desc for _, desc in matches[:3]])}. "
                "This is the DevOps team's responsibility to resolve."
            )
        elif category == ErrorCategory.CONFIGURATION:
            return (
                "This is a CONFIGURATION ISSUE. The error indicates missing or incorrect "
                "configuration (environment variables, secrets, connection strings). "
                f"Evidence: {', '.join([desc for _, desc in matches[:3]])}. "
                "This requires DevOps to update configuration."
            )
        elif category == ErrorCategory.DEPENDENCY:
            return (
                "This is a DEPENDENCY FAILURE. An external service or API is unavailable "
                "or not responding correctly. "
                f"Evidence: {', '.join([desc for _, desc in matches[:3]])}. "
                "This requires joint investigation (Dev + DevOps)."
            )
        else:
            return (
                "Unable to automatically classify this error. No known patterns matched. "
                "Requires manual investigation by both Dev and DevOps teams."
            )

    def _generate_actions(self, category: ErrorCategory, matches: List[tuple], context: Optional[Dict]) -> List[str]:
        """Generate specific recommended actions"""
        
        actions = []
        
        if category == ErrorCategory.APPLICATION_BUG:
            actions = [
                "Review application logs for full stack trace",
                "Check recent code changes that may have introduced the bug",
                "Add null checks / error handling in application code",
                "Write unit test to reproduce the issue",
                "Fix the bug and deploy patch"
            ]
        elif category == ErrorCategory.INFRASTRUCTURE:
            actions = [
                "Check pod resource limits (CPU/memory)",
                "Review Kubernetes events for the pod",
                "Check node health and available resources",
                "Verify network connectivity and DNS",
                "Check for infrastructure alerts in monitoring"
            ]
        elif category == ErrorCategory.CONFIGURATION:
            actions = [
                "Verify all environment variables are set correctly",
                "Check Kubernetes secrets and ConfigMaps exist",
                "Validate connection strings and credentials",
                "Review deployment manifests for missing config",
                "Test configuration in dev environment first"
            ]
        elif category == ErrorCategory.DEPENDENCY:
            actions = [
                "Check status of external services/APIs",
                "Review upstream service logs",
                "Test connectivity to dependent services",
                "Check for known outages or maintenance",
                "Implement retry logic or circuit breaker"
            ]
        else:
            actions = [
                "Collect full error logs and context",
                "Review recent changes (code + infrastructure)",
                "Check monitoring and metrics for anomalies",
                "Reproduce the issue in dev environment",
                "Escalate to senior engineer if needed"
            ]
        
        return actions


# Global instance
triage_engine = TriageEngine()
