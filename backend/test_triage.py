#!/usr/bin/env python3
"""
Test AI Triage Engine - Verify error classification accuracy
"""

from triage import triage_engine, ErrorCategory

# Test cases with expected results
test_cases = [
    {
        "name": "Application Bug - NPE",
        "log": """
        Exception in thread "main" java.lang.NullPointerException
            at com.example.UserService.getUser(UserService.java:42)
            at com.example.Main.main(Main.java:15)
        """,
        "expected_category": ErrorCategory.APPLICATION_BUG,
        "expected_team": "Development Team"
    },
    {
        "name": "Application Bug - Python TypeError",
        "log": """
        Traceback (most recent call last):
          File "app.py", line 123, in process_data
            result = data['items'][0]['value']
        TypeError: 'NoneType' object is not subscriptable
        """,
        "expected_category": ErrorCategory.APPLICATION_BUG,
        "expected_team": "Development Team"
    },
    {
        "name": "Application Bug - JavaScript Undefined",
        "log": """
        UnhandledPromiseRejectionWarning: TypeError: Cannot read property 'id' of undefined
            at UserController.getUser (/app/controllers/user.js:56:23)
            at Layer.handle [as handle_request] (/app/node_modules/express/lib/router/layer.js:95:5)
        """,
        "expected_category": ErrorCategory.APPLICATION_BUG,
        "expected_team": "Development Team"
    },
    {
        "name": "Infrastructure - OOM Killed",
        "log": """
        Error from server: error dialing backend: dial tcp 10.0.0.5:10250: connect: connection refused
        Status:     Failed
        Reason:     OOMKilled
        Exit Code:  137
        """,
        "expected_category": ErrorCategory.INFRASTRUCTURE,
        "expected_team": "DevOps Team (Infrastructure)"
    },
    {
        "name": "Infrastructure - CrashLoopBackOff",
        "log": """
        Pod acme-corp-api-7d4b8c9f7-xk2j5 is in CrashLoopBackOff
        Back-off restarting failed container
        """,
        "expected_category": ErrorCategory.INFRASTRUCTURE,
        "expected_team": "DevOps Team (Infrastructure)"
    },
    {
        "name": "Configuration - Missing Env Var",
        "log": """
        Error: Environment variable DATABASE_URL is not set
        Application failed to start
        """,
        "expected_category": ErrorCategory.CONFIGURATION,
        "expected_team": "DevOps Team (Configuration)"
    },
    {
        "name": "Configuration - Auth Failure",
        "log": """
        psycopg2.OperationalError: FATAL:  password authentication failed for user "postgres"
        connection to server at "postgres.default.svc.cluster.local" (10.0.0.10), port 5432 failed
        """,
        "expected_category": ErrorCategory.CONFIGURATION,
        "expected_team": "DevOps Team (Configuration)"
    },
    {
        "name": "Dependency - Upstream 503",
        "log": """
        HTTPError: 503 Server Error: Service Unavailable for url: https://api.external.com/data
        Failed to fetch data from external API
        """,
        "expected_category": ErrorCategory.DEPENDENCY,
        "expected_team": "Joint (Dev + DevOps)"
    },
    {
        "name": "Dependency - Connection Timeout",
        "log": """
        requests.exceptions.ConnectTimeout: HTTPConnectionPool(host='external-service.com', port=443): 
        Max retries exceeded with url: /api/v1/data (Caused by ConnectTimeoutError)
        """,
        "expected_category": ErrorCategory.DEPENDENCY,
        "expected_team": "Joint (Dev + DevOps)"
    }
]


def run_tests():
    """Run all triage test cases and report results"""
    print("=" * 80)
    print("AI TRIAGE ENGINE - TEST SUITE")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test['name']}")
        print("-" * 80)
        
        result = triage_engine.analyze(test['log'])
        
        # Check if classification is correct
        category_match = result.category == test['expected_category']
        team_match = result.responsible_team == test['expected_team']
        
        if category_match and team_match:
            print(f"✅ PASS")
            passed += 1
        else:
            print(f"❌ FAIL")
            failed += 1
            if not category_match:
                print(f"   Expected category: {test['expected_category'].value}")
                print(f"   Got category: {result.category.value}")
            if not team_match:
                print(f"   Expected team: {test['expected_team']}")
                print(f"   Got team: {result.responsible_team}")
        
        print(f"\nCategory: {result.category.value}")
        print(f"Severity: {result.severity.value}")
        print(f"Confidence: {result.confidence:.0%}")
        print(f"Responsible: {result.responsible_team}")
        print(f"\nReasoning:")
        print(f"  {result.reasoning}")
        print(f"\nEvidence:")
        for evidence in result.evidence[:3]:
            print(f"  • {evidence}")
        print(f"\nSuggested Actions:")
        for action in result.suggested_actions[:3]:
            print(f"  1. {action}")
        print()
        print()
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    
    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    exit(0 if failed == 0 else 1)
