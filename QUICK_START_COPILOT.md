# Quick Start: Using GitHub Copilot for MNR RT Service Development

**🎯 Goal:** Get contributors productive with GitHub Copilot in under 30 minutes

**📋 Prerequisites:** VS Code installed, GitHub account with Copilot access

---

## 5-Minute Setup

### 1. Install GitHub Copilot (2 minutes)

**In VS Code:**
1. Open Extensions (Ctrl+Shift+X)
2. Search "GitHub Copilot"
3. Click Install
4. Click Install for "GitHub Copilot Chat" (optional but recommended)

### 2. Authenticate (1 minute)

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "GitHub Copilot: Sign In"
3. Follow browser authentication
4. Return to VS Code

### 3. Verify It Works (1 minute)

Create a new Python file and type:
```python
# Function to fetch train data from API
def get_trains
```

**Expected:** Copilot suggests function parameters and body.  
**Action:** Press `Tab` to accept, or keep typing to modify.

### 4. Open the Repository (1 minute)

```bash
git clone https://github.com/jm0rt1/mnr-rt-service.git
cd mnr-rt-service
code .  # Opens in VS Code
```

---

## Your First Contribution (20 minutes)

### Choose Your Path

#### 🐍 Python Developer? → API Enhancement
**File:** `web_server.py`  
**Task:** Add a new endpoint  

```python
# Let Copilot help you create a new endpoint to get delay statistics
# Type this comment and let Copilot generate:
@app.route('/stats/delays/<route_id>')
def get_delay_stats(route_id):
    """Get average delay for a route"""
    # Copilot generates implementation
```

#### 🎨 Frontend Developer? → GUI Enhancement
**File:** `src/gui/controllers/main_window_controller.py`  
**Task:** Add dark mode toggle  

```python
# Let Copilot help with UI theme switching
def toggle_dark_mode(self):
    """Switch between light and dark themes"""
    # Copilot generates implementation
```

#### 📝 Technical Writer? → Documentation
**File:** `docs/NEW_FEATURE.md`  
**Task:** Document a feature  

```markdown
<!-- Ask Copilot Chat: "Document the /trains endpoint with examples" -->
```

#### 🔧 DevOps Engineer? → Testing
**File:** `tests/test_new_feature.py`  
**Task:** Add test coverage  

```python
# Let Copilot generate comprehensive tests
def test_get_trains_with_filters(self):
    """Test train filtering by route and station"""
    # Copilot generates test cases
```

---

## Copilot Power Tips

### Tip 1: Write Comments First
**Before:**
```python
def fetch():
    # vague, Copilot confused
```

**After:**
```python
def fetch():
    # Fetch trains from MTA API, filter by station_id='1',
    # and return enriched data with stop names
    # Copilot generates great code!
```

### Tip 2: Use Copilot Chat for Complex Questions
**Open Chat:** `Ctrl+Shift+I`

**Ask:**
- "How do I add WebSocket support to Flask?"
- "Show me how to parse GTFS-RT protobuf data"
- "Generate unit tests for the get_trains function"

### Tip 3: Accept, Modify, or Reject
- `Tab` - Accept suggestion
- `Alt+]` - Next suggestion
- `Alt+[` - Previous suggestion
- Keep typing - Modify/reject

### Tip 4: Leverage Type Hints
```python
from typing import List, Dict

# Copilot understands types better with hints
def process_trains(data: List[Dict]) -> List[str]:
    # Much better suggestions!
```

---

## Common Tasks with Copilot

### Task: Add New API Endpoint

1. **Open** `web_server.py`
2. **Type comment:**
   ```python
   # Create endpoint to get vehicle positions with filters
   @app.route('/vehicle-positions')
   ```
3. **Let Copilot generate** the function
4. **Press Tab** to accept or modify

### Task: Write Tests

1. **Open** `tests/test_web_server.py`
2. **Type:**
   ```python
   def test_vehicle_positions_endpoint(self):
       """Test vehicle positions with route filter"""
       # Copilot generates test
   ```
