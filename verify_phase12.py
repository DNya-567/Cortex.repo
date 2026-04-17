#!/usr/bin/env python3
import sys, os
from pathlib import Path
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)
os.environ["PYTHONPATH"] = "."
def test_1():
    try:
        from src.orchestrator.agents import get_available_agents, run_agent
        print("? TEST 1: Agent module imported")
        return True
    except Exception as e:
        print(f"? TEST 1: {e}")
        return False
def test_2():
    try:
        from src.orchestrator.agents import get_available_agents
        agents = get_available_agents()
        assert isinstance(agents, list)
        print(f"? TEST 2: Available: {agents}")
        return True
    except Exception as e:
        print(f"? TEST 2: {e}")
        return False
def test_3():
    try:
        from src.orchestrator.agents import run_agent
        result = run_agent("ollama", "hello", max_tokens=20)
        assert len(result["answer"]) > 0
        print(f"? TEST 3: run_agent works")
        return True
    except Exception as e:
        print(f"? TEST 3: {e}")
        return False
def test_4():
    try:
        from src.orchestrator.agents import run_agent
        result = run_agent("invalid", "test")
        assert result["error"] is not None
        print(f"? TEST 4: Invalid agent rejected")
        return True
    except Exception as e:
        print(f"? TEST 4: {e}")
        return False
def test_5():
    try:
        from src.orchestrator.planner import plan_task
        plan = plan_task("how does login work", ["ollama"], mode="auto")
        assert len(plan) >= 1
        print(f"? TEST 5: plan_task works ({len(plan)} subtasks)")
        return True
    except Exception as e:
        print(f"? TEST 5: {e}")
        return False
def test_6():
    try:
        from src.orchestrator.planner import plan_task
        plan = plan_task("explain auth", ["ollama"], mode="ollama")
        assert all(st["agent"] == "ollama" for st in plan)
        print(f"? TEST 6: Forced mode works")
        return True
    except Exception as e:
        print(f"? TEST 6: {e}")
        return False
def test_7():
    try:
        from src.orchestrator.planner import plan_task
        from src.orchestrator.runner import run_plan
        plan = plan_task("test", ["ollama"], mode="ollama")
        result = run_plan("test", plan)
        assert len(result["final_answer"]) > 0
        print(f"? TEST 7: run_plan works")
        return True
    except Exception as e:
        print(f"? TEST 7: {e}")
        return False
def test_8():
    try:
        from src.orchestrator.orchestrator import orchestrate
        result = orchestrate("test", mode="ollama")
        assert "run_id" in result
        print(f"? TEST 8: orchestrate works")
        return True
    except Exception as e:
        print(f"? TEST 8: {e}")
        return False
def test_9():
    try:
        from src.orchestrator.orchestrator import orchestrate
        from src.orchestrator.history import get_run, list_runs
        result = orchestrate("history test", mode="ollama")
        run_id = result["run_id"]
        retrieved = get_run(run_id)
        assert retrieved is not None
        print(f"? TEST 9: History works")
        return True
    except Exception as e:
        print(f"? TEST 9: {e}")
        return False
def test_10():
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app
        client = TestClient(app)
        response = client.get("/orchestrate/agents")
        assert response.status_code == 200
        print(f"? TEST 10: API agents endpoint works")
        return True
    except Exception as e:
        print(f"? TEST 10: {e}")
        return False
def test_11():
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app
        client = TestClient(app)
        response = client.get("/orchestrate?task=test&mode=ollama")
        assert response.status_code == 200
        print(f"? TEST 11: API orchestrate endpoint works")
        return True
    except Exception as e:
        print(f"? TEST 11: {e}")
        return False
def test_12():
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app
        client = TestClient(app)
        response = client.get("/orchestrate/history")
        assert response.status_code == 200
        print(f"? TEST 12: API history endpoint works")
        return True
    except Exception as e:
        print(f"? TEST 12: {e}")
        return False
tests = [test_1, test_2, test_3, test_4, test_5, test_6, test_7, test_8, test_9, test_10, test_11, test_12]
results = [test() for test in tests]
passed = sum(results)
total = len(results)
print(f"\nRESULTS: {passed}/{total} passed\n")
sys.exit(0 if passed == total else 1)
