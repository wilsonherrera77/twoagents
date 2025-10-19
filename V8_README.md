# Discovery Motor V8 - Quick Start Guide

**Version**: 8.0.0 (Phase 1 Complete)
**Date**: 2025-10-19
**Status**: PHASE 1 - Foundation Complete

---

## WHAT IS V8?

Discovery Motor V8 es la evolución de V7 hacia una arquitectura **multi-proceso distribuida** donde PM y Dev agents negocian inteligentemente en lugar de seguir un workflow secuencial.

**Key Improvements over V7**:
- PM y Dev son procesos independientes (no funciones)
- Negociación bidireccional (Dev puede counter-proponer)
- Comunicación via filesystem (`.shared/` directory)
- Foundation lista para Discovery Motor y async validators

---

## ARCHITECTURE

```
┌──────────────┐    ┌──────────────┐
│  PM Agent    │◄──►│  Dev Agent   │
│  Process 1   │    │  Process 2   │
└──────┬───────┘    └──────┬───────┘
       │                   │
       └───────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │   .shared/ Directory  │
    │                       │
    │   - state/            │
    │   - pm/proposals/     │
    │   - dev/evaluations/  │
    │   - dev/implementations/ │
    └───────────────────────┘
```

---

## FILES IMPLEMENTED (Phase 1)

### Core Components

1. **`protocols/message_types.py`** (465 lines)
   - 7 typed message classes
   - JSON serialization/deserialization
   - Atomic file writes
   - Helper functions

2. **`agents/pm_agent_v8.py`** (376 lines)
   - Independent PM process
   - Proposes architecture
   - Adjusts based on Dev feedback
   - Signals agreement

3. **`agents/dev_agent_v8.py`** (438 lines)
   - Independent Dev process
   - Evaluates PM proposals
   - Can counter-propose
   - Generates code
   - Improves based on validation

4. **`test_v8_poc.py`** (284 lines)
   - Proof of Concept test
   - Validates inter-process communication
   - Tests negotiation workflow

### Documentation

5. **`V8_TECHNICAL_DESIGN.md`** (859 lines)
   - Complete technical specification
   - Architecture analysis V7 → V8
   - Component specifications
   - 5-phase migration plan
   - Success metrics

---

## DIRECTORY STRUCTURE

```
discovery_motor_final/
├── .shared/                  # NEW - Message queue
│   ├── state/                # Objective, iteration, feedback
│   ├── pm/                   # PM proposals
│   ├── dev/                  # Dev evaluations & implementations
│   ├── discovery/            # (Future) Discovery Motor insights
│   └── validation/           # (Future) Security + QA results
│
├── agents/                   # NEW - Independent agent processes
│   ├── pm_agent_v8.py        # PM Agent standalone
│   └── dev_agent_v8.py       # Dev Agent standalone
│
├── protocols/                # NEW - Message types
│   └── message_types.py      # Typed messages for communication
│
├── workspace/
│   └── v8_projects/          # V8 generated projects
│
├── test_v8_poc.py            # POC test script
├── V8_TECHNICAL_DESIGN.md    # Technical design doc
└── V8_README.md              # This file
```

---

## HOW TO RUN POC TEST

### Prerequisites

- Python 3.8+
- Claude CLI configured (`claude --print` works)
- All V7 dependencies installed

### Run Test

```bash
# From project root
python test_v8_poc.py
```

### Expected Output

```
[HH:MM:SS] [POC Test] [INFO] POC TEST V8 - Inter-Process Communication
[HH:MM:SS] [POC Test] [INFO] Starting PM Agent process...
[HH:MM:SS] [POC Test] [SUCCESS] PM Agent started (PID: 12345)
[HH:MM:SS] [POC Test] [INFO] Starting Dev Agent process...
[HH:MM:SS] [POC Test] [SUCCESS] Dev Agent started (PID: 12346)
[HH:MM:SS] [POC Test] [SUCCESS] PM proposed 6 modules
[HH:MM:SS] [POC Test] [SUCCESS] Dev action: ACCEPT (0 concerns)
[HH:MM:SS] [POC Test] [SUCCESS] Dev generated 12 files

Results:
  ✓ PASS - pm_proposal
  ✓ PASS - dev_evaluation
  ✓ PASS - dev_implementation
  ✓ PASS - negotiation_worked

[HH:MM:SS] [POC Test] [SUCCESS] POC TEST: SUCCESS ✓
```

### What the Test Validates

1. ✅ PM Agent runs as independent process
2. ✅ Dev Agent runs as independent process
3. ✅ Communication via `.shared/` filesystem works
4. ✅ PM can propose architecture
5. ✅ Dev can evaluate and respond
6. ✅ Negotiation workflow (COUNTER or ACCEPT) works
7. ✅ Dev can generate code after agreement

---

## MESSAGE TYPES

### 1. ObjectiveMessage
**From**: Orchestrator → PM
**File**: `.shared/state/objective.json`

```json
{
  "type": "OBJECTIVE",
  "role": "orchestrator",
  "objective": "REST API for task management",
  "iteration": 1,
  "timestamp": "2025-10-19T14:30:00"
}
```

### 2. ProposalMessage
**From**: PM → Dev
**File**: `.shared/pm/proposal_001.json`

```json
{
  "type": "PROPOSAL",
  "role": "pm",
  "action": "PROPOSE",
  "architecture": {
    "proposed_modules": ["auth_service.py", "task_service.py"],
    "database_schema": {...},
    "technologies": {...}
  },
  "reasoning": "...",
  "iteration": 1
}
```

### 3. EvaluationMessage
**From**: Dev → PM
**File**: `.shared/dev/evaluation_001.json`

