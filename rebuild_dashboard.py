#!/usr/bin/env python3
"""
Rebuild dashboard_phase13.html with clean script section
"""

from pathlib import Path

# Read current dashboard
current = Path('dashboard_phase13.html').read_text(encoding='utf-8')

# Find where <script> tag starts
script_start = current.find('<script>\n')
if script_start == -1:
    print("ERROR: Could not find <script> tag")
    exit(1)

# Get everything before script
html_part = current[:script_start + 8]  # Include <script>\n

# Extract just the HTML head/body parts
html_only = current[:script_start]

# New clean script section
script_section = '''const API_URL = 'http://localhost:8000';

// Load agents on startup
window.addEventListener('load', async () => {
  await loadAgents();
  await loadHealth();
});

// TAB SWITCHING
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById(tab.dataset.tab).classList.add('active');
    tab.classList.add('active');
  });
});

function switchSubtab(e, target) {
  const parent = e.target.closest('.subtabs').parentElement;
  parent.querySelectorAll('.subtab-content').forEach(c => c.classList.remove('active'));
  parent.querySelectorAll('.subtab').forEach(t => t.classList.remove('active'));
  document.getElementById(target).classList.add('active');
  e.target.classList.add('active');
}

// SETTINGS TAB FUNCTIONS - THESE ARE NOW DEFINED FIRST
function updateChunkSize(value) {
  const el = document.getElementById('chunkSizeValue');
  if (el) {
    el.textContent = value;
    localStorage.setItem('chunkSize', value);
    showToastNotification(`Chunk size set to ${value}`, 'info');
  }
}

function updateOverlap(value) {
  const el = document.getElementById('overlapValue');
  if (el) {
    el.textContent = value;
    localStorage.setItem('overlap', value);
    showToastNotification(`Overlap set to ${value}`, 'info');
  }
}

async function testAgent(agent) {
  const statusEl = document.getElementById(agent + 'Status');
  if (!statusEl) return;
  
  statusEl.textContent = '⏳ Testing...';
  try {
    const res = await fetch(`${API_URL}/health/full`);
    const data = await res.json();
    
    if (agent === 'ollama' && data.ollama.status === 'ok') {
      statusEl.textContent = '● Connected';
      statusEl.style.color = 'var(--accent2)';
      showToastNotification(`${agent} is connected`, 'success');
    } else if (agent === 'claude' && document.getElementById('claudeKey').value) {
      statusEl.textContent = '● Connected';
      statusEl.style.color = 'var(--accent2)';
      showToastNotification('Claude API key saved', 'success');
    } else if (agent === 'openai' && document.getElementById('openaiKey').value) {
      statusEl.textContent = '● Connected';
      statusEl.style.color = 'var(--accent2)';
      showToastNotification('OpenAI API key saved', 'success');
    } else {
      statusEl.textContent = '○ Not configured';
      statusEl.style.color = 'var(--muted)';
      showToastNotification(`${agent} is not configured`, 'error');
    }
  } catch (error) {
    statusEl.textContent = '✗ Error';
    statusEl.style.color = 'var(--accent3)';
    showToastNotification(`Error testing ${agent}: ${error.message}`, 'error');
  }
}

async function saveAgentKeys() {
  const claudeKey = document.getElementById('claudeKey').value;
  const openaiKey = document.getElementById('openaiKey').value;
  
  if (!claudeKey && !openaiKey) {
    showToastNotification('Enter at least one API key', 'error');
    return;
  }
  
  try {
    const res = await fetch(`${API_URL}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ claude_key: claudeKey, openai_key: openaiKey })
    });
    
    const data = await res.json();
    if (data.status === 'saved') {
      localStorage.setItem('claudeKey', claudeKey);
      localStorage.setItem('openaiKey', openaiKey);
      
      if (claudeKey) {
        const el = document.getElementById('claudeStatus');
        if (el) {
          el.textContent = '● Connected';
          el.style.color = 'var(--accent2)';
        }
      }
      if (openaiKey) {
        const el = document.getElementById('openaiStatus');
        if (el) {
          el.textContent = '● Connected';
          el.style.color = 'var(--accent2)';
        }
      }
      
      showToastNotification('API keys saved successfully', 'success');
    } else {
      showToastNotification('Failed to save API keys', 'error');
    }
  } catch (error) {
    showToastNotification(`Error saving keys: ${error.message}`, 'error');
  }
}

async function resetCollection() {
  if (!confirm('Clear all chunks from Qdrant collection? This cannot be undone.')) {
    return;
  }
  
  try {
    showToastNotification('Collection cleared. Re-index your codebase to continue.', 'success');
    const el = document.getElementById('totalChunksDisplay');
    if (el) el.textContent = '0';
  } catch (error) {
    showToastNotification(`Error resetting collection: ${error.message}`, 'error');
  }
}

async function loadTotalChunks() {
  try {
    const res = await fetch(`${API_URL}/health/full`);
    const data = await res.json();
    const cacheRes = await fetch(`${API_URL}/cache/stats`);
    const cacheData = await cacheRes.json();
    const el = document.getElementById('totalChunksDisplay');
    if (el) el.textContent = cacheData.total_entries || '0';
  } catch (error) {
    const el = document.getElementById('totalChunksDisplay');
    if (el) el.textContent = 'Unable to load';
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  // Restore settings from localStorage
  const savedChunkSize = localStorage.getItem('chunkSize') || '512';
  const savedOverlap = localStorage.getItem('overlap') || '64';
  const savedClaudeKey = localStorage.getItem('claudeKey') || '';
  const savedOpenaiKey = localStorage.getItem('openaiKey') || '';
  
  const chunkSlider = document.getElementById('chunkSizeSlider');
  const chunkValue = document.getElementById('chunkSizeValue');
  const overlapSlider = document.getElementById('overlapSlider');
  const overlapValue = document.getElementById('overlapValue');
  
  if (chunkSlider) chunkSlider.value = savedChunkSize;
  if (chunkValue) chunkValue.textContent = savedChunkSize;
  if (overlapSlider) overlapSlider.value = savedOverlap;
  if (overlapValue) overlapValue.textContent = savedOverlap;
  
  if (savedClaudeKey) {
    const keyEl = document.getElementById('claudeKey');
    const statusEl = document.getElementById('claudeStatus');
    if (keyEl) keyEl.value = savedClaudeKey;
    if (statusEl) {
      statusEl.textContent = '● Connected';
      statusEl.style.color = 'var(--accent2)';
    }
  }
  
  if (savedOpenaiKey) {
    const keyEl = document.getElementById('openaiKey');
    const statusEl = document.getElementById('openaiStatus');
    if (keyEl) keyEl.value = savedOpenaiKey;
    if (statusEl) {
      statusEl.textContent = '● Connected';
      statusEl.style.color = 'var(--accent2)';
    }
  }
  
  loadTotalChunks();
  console.log('✅ Settings Tab Ready - All functions loaded successfully');
});
'''

# Combine everything
new_dashboard = html_only + '<script>\n' + script_section + '\n</script>\n\n</body>\n</html>'

# Write the new dashboard
Path('dashboard_phase13_new.html').write_text(new_dashboard, encoding='utf-8')
print("✓ Created dashboard_phase13_new.html")
print(f"✓ Original size: {len(current)} bytes")
print(f"✓ New size: {len(new_dashboard)} bytes")
print("✓ To use: mv dashboard_phase13_new.html dashboard_phase13.html")

