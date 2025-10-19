# Discovery Motor V8 - Technical Design Document
**Version**: 8.0.0
**Date**: 2025-10-19
**Team**: Senior Engineering Team (30 years experience)
**Status**: DESIGN PHASE

---

## EXECUTIVE SUMMARY

**Objective**: Migrate from V7's monolithic sequential architecture to V8's distributed multi-process architecture with bidirectional negotiation and proactive discovery.

**Key Improvement**: Transform from one-way workflow (PM → Dev accepts) to intelligent collaboration (PM ↔ Dev negotiate → Discovery Motor enhances).

**Expected Impact**:
- **30-50% faster convergence** via parallel PM/Dev work
- **70% better architectures** via PM-Dev negotiation
- **+30% code quality** via Discovery Motor proactive analysis
- **Native concurrency** supporting N simultaneous projects

---

## ARCHITECTURE ANALYSIS: V7 → V8

### V7 Current Architecture (Monolithic)

```
┌─────────────────────────────────────────────────────────┐
│             orchestrator_v7.py (Single Process)          │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │  PM Agent    │───>│  Dev Agent   │                   │
│  │  (Claude)    │    │  (Claude)    │                   │
│  │  Function    │    │  Function    │                   │
│  │  Call        │    │  Call        │                   │
│  └──────────────┘    └──────────────┘                   │
│         │                   │                            │
│         └───────┬───────────┘                            │
│                 ▼                                        │
│        ┌──────────────────┐                              │
│        │  Security Agent  │                              │
│        │  QA Agent        │                              │
│        │  (Python Rules)  │                              │
│        └──────────────────┘                              │
│                                                          │
│  Communication: Function returns (in-memory)             │
│  Workflow: Sequential (PM → Dev → Validate → Loop)      │
│  Concurrency: V7.12 UUID fix (filesystem-based)         │
└─────────────────────────────────────────────────────────┘
```

**Limitations**:
1. **Sequential Execution**: PM must finish before Dev starts
2. **One-Way Communication**: Dev cannot challenge PM's architecture
3. **No Proactive Discovery**: Issues found reactively during validation
4. **Tight Coupling**: All agents in single process
5. **Limited Scalability**: Memory-bound, hard to distribute

---

### V8 Target Architecture (Multi-Process)

```
┌────────────────────────────────────────────────────────────────────┐
│                    DISCOVERY MOTOR V8                               │
│              Multi-Process Distributed Architecture                 │
└────────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PROCESS 1   │    │  PROCESS 2   │    │  PROCESS 3   │
│              │    │              │    │              │
│  PM Agent    │◄──►│  Dev Agent   │◄──►│  Discovery   │
│  (Claude)    │    │  (Claude)    │    │  Motor       │
│              │    │              │    │  (Claude)    │
│  pm_agent.py │    │  dev_agent.py│    │  discovery.py│
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    .shared/ Directory  │
              │   (Filesystem Queue)   │
              │                        │
              │  - pm/proposals/       │
              │  - dev/evaluations/    │
              │  - dev/implementations/│
              │  - discovery/insights/ │
              │  - state/convergence/  │
              └────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────────┐
       │       PROCESS 4 (Orchestrator)    │
       │                                   │
       │  - Spawn processes 1-3            │
       │  - Watch .shared/ (filesystem)    │
       │  - State machine (negotiation)    │
       │  - Async validators (Sec + QA)    │
       │  - Convergence detection          │
       │  - Git commits                    │
       └───────────────────────────────────┘
```

**Capabilities**:
1. **Parallel Execution**: PM and Dev can work simultaneously
2. **Bidirectional Negotiation**: Dev can counter-propose architecture
3. **Proactive Discovery**: Continuous code analysis and suggestions
4. **Loose Coupling**: Independent processes communicating via filesystem
5. **Horizontal Scalability**: Add more agents easily

---

## GAP ANALYSIS: V7 vs V8

