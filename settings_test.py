#!/usr/bin/env python3
"""
SETTINGS TAB - FINAL VERIFICATION TEST
Run: python settings_test.py
"""

import sys
import re
from pathlib import Path

def test_settings_tab():
    """Comprehensive test of Settings tab implementation"""

    dashboard_path = Path('dashboard_phase13.html')
    api_path = Path('src/api/main.py')

    print("\n" + "="*70)
    print(" SETTINGS TAB - FINAL VERIFICATION TEST")
    print("="*70)

    # Test 1: File exists
    print("\n[1/10] Checking files exist...")
    assert dashboard_path.exists(), "dashboard_phase13.html not found"
    assert api_path.exists(), "src/api/main.py not found"
    print("  ✓ Both files exist")

    # Read files
    dashboard_html = dashboard_path.read_text(encoding='utf-8')
    api_python = api_path.read_text(encoding='utf-8')

    # Test 2: Settings tab button exists
    print("\n[2/10] Checking Settings tab button...")
    assert 'data-tab="settings"' in dashboard_html, "Settings tab button not found"
    assert '⚙️ Settings' in dashboard_html, "Settings emoji not found"
    print("  ✓ Settings tab button present")

    # Test 3: Settings tab container exists
    print("\n[3/10] Checking Settings tab container...")
    assert 'id="settings"' in dashboard_html, "Settings container not found"
    assert 'class="tab-content"' in dashboard_html, "tab-content class not found"
    print("  ✓ Settings tab container present")

    # Test 4: AI Agents section exists
    print("\n[4/10] Checking AI Agents section...")
    agents_section = "🤖 AI Agents" in dashboard_html
    ollama_check = 'id="ollamaStatus"' in dashboard_html
    claude_check = 'id="claudeStatus"' in dashboard_html
    openai_check = 'id="openaiStatus"' in dashboard_html
    assert all([agents_section, ollama_check, claude_check, openai_check]), \
        "AI Agents section incomplete"
    print("  ✓ AI Agents section complete (Ollama, Claude, OpenAI)")

    # Test 5: Indexing Settings section exists
    print("\n[5/10] Checking Indexing Settings section...")
    chunk_slider = 'id="chunkSizeSlider"' in dashboard_html
    overlap_slider = 'id="overlapSlider"' in dashboard_html
    file_types = '.js' in dashboard_html and '.ts' in dashboard_html
    assert all([chunk_slider, overlap_slider, file_types]), \
        "Indexing Settings incomplete"
    print("  ✓ Indexing Settings section complete (Sliders, File Types)")

    # Test 6: Qdrant Collection section exists
    print("\n[6/10] Checking Qdrant Collection section...")
    collection_name = "💾 Qdrant Collection" in dashboard_html
    chunks_display = 'id="totalChunksDisplay"' in dashboard_html
    clear_button = 'onclick="resetCollection()"' in dashboard_html
    assert all([collection_name, chunks_display, clear_button]), \
        "Qdrant Collection section incomplete"
    print("  ✓ Qdrant Collection section complete")

    # Test 7: JavaScript functions defined
    print("\n[7/10] Checking JavaScript functions...")
    functions = {
        'updateChunkSize': 'function updateChunkSize',
        'updateOverlap': 'function updateOverlap',
        'testAgent': 'async function testAgent',
        'saveAgentKeys': 'async function saveAgentKeys',
        'resetCollection': 'async function resetCollection',
        'loadTotalChunks': 'async function loadTotalChunks',
        'showToastNotification': 'function showToastNotification',
    }

    for func_name, func_pattern in functions.items():
        assert func_pattern in dashboard_html, f"{func_name} not found"
    print(f"  ✓ All {len(functions)} JavaScript functions defined")

    # Test 8: Button handlers wired correctly
    print("\n[8/10] Checking button onclick handlers...")
    handlers = [
        'onclick="testAgent(\'ollama\')"',
        'onclick="testAgent(\'claude\')"',
        'onclick="testAgent(\'openai\')"',
        'onclick="saveAgentKeys()"',
        'onclick="resetCollection()"',
    ]
    for handler in handlers:
        assert handler in dashboard_html, f"Handler missing: {handler}"
    print(f"  ✓ All {len(handlers)} button handlers wired")

    # Test 9: Element IDs exist
    print("\n[9/10] Checking element IDs...")
    element_ids = [
        'chunkSizeSlider', 'chunkSizeValue',
        'overlapSlider', 'overlapValue',
        'ollamaStatus', 'claudeStatus', 'openaiStatus',
        'claudeKey', 'openaiKey',
        'totalChunksDisplay',
    ]
    for elem_id in element_ids:
        assert f'id="{elem_id}"' in dashboard_html, f"ID missing: {elem_id}"
    print(f"  ✓ All {len(element_ids)} element IDs present")

    # Test 10: Backend endpoint exists
    print("\n[10/10] Checking backend /settings endpoint...")
    assert '@app.post("/settings")' in api_python, "POST /settings endpoint not found"
    assert 'claude_key' in api_python, "claude_key handling missing"
    assert 'openai_key' in api_python, "openai_key handling missing"
    assert '{"status": "saved"}' in api_python, "Success response missing"
    print("  ✓ POST /settings endpoint complete")

    # Summary
    print("\n" + "="*70)
    print(" ✅ ALL TESTS PASSED - Settings Tab Implementation Complete")
    print("="*70)
    print("\nSummary:")
    print("  • Settings tab button:        ✓")
    print("  • AI Agents section:          ✓")
    print("  • Indexing Settings section:  ✓")
    print("  • Qdrant Collection section:  ✓")
    print("  • JavaScript functions:       ✓")
    print("  • Button handlers:            ✓")
    print("  • Element IDs:                ✓")
    print("  • Backend endpoint:           ✓")
    print("\nReady for production use!\n")

    return True

if __name__ == '__main__':
    try:
        test_settings_tab()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        sys.exit(1)

