---
paths:
  - "back/**/*.py"
---

# Python Style (`back/`)

Mandatory styling rules for the `creature` backend. Code that violates them is
considered **incorrect**, even if it works.

---

## Core Principles

* Enforce **DRY (Don’t Repeat Yourself)**
* Prioritize **readability and maintainability**
* Minimize **visual nesting**
* Avoid **unnecessary abstraction and duplication**
* Optimize for **human comprehension**

---

## Code Style and Structure


* *Write concise, idiomatic Python code with accurate examples.*
* *Follow Python conventions and best practices.*
* *Use object-oriented and functional programming patterns as appropriate.*
* *Prefer iteration and modularization over code duplication.*
* *Use descriptive variable and method names (e.g., user_signed_in, calculate_total).*


---

## DRY (Hard Enforcement — Strict)

### No Duplicated Workflows (Mandatory)

If two or more code paths:

* execute the **same sequence of operations**
* express the **same intent**
* differ only by parameters, flags, configuration, or small variations

➡️ **They represent the same workflow and MUST be refactored.**

Duplication is **structural**, not textual.
Different names, control flow, or formatting **do not imply different logic**.
Duplication is a **design error** and **explicitly forbidden**.

---

### Parameterize, Don’t Fork

❌ Bad

```python
if debug:
    run()
    log()
else:
    run()
```

✅ Good

```python
def run_process(*, debug=False):
    run()
    if debug:
        log()
```

---

### What “Same Workflow” Means

Two code blocks are the same workflow if:

* steps occur in the same order
* behavior is equivalent
* a change would need to be applied in more than one place

---

## Examples (Bad → Required Refactor)

### 1. Same Workflow, Different Functions

❌ Bad

```python
def process_a(x):
    validate(x)
    result = compute(x)
    save(result)
```

```python
def process_b(y):
    validate(y)
    result = compute(y)
    save(result)
```

✅ Good

```python
def process(value):
    validate(value)
    result = compute(value)
    save(result)

def process_a(x):
    return process(x)

def process_b(y):
    return process(y)
```

---

### 2. Same Workflow, Optional Behavior

❌ Bad

```python
def handle(x):
    validate(x)
    compute(x)
```

```python
def handle_debug(x):
    validate(x)
    compute(x)
    log(x)
```

✅ Good

```python
def handle(x, *, debug=False):
    validate(x)
    compute(x)
    if debug:
        log(x)
```

---

### 3. Same Workflow, Different Variable Names

❌ Bad

```python
start = now()
output = run(a)
elapsed = now() - start
```

```python
begin = now()
result = run(b)
duration = now() - begin
```

✅ Good

```python
def timed_run(value):
    start = now()
    result = run(value)
    return result, now() - start
```

---

### 4. Same Workflow, Different Control Flow Shape

❌ Bad

```python
validate(x)
if success(x):
    save(x)
```

```python
if not success(x):
    return
save(x)
```

✅ Good

```python
def save_if_success(x):
    if success(x):
        save(x)
```

---

### 5. Same Workflow, Extra Guard Logic

❌ Bad

```python
def process(x):
    validate(x)
    compute(x)
```

```python
def process_optional(x):
    if x is None:
        return
    validate(x)
    compute(x)
```

✅ Good

```python
def _process(x):
    validate(x)
    compute(x)

def process_optional(x):
    if x is None:
        return
    _process(x)
```

---

### 6. Same Workflow, Different Wrapping Context

❌ Bad

```python
def run():
    validate(data)
    compute(data)
```

```python
def run_with_lock():
    with lock:
        validate(data)
        compute(data)
```

✅ Good

```python
def _run_core(data):
    validate(data)
    compute(data)

def run():
    _run_core(data)

def run_with_lock():
    with lock:
        _run_core(data)
```

---

### What Is NOT a Valid Excuse

The following are **explicitly invalid justifications** for duplication:

* “It’s clearer this way”
* “They might diverge later”
* “This is only a small copy”
* “Different callers”
* “Sync vs async”

If the workflow is the same → **refactor immediately**.

---

## Variables

### Single-Use Variables

Do **not** introduce a variable if it is:

* used only once
* used immediately
* readable inline

❌ Bad
```python
value = compute()
consume(value)
```

✅ Good

```python
consume(compute())
```

---

### Single-Use Variables — Allowed Exceptions

A single-use variable is allowed **only if it**:

* reduces nesting
* simplifies a complex expression
* improves formatting/alignment
* captures meaningful domain intent
* aids debugging or logging

If it doesn’t add semantic value → inline it.

---

### Pass-Through Variables (Forbidden)

Do **not** create variables whose only purpose is to be passed to another call.

❌ Bad

```python
mimetype = file.content_type or "unknown"
track(mimetype=mimetype)
```

✅ Good

```python
track(mimetype=file.content_type or "unknown")
```

---

## Control Flow

### Reduce Nesting

Prefer:

* flat control flow
* early returns
* simple boolean logic

❌ Bad

```python
if a:
    if b:
        do()
```

✅ Good

```python
if a and b:
    do()
```

---

### Early Returns

❌ Bad

```python
if data:
    if valid(data):
        return process(data)
return None
```

✅ Good

```python
if not data or not valid(data):
    return None
return process(data)
```

---

## Functions

### Nested Functions

Avoid nested functions by default.

Allowed **only if**:

* very small
* logically scoped
* used as wrappers (retry, callback, etc.)

---

## Exception Handling

* Do **not** catch exceptions you don’t handle
* Do **not** catch just to log + re-raise
* Catch **specific exceptions only** when adding value

❌ Bad

```python
try:
    run()
except Exception as e:
    print(e)
    raise
```

✅ Good

```python
run()
```

---

## Comments

**Default to ONE line per comment and docstring; deleting it is often better. Only genuinely complex code may run a tiny bit longer, and only rarely** — see the 🔥 CRITICAL RULE in [`general-style.md`](general-style.md). Python-specific nuance:

### Inline comments for implicit state (allowed)

A one-line, same-line comment is fine when a value encodes **implicit/sentinel state**
(`None`, `0`, empty list) whose meaning the name doesn't carry.

✅ Good

```python
if cache is None:  # cache invalidated
    rebuild()
```

❌ Still bad — restates syntax

```python
if x is None:  # x is None
    ...
```

---

## Naming

* Prefer explicit over short
* Avoid cryptic abbreviations
* Names must express **intent**

---

## Enforcement Heuristic (Mandatory)

Before emitting code, verify:

> “If I change this logic, would I need to update more than one place?”

If **yes**, the output is incorrect.

---

## One-Line Rule (Memory Anchor)

> **Never copy a workflow. Extract it, name it, reuse it.**