| Component | V7 (Current) | V8 (Target) | Migration Complexity |
|-----------|--------------|-------------|---------------------|
| **PM Agent** | Function in orchestrator | Independent process | **HIGH** - Extract + add negotiation |
| **Dev Agent** | Function in orchestrator | Independent process | **HIGH** - Extract + add evaluation |
| **Security Agent** | Sync function | Async process | **MEDIUM** - Wrap existing validator |
| **QA Agent** | Sync function | Async process | **MEDIUM** - Wrap existing validator |
| **Discovery Motor** | Does not exist | New independent process | **HIGH** - New component |
| **Communication** | Function returns | Filesystem queue | **MEDIUM** - Already have .agents/ |
| **Orchestrator** | Sequential loop | State machine + watcher | **HIGH** - Complete rewrite |
| **Concurrency** | UUID fix (V7.12) | Native multi-process | **LOW** - Already working |

**Total Complexity**: **HIGH** (7-10 days for experienced team)

---

## V8 COMPONENT SPECIFICATIONS

### 1. PM Agent (Process 1) - `pm_agent_v8.py`

**Purpose**: Propose architecture and negotiate with Dev Agent

**Input** (reads from `.shared/state/objective.json`):
```json
{
  "objective": "REST API for task management",
  "iteration": 1,
  "timestamp": "2025-10-19T14:30:00"
}
```

**Output** (writes to `.shared/pm/proposal_{iteration}.json`):
```json
{
  "role": "pm",
  "iteration": 1,
  "action": "PROPOSE" | "ADJUST" | "AGREE",
  "architecture": {
    "modules": ["auth_service.py", "task_service.py", ...],
    "database": {...},
    "technologies": {...}
  },
  "reasoning": "Why this architecture is appropriate",
  "response_to_dev": ["Addressed concern X", "Modified module Y"]
}
```

**Process Loop**:
```python
while True:
    # 1. Check for new objective
    if objective_file.exists():
        objective = read_json(objective_file)
        proposal = propose_architecture(objective)
        write_json(pm_proposal_file, proposal)

    # 2. Check for Dev counter-proposal
    if dev_counter_file.exists():
        counter = read_json(dev_counter_file)
        if counter["action"] == "COUNTER":
            adjusted = adjust_architecture(counter)
            write_json(pm_proposal_file, adjusted)
        elif counter["action"] == "ACCEPT":
            write_json(pm_agreement_file, {"status": "agreed"})
            # Wait for next objective

    sleep(5)  # Poll every 5 seconds
```

**Key Features**:
- Maintains architecture state across iterations
- Can adjust proposals based on Dev feedback
- Signals agreement when negotiation complete

---

### 2. Dev Agent (Process 2) - `dev_agent_v8.py`

**Purpose**: Evaluate PM architecture, counter-propose if needed, implement code

**Input** (reads from `.shared/pm/proposal_{iteration}.json`):
```json
{
  "role": "pm",
  "architecture": {...}
}
```

**Output** (writes to `.shared/dev/evaluation_{iteration}.json`):
```json
{
  "role": "dev",
  "iteration": 1,
  "action": "ACCEPT" | "COUNTER",
  "concerns": [
    "Circular dependency between auth_service and task_service",
    "Missing index on user_id (performance issue)"
  ],
  "alternative_architecture": {
    "modules": ["auth_service.py", "task_service.py", "shared_models.py"],
    "reasoning": "Eliminates circular dependency via shared models"
  }
}
```

**Or Implementation** (`.shared/dev/implementation_{iteration}.json`):
```json
{
  "role": "dev",
  "status": "implemented",
  "output_dir": "workspace/v8_projects/project_20251019_143000",
  "files": [
    {"path": "src/auth_service.py", "content": "..."},
    ...
  ]
}
```

**Process Loop**:
```python
while True:
    # 1. Check for PM proposal
    if pm_proposal_file.exists():
        proposal = read_json(pm_proposal_file)

        # Evaluate architecture
        evaluation = evaluate_architecture(proposal)

        if evaluation["has_issues"]:
            # Counter-propose
            counter = create_counter_proposal(evaluation)
            write_json(dev_counter_file, counter)
        else:
            # Accept and implement
            write_json(dev_acceptance_file, {"status": "accepted"})
            implementation = generate_code(proposal)
            write_json(dev_implementation_file, implementation)
            write_files_to_disk(implementation)

    # 2. Check for validation feedback
    if validation_feedback_file.exists():
        feedback = read_json(validation_feedback_file)
        improved_code = improve_based_on_feedback(feedback)
        write_json(dev_implementation_file, improved_code)

    sleep(5)
```