```json
{
  "type": "EVALUATION",
  "role": "dev",
  "action": "COUNTER" | "ACCEPT",
  "concerns": ["Circular dependency between X and Y"],
  "alternative_architecture": {...},
  "iteration": 1
}
```

### 4. ImplementationMessage
**From**: Dev → Orchestrator
**File**: `.shared/dev/implementation_001.json`

```json
{
  "type": "IMPLEMENTATION",
  "role": "dev",
  "status": "implemented",
  "output_dir": "workspace/v8_projects/project_...",
  "files": [
    {"path": "src/module.py", "content": "..."}
  ],
  "iteration": 1
}
```

---

## NEGOTIATION WORKFLOW

### Scenario 1: Dev Accepts Immediately

```
1. Orchestrator writes objective.json
2. PM reads objective → proposes architecture → writes proposal_001.json
3. Dev reads proposal → evaluates → action="ACCEPT" → writes evaluation_001.json
4. PM reads evaluation → writes agreement.json
5. Dev generates code → writes implementation_001.json
```

### Scenario 2: Dev Counter-Proposes

```
1. Orchestrator writes objective.json
2. PM reads objective → proposes architecture → writes proposal_001.json
3. Dev reads proposal → finds issues → action="COUNTER" → writes evaluation_001.json
4. PM reads evaluation → adjusts architecture → writes proposal_002.json
5. Dev reads adjusted proposal → action="ACCEPT" → writes evaluation_002.json
6. PM writes agreement.json
7. Dev generates code → writes implementation_002.json
```

---

## PHASE 1 COMPLETION STATUS

### ✅ Completed

- [x] Directory structure (`.shared/`, `agents/`, `protocols/`)
- [x] Message types system (`protocols/message_types.py`)
- [x] PM Agent standalone process (`agents/pm_agent_v8.py`)
- [x] Dev Agent standalone process (`agents/dev_agent_v8.py`)
- [x] POC test script (`test_v8_poc.py`)
- [x] Technical design documentation
- [x] Atomic file writes (prevent race conditions)
- [x] State machine logic in agents

### 🔄 In Progress

- [ ] Run POC test to validate implementation
- [ ] Debug and fix any communication issues

### ⏳ Future Phases

**Phase 2** (Negotiation Enhancement):
- [ ] Improve counter-proposal prompts
- [ ] Add negotiation limits and fallbacks
- [ ] Logging and debugging improvements

**Phase 3** (Discovery Motor):
- [ ] Create `discovery_agent_v8.py`
- [ ] Code analysis prompts
- [ ] Pattern detection (security, performance, refactoring)

**Phase 4** (Orchestrator):
- [ ] Rewrite orchestrator with state machine
- [ ] Filesystem watcher (`watchdog` library)
- [ ] Async validators (Security + QA)
- [ ] Convergence detection

**Phase 5** (Testing & Polish):
- [ ] End-to-end tests with real projects
- [ ] Performance benchmarking vs V7
- [ ] Documentation and migration guide

---

## DIFFERENCES FROM V7

| Aspect | V7 | V8 Phase 1 |
|--------|----|-----------|
| **PM Agent** | Function in orchestrator | Independent process |
| **Dev Agent** | Function in orchestrator | Independent process |
| **Communication** | Function returns (in-memory) | Filesystem (.shared/) |
| **Negotiation** | One-way (Dev accepts) | Bidirectional (Dev can counter) |
| **State Management** | Local variables | JSON files |
| **Process Isolation** | Single process | Multi-process |
| **Debugging** | Harder (shared state) | Easier (isolated processes) |

---

## TROUBLESHOOTING

### POC Test Fails

**Issue**: `PM Agent started (PID: XXX)` but no proposal created

**Fix**:
1. Check Claude CLI works: `echo "test" | claude --print --output-format json`
2. Check `.agents/pm/outbox/` for response files
3. Check PM Agent stdout/stderr for errors

**Issue**: `Dev did not create evaluation`

**Fix**:
1. Verify proposal file exists in `.shared/pm/`
2. Check Dev Agent is polling correctly (5s intervals)
3. Check `.agents/dev/outbox/` for response files

### File Permission Errors

**Issue**: `PermissionError` when writing to `.shared/`

**Fix**:
- Use atomic writes (already implemented in `message_types.py`)
- Ensure no other processes are holding file locks
- On Windows: check antivirus isn't blocking

---

## NEXT STEPS

1. **Run POC Test**: `python test_v8_poc.py`
2. **Review Results**: Check if PM-Dev communication works
3. **Debug if Needed**: Fix any issues found in POC
4. **Proceed to Phase 2**: Enhance negotiation with better prompts
5. **Add Discovery Motor** (Phase 3): Proactive code analysis

---

## TECHNICAL NOTES

### Why Filesystem vs RabbitMQ/Redis?

**Pros**:
- ✅ No external dependencies
- ✅ Human-readable (can debug by looking at JSON files)
- ✅ Git-versionable
- ✅ Cross-platform
- ✅ V7.12 UUID fix already works with filesystem

**Cons**:
- ⚠️ Slower than message queues (but acceptable for 3-5 processes)
- ⚠️ Requires polling (5s intervals)

**Decision**: Start with filesystem, migrate to message queue if needed in future.

### Atomic Writes

All message writes use atomic pattern:
```python
# Write to temp file
temp_file.write_text(json_data)

# Atomic rename (works on Windows + Linux)
temp_file.replace(target_file)
```

This prevents race conditions when multiple processes write simultaneously.

---

**Created**: 2025-10-19
**Last Updated**: 2025-10-19
**Status**: Phase 1 Foundation Complete ✅
**Next**: Run POC test and validate
