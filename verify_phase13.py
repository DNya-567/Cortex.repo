#!/usr/bin/env python3
"""
Phase 13 Verification Script
Tests agent comparison, recommendation, and side-by-side UI
"""

import sys
import os

# Add project root to path
sys.path.insert(0, ".")
os.environ["PYTHONPATH"] = "."

def test_1_comparator_import():
    """Test: comparator module imports"""
    try:
        from src.orchestrator.comparator import compare_agents, score_answer
        print("✅ Test 1 PASS: Comparator imported OK")
        return True
    except Exception as e:
        print(f"❌ Test 1 FAIL: {e}")
        return False


def test_2_score_answer():
    """Test: score_answer function"""
    try:
        from src.orchestrator.comparator import score_answer

        # Test empty answer
        score1 = score_answer("")
        assert 0.0 <= score1 <= 0.2, f"Empty answer score {score1} too high"

        # Test medium answer
        medium = "The login function " * 50
        score2 = score_answer(medium)
        assert score2 > score1, f"Medium score {score2} not > empty {score1}"

        # Test high-quality answer
        quality = """
        The login function handles authentication:
```javascript
function login(user, pass) {
  return authenticate(user, pass);
}
```
        - Validates credentials
        - Returns JWT token
        - Uses loginController.js
        """
        score3 = score_answer(quality)
        assert score3 > score2, f"Quality score {score3} not > medium {score2}"
        assert score3 > 0.5, f"Quality score {score3} should be > 0.5"

        print(f"✅ Test 2 PASS: Scores {score1} < {score2} < {score3}")
        return True
    except AssertionError as e:
        print(f"❌ Test 2 FAIL: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 2 FAIL: {e}")
        return False


def test_3_compare_agents_single():
    """Test: compare_agents with single agent"""
    try:
        from src.orchestrator.comparator import compare_agents

        result = compare_agents("what does login do", ["ollama"])

        assert "results" in result, "Missing 'results' key"
        assert len(result["results"]) == 1, f"Expected 1 result, got {len(result['results'])}"
        assert result["results"][0]["agent"] == "ollama", "Agent mismatch"
        assert "best_agent" in result, "Missing 'best_agent'"
        assert result["best_agent"] == "ollama", "Best agent should be ollama"
        assert "comparison_summary" in result, "Missing 'comparison_summary'"
        assert 0.0 <= result["results"][0]["score"] <= 1.0, "Invalid score"

        print(f"✅ Test 3 PASS: Single agent compare OK (score: {result['results'][0]['score']})")
        return True
    except AssertionError as e:
        print(f"❌ Test 3 FAIL: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 3 FAIL: {e}")
        return False


def test_4_selector_import():
    """Test: selector module imports"""
    try:
        from src.orchestrator.selector import recommend_agent
        print("✅ Test 4 PASS: Selector imported OK")
        return True
    except Exception as e:
        print(f"❌ Test 4 FAIL: {e}")
        return False


def test_5_recommend_agent():
    """Test: recommend_agent function"""
    try:
        from src.orchestrator.selector import recommend_agent

        # Test "explain" task type
        r1 = recommend_agent("how does login work", ["ollama", "claude"])
        assert r1["task_type"] in ["explain", "search"], f"Unexpected task type: {r1['task_type']}"
        assert r1["recommended"] in ["ollama", "claude"], f"Unexpected recommendation: {r1['recommended']}"
        assert "reason" in r1, "Missing reason"
        assert 0.0 < r1["confidence"] <= 1.0, f"Invalid confidence: {r1['confidence']}"

        # Test "search" task type
        r2 = recommend_agent("find all routes", ["ollama", "claude"])
        assert r2["task_type"] == "search", f"Should detect search, got {r2['task_type']}"
        assert r2["recommended"] in ["ollama", "claude"], f"Unexpected recommendation: {r2['recommended']}"

        print(f"✅ Test 5 PASS: Recommendations OK")
        print(f"   - '{r1['task_type']}' -> {r1['recommended']} (confidence: {r1['confidence']})")
        print(f"   - '{r2['task_type']}' -> {r2['recommended']} (confidence: {r2['confidence']})")
        return True
    except AssertionError as e:
        print(f"❌ Test 5 FAIL: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 5 FAIL: {e}")
        return False


def test_6_api_recommend_endpoint():
    """Test: API /recommend endpoint"""
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/recommend?task=how+does+login+work")

        assert response.status_code == 200, f"Status {response.status_code}"
        data = response.json()
        assert "recommended" in data, "Missing 'recommended'"
        assert "task_type" in data, "Missing 'task_type'"
        assert "confidence" in data, "Missing 'confidence'"

        print(f"✅ Test 6 PASS: /recommend endpoint OK")
        print(f"   Recommendation: {data['recommended']} ({data['task_type']})")
        return True
    except AssertionError as e:
        print(f"❌ Test 6 FAIL: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 6 FAIL: {e}")
        return False