**Key Features**:
- Technical evaluation of PM proposals
- Can challenge architecture decisions
- Implements code only after agreement
- Improves code based on validator feedback

---

### 3. Discovery Motor (Process 3) - `discovery_agent_v8.py`

**Purpose**: Proactive code analysis and continuous improvement suggestions

**Input** (watches `.shared/dev/implementation_*.json`):
```json
{
  "output_dir": "workspace/v8_projects/project_...",
  "files": [...]
}
```

**Output** (writes to `.shared/discovery/insights_{timestamp}.json`):
```json
{
  "role": "discovery",
  "timestamp": "2025-10-19T14:35:00",
  "insights": [
    {
      "type": "performance",
      "severity": "high",
      "file": "src/auth_service.py:45",
      "issue": "N+1 query detected in get_user_permissions()",
      "suggestion": "Use join() instead of separate queries",
      "estimated_impact": "50% faster for users with many permissions"
    },
    {
      "type": "security",
      "severity": "critical",
      "file": "src/task_service.py:12",
      "issue": "SQL injection vulnerability in search_tasks()",
      "suggestion": "Use parameterized queries",
      "cwe": "CWE-89"
    },
    {
      "type": "refactoring",
      "severity": "medium",
      "file": "src/auth_service.py:100-150",
      "issue": "Code duplication in JWT encode/decode",
      "suggestion": "Extract to jwt_utils.py"
    }
  ],
  "recommended_actions": [
    "Fix CWE-89 immediately",
    "Optimize N+1 queries before production",
    "Refactor JWT utils in next iteration"
  ]
}
```

**Process Loop**:
```python
while True:
    # Watch for new implementations
    for impl_file in glob(".shared/dev/implementation_*.json"):
        if not analyzed(impl_file):
            impl = read_json(impl_file)

            # Deep analysis
            insights = analyze_code(impl["output_dir"])

            # Detect patterns
            code_smells = detect_code_smells(insights)
            security_gaps = detect_security_gaps(insights)
            performance_issues = detect_performance_issues(insights)

            # Write insights
            write_json(discovery_insights_file, {
                "insights": insights,
                "code_smells": code_smells,
                "security_gaps": security_gaps,
                "performance_issues": performance_issues
            })

            mark_analyzed(impl_file)

    sleep(10)  # Analyze every 10 seconds
```

**Key Features**:
- Continuous monitoring of code quality
- Proactive detection (before validators fail)
- Prioritized recommendations
- Learning from patterns across projects

---

### 4. Orchestrator V8 (Process 4) - `orchestrator_v8.py`

**Purpose**: Coordinate all agents, manage state, detect convergence

**State Machine**:
```
INIT
  ↓ write objective
PM_PROPOSE
  ↓ PM writes proposal
DEV_EVALUATE
  ├─ COUNTER → PM_ADJUST → PM_PROPOSE
  └─ ACCEPT → DEV_IMPLEMENT
DEV_IMPLEMENT
  ↓ Dev writes implementation
DISCOVERY_ANALYZE (parallel)
  ↓ Discovery writes insights
VALIDATE (async)
  ├─ Security Agent
  └─ QA Agent
  ↓
CONVERGENCE_CHECK
  ├─ scores >= 9.5 → CONVERGED ✅
  └─ scores < 9.5 → DEV_IMPROVE → VALIDATE
```