3. **Review** generated test
4. **Modify** as needed

### Task: Update Documentation

1. **Open** relevant `.md` file
2. **Type:**
   ```markdown
   ## New Feature: Vehicle Positions
   <!-- Copilot generates documentation -->
   ```
3. **Review** and edit

---

## Workstream Selection Guide

**Read:** [WORKSTREAMS.md](WORKSTREAMS.md) for complete details.

**Quick Pick:**

| You Like | Choose Workstream | Priority | Start File |
|----------|-------------------|----------|------------|
| Backend coding | Core API Development | 🔴 High | `web_server.py` |
| UI/UX | GUI Enhancement | 🟡 Medium | `src/gui/controllers/` |
| Writing | Documentation | 🔴 High | `docs/*.md` |
| Breaking things | Testing & QA | 🔴 High | `tests/` |
| Embedded systems | Arduino Integration | 🟡 Medium | `docs/arduino-train-clock/` |
| Security | Security & Compliance | 🔴 High | Security scan |
| Planning | Travel Assistance | 🟡 Medium | `src/travel_assist/` |
| AI/ML | Generative AI | 🟢 Low | `docs/generative-ai/` |

---

## Getting Help

### Copilot Not Working?
1. Check sign-in status: Look for Copilot icon in status bar
2. Reload window: `Ctrl+Shift+P` → "Reload Window"
3. Check output: `View` → `Output` → Select "GitHub Copilot"

### Need Code Review?
1. Make changes
2. Commit to branch
3. Create Pull Request
4. Tag reviewers

### Have Questions?
- Check [WORKSTREAMS.md](WORKSTREAMS.md) for detailed info
- Review [DOCUMENTATION_REVIEW_SUMMARY.md](DOCUMENTATION_REVIEW_SUMMARY.md)
- Ask in GitHub Issues
- Use Copilot Chat for technical questions

---

## Success Checklist

Before submitting PR:
- [ ] Code follows Python style (PEP 8)
- [ ] Added/updated tests
- [ ] Tests pass locally (`python -m unittest discover tests/`)
- [ ] Documentation updated
- [ ] Copilot helped accelerate development 🚀

---

## Example: Complete Feature Addition

**Goal:** Add endpoint to get train count by route

### Step 1: Plan (1 min)
Read workstream: Core API Development in [WORKSTREAMS.md](WORKSTREAMS.md#1-core-api-development)

### Step 2: Code with Copilot (10 min)

**File:** `web_server.py`
```python
# Add endpoint to count trains by route
@app.route('/stats/count/<route_id>')
def get_train_count(route_id):
    """
    Returns the number of active trains for a specific route.
    
    Args:
        route_id: Route identifier (e.g., "1" for Hudson)
    
    Returns:
        JSON with train count and route info
    """
    # Press Tab - Copilot generates implementation!
```

### Step 3: Test with Copilot (5 min)

**File:** `tests/test_web_server.py`
```python
def test_get_train_count_valid_route(self):
    """Test train count endpoint with valid route"""
    # Press Tab - Copilot generates test!
```

### Step 4: Document (2 min)

**File:** `README.md`
```markdown
### Get Train Count

**Endpoint:** `GET /stats/count/<route_id>`
<!-- Copilot fills in details -->
```

### Step 5: Submit (2 min)
```bash
git add .
git commit -m "feat: Add train count by route endpoint"
git push origin feature/train-count
# Create PR on GitHub
```

**Total Time:** ~20 minutes (vs 1-2 hours without Copilot!)

---

## Next Steps

1. ✅ Read this guide (you're here!)
2. ⬜ Install GitHub Copilot
3. ⬜ Clone repository
4. ⬜ Pick a workstream from [WORKSTREAMS.md](WORKSTREAMS.md)
5. ⬜ Make your first contribution
6. ⬜ Submit PR
7. ⬜ Celebrate! 🎉

---

**Questions?** Check [WORKSTREAMS.md](WORKSTREAMS.md) or ask in GitHub Issues.

**Ready to contribute?** Pick a workstream and start coding with AI assistance!