def test_7_api_compare_single_agent():
    """Test: API /compare endpoint with single agent"""
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/compare?task=what+does+login+do&agents=ollama")

        assert response.status_code == 200, f"Status {response.status_code}"
        data = response.json()
        assert "results" in data, "Missing 'results'"
        assert "best_agent" in data, "Missing 'best_agent'"
        assert len(data["results"]) == 1, f"Expected 1 result, got {len(data['results'])}"

        print(f"✅ Test 7 PASS: /compare single agent OK")
        return True
    except AssertionError as e:
        print(f"❌ Test 7 FAIL: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 7 FAIL: {e}")
        return False


def test_8_api_compare_no_agents():
    """Test: API /compare endpoint without agents param"""
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/compare?task=what+does+login+do")

        assert response.status_code == 200, f"Status {response.status_code}"
        data = response.json()
        assert "results" in data, "Missing 'results'"
        assert len(data["results"]) >= 1, "Should have at least 1 result"

        print(f"✅ Test 8 PASS: /compare default agents OK ({len(data['results'])} agents)")
        return True
    except AssertionError as e:
        print(f"❌ Test 8 FAIL: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 8 FAIL: {e}")
        return False


def test_9_dashboard_comparison_ui():
    """Test: dashboard.html has comparison UI"""
    try:
        # Check if new dashboard exists
        from pathlib import Path
        dashboard = Path("dashboard_phase13.html")

        if not dashboard.exists():
            print("❌ Test 9 FAIL: dashboard_phase13.html not found")
            return False

        content = dashboard.read_text()

        assert "Compare" in content, "Missing 'Compare' tab"
        assert "/compare" in content or "compare" in content.lower(), "Missing compare API calls"
        assert "/recommend" in content or "recommend" in content.lower(), "Missing recommend API calls"

        print("✅ Test 9 PASS: Dashboard comparison UI found")
        return True
    except Exception as e:
        print(f"❌ Test 9 FAIL: {e}")
        return False


def test_10_dashboard_agent_status():
    """Test: dashboard.html has agent status bar"""
    try:
        from pathlib import Path
        dashboard = Path("dashboard_phase13.html")
        content = dashboard.read_text()

        assert "orchestrate/agents" in content, "Missing agent status fetch"
        assert "agent-status" in content or "agentStatus" in content, "Missing agent status bar"
        assert "Available" in content or "available" in content.lower(), "Missing availability indicator"

        print("✅ Test 10 PASS: Agent status bar found")
        return True
    except Exception as e:
        print(f"❌ Test 10 FAIL: {e}")
        return False


def test_11_dashboard_sub_tabs():
    """Test: dashboard.html has sub-tabs"""
    try:
        from pathlib import Path
        dashboard = Path("dashboard_phase13.html")
        content = dashboard.read_text()

        # Check for Compare tab
        assert "Compare" in content or "compare" in content, "Missing Compare tab"

        # Check for sub-tabs
        assert "Single Agent" in content or "single" in content.lower(), "Missing single agent tab"
        assert "compareAll" in content or "compare_all" in content.lower(), "Missing compare all functionality"

        print("✅ Test 11 PASS: Sub-tabs found")
        return True
    except Exception as e:
        print(f"❌ Test 11 FAIL: {e}")
        return False


def test_12_full_comparison_pipeline():
    """Test: full comparison pipeline"""
    try:
        from src.orchestrator.comparator import compare_agents

        result = compare_agents("explain the login function", ["ollama"])

        assert result["best_agent"] == "ollama", "Best agent should be ollama"
        assert result["results"][0]["score"] > 0, "Score should be > 0"
        assert len(result["comparison_summary"]) > 20, "Summary too short"

        print(f"✅ Test 12 PASS: Full pipeline OK")
        print(f"   Summary: {result['comparison_summary'][:80]}...")
        return True
    except Exception as e:
        print(f"❌ Test 12 FAIL: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("PHASE 13 VERIFICATION - AGENT COMPARISON & RECOMMENDATION")
    print("=" * 70 + "\n")

    tests = [
        test_1_comparator_import,
        test_2_score_answer,
        test_3_compare_agents_single,
        test_4_selector_import,
        test_5_recommend_agent,
        test_6_api_recommend_endpoint,
        test_7_api_compare_single_agent,
        test_8_api_compare_no_agents,
        test_9_dashboard_comparison_ui,
        test_10_dashboard_agent_status,
        test_11_dashboard_sub_tabs,
        test_12_full_comparison_pipeline,
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(tests, 1):
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {i} ERROR: {e}")
            failed += 1
        print()

    print("=" * 70)
    print(f"RESULTS: {passed}/{len(tests)} passed")
    print("=" * 70)

    if passed == len(tests):
        print("\n🎉 Phase 13 complete. Agent comparison system fully operational.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. See above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