**Main Loop**:
```python
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class V8Orchestrator:
    def __init__(self):
        self.state = "INIT"
        self.iteration = 0
        self.pm_process = None
        self.dev_process = None
        self.discovery_process = None

    async def run(self, objective):
        # 1. Spawn agent processes
        self.spawn_agents()

        # 2. Write objective
        write_json(".shared/state/objective.json", {
            "objective": objective,
            "iteration": 1
        })

        # 3. Start filesystem watcher
        observer = Observer()
        handler = SharedDirHandler(self)
        observer.schedule(handler, ".shared", recursive=True)
        observer.start()

        # 4. Wait for convergence or timeout
        while self.state != "CONVERGED" and self.iteration < MAX_ITERATIONS:
            await asyncio.sleep(1)

        # 5. Cleanup
        observer.stop()
        observer.join()
        self.kill_agents()

        return self.get_result()

    def spawn_agents(self):
        self.pm_process = subprocess.Popen(["python", "pm_agent_v8.py"])
        self.dev_process = subprocess.Popen(["python", "dev_agent_v8.py"])
        self.discovery_process = subprocess.Popen(["python", "discovery_agent_v8.py"])

    def on_file_change(self, event):
        """Handle filesystem events"""
        if "pm/proposal" in event.src_path:
            self.state = "DEV_EVALUATE"
        elif "dev/evaluation" in event.src_path:
            eval_data = read_json(event.src_path)
            if eval_data["action"] == "COUNTER":
                self.state = "PM_ADJUST"
            elif eval_data["action"] == "ACCEPT":
                self.state = "DEV_IMPLEMENT"
        elif "dev/implementation" in event.src_path:
            self.state = "VALIDATE"
            asyncio.create_task(self.run_validators())

    async def run_validators(self):
        """Run Security + QA in parallel"""
        security_task = asyncio.create_task(validate_security_async())
        qa_task = asyncio.create_task(validate_qa_async())

        security_result, qa_result = await asyncio.gather(security_task, qa_task)

        if (security_result["score"] >= 9.5 and
            qa_result["score"] >= 9.5):
            self.state = "CONVERGED"
        else:
            # Write feedback for Dev to improve
            write_json(".shared/state/validation_feedback.json", {
                "security": security_result,
                "qa": qa_result
            })
            self.iteration += 1
```

**Key Features**:
- Non-blocking event-driven architecture
- Async validators (don't block main loop)
- Watchdog for filesystem monitoring
- Clean state management

---

## COMMUNICATION PROTOCOL

### Message Types

**1. OBJECTIVE** (Orchestrator → PM):
```json
{
  "type": "OBJECTIVE",
  "objective": "REST API for task management",
  "iteration": 1,
  "timestamp": "2025-10-19T14:30:00"
}
```

**2. PROPOSAL** (PM → Dev):
```json
{
  "type": "PROPOSAL",
  "architecture": {...},
  "reasoning": "..."
}
```

**3. EVALUATION** (Dev → PM):
```json
{
  "type": "EVALUATION",
  "action": "COUNTER" | "ACCEPT",
  "concerns": [...],
  "alternative": {...}
}
```

**4. IMPLEMENTATION** (Dev → Orchestrator):
```json
{
  "type": "IMPLEMENTATION",
  "output_dir": "...",
  "files": [...]
}
```

**5. INSIGHTS** (Discovery → Orchestrator):
```json
{
  "type": "INSIGHTS",
  "insights": [...],
  "priority_actions": [...]
}
```

**6. VALIDATION** (Orchestrator → Dev):
```json
{
  "type": "VALIDATION_FEEDBACK",
  "security_issues": [...],
  "qa_issues": [...]
}
```

### Filesystem Queue Structure

```
.shared/
├── state/
│   ├── objective.json              # Current objective
│   ├── iteration.json              # Current iteration number
│   ├── convergence.json            # Final result
│   └── validation_feedback.json   # Feedback for Dev
│
├── pm/
│   ├── proposal_001.json
│   ├── proposal_002.json
│   └── agreement.json
│
├── dev/
│   ├── evaluation_001.json
│   ├── counter_proposal_001.json
│   ├── acceptance.json
│   └── implementation_001.json
│
├── discovery/
│   ├── insights_001.json
│   ├── insights_002.json
│   └── recommendations.json
│
└── validation/
    ├── security_001.json
    └── qa_001.json
```

---

## TECHNOLOGY STACK

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Communication** | Filesystem (JSON) | Simple, debuggable, already working in V7.12 |
| **Process Management** | `subprocess.Popen` | Native Python, cross-platform |
| **File Watching** | `watchdog` library | Mature, event-driven, cross-platform |
| **Async Execution** | `asyncio` | Native Python, good for I/O-bound tasks |
| **State Management** | JSON files | Human-readable, versionable, simple |
| **Agents** | Claude CLI | Already proven in V7 |
| **Validators** | Existing V5/V7 code | Reuse what works |

**Why NOT RabbitMQ/Redis/ZeroMQ?**
- Adds external dependencies
- Increases deployment complexity
- Filesystem is sufficient for 3-5 processes
- Can migrate later if needed

---

## MIGRATION STRATEGY

### Phase 1: Foundation (Days 1-2)
- [ ] Create `.shared/` directory structure
- [ ] Implement message types (`message_types.py`)
- [ ] Extract PM Agent prompt logic to `pm_agent_v8.py`
- [ ] Extract Dev Agent prompt logic to `dev_agent_v8.py`
- [ ] Test PM and Dev as independent processes

### Phase 2: Negotiation (Days 3-4)
- [ ] Implement Dev evaluation logic
- [ ] Implement PM adjustment logic
- [ ] Add counter-proposal workflow
- [ ] Test PM ↔ Dev negotiation cycle

### Phase 3: Discovery Motor (Days 5-6)
- [ ] Create `discovery_agent_v8.py`
- [ ] Implement code analysis prompts
- [ ] Add pattern detection (code smells, security gaps)
- [ ] Integrate with validation feedback

### Phase 4: Orchestrator (Days 7-8)
- [ ] Rewrite orchestrator with state machine
- [ ] Add filesystem watcher (`watchdog`)
- [ ] Implement async validators
- [ ] Add convergence detection

### Phase 5: Testing & Polish (Days 9-10)
- [ ] End-to-end test with 3 real projects
- [ ] Performance benchmarking vs V7
- [ ] Documentation
- [ ] Create migration guide

---

## BACKWARDS COMPATIBILITY

V8 will support V7 mode via CLI flag:

```python
# orchestrator_v8.py
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["v7", "v8"], default="v8")
    args = parser.parse_args()

    if args.mode == "v7":
        # Import and run V7 monolithic code
        from orchestrator_v7 import run_v7_loop
        run_v7_loop(objective, dialogue_log)
    else:
        # Run V8 multi-process
        orchestrator = V8Orchestrator()
        asyncio.run(orchestrator.run(objective))
```

---

## SUCCESS METRICS

| Metric | V7 Baseline | V8 Target | Measurement |
|--------|-------------|-----------|-------------|
| **Convergence Rate** | ~70% | ≥90% | % projects that converge |
| **Avg Iterations** | 5-8 | ≤4 | Iterations to convergence |
| **Time to Convergence** | 20-40 min | ≤30 min | Total time for average project |
| **Architecture Quality** | 60% optimal | ≥80% | PM-Dev negotiation improves design |
| **Proactive Issues Found** | 0 | ≥3/project | Discovery Motor catches issues early |
| **Concurrent Projects** | 2-3 | ≥5 | Scalability test |

---

## RISKS & MITIGATION

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| **Filesystem race conditions** | HIGH | MEDIUM | Use atomic writes, file locking |
| **Process communication latency** | MEDIUM | LOW | Optimize poll intervals, use inotify |
| **Discovery Motor adds overhead** | MEDIUM | MEDIUM | Make async, only analyze on changes |
| **Complex state machine bugs** | HIGH | MEDIUM | Extensive testing, state logging |
| **V7 regression** | LOW | LOW | Keep V7 mode, gradual migration |

---

## NEXT STEPS

**Immediate Action**: Begin Phase 1 (Foundation)

1. Create `.shared/` directory structure
2. Define message types in `protocols/message_types.py`
3. Extract PM Agent to `agents/pm_agent_v8.py`
4. Extract Dev Agent to `agents/dev_agent_v8.py`
5. Test independent process communication

**Timeline**: 10 days for full V8 implementation

**Approval Required**: Team lead sign-off on architecture before Phase 1

---

**Document Version**: 1.0
**Last Updated**: 2025-10-19
**Next Review**: After Phase 1 completion
