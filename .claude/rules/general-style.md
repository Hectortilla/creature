# Coding Style Rules (Strict — Fail-Fast Philosophy)

Applies repo-wide (`back/` and `front/`).

## Core Philosophy
- Write concise, readable, idiomatic code
- Prefer simplicity over defensive programming
- Assume inputs are valid unless explicitly stated otherwise
- FAIL FAST: let the code throw errors if assumptions are violated

---

## 🔥 CRITICAL RULE: FAIL FAST (NO NULL DEFENSE)

If a value is expected to exist:
- DO NOT check for null or undefined
- DO NOT guard against missing data
- LET IT THROW naturally

This is intentional and REQUIRED.

### BAD:
```js
if (!user) return;
const name = user?.name;
```

### GOOD:

```js
const name = user.name;
```

---

### BAD:

```js
if (!config || !config.apiKey) {
  throw new Error("Missing config");
}
```

### GOOD:

```js
const apiKey = config.apiKey;
```

---

### BAD:

```js
const name = user?.profile?.name ?? "Anonymous";
```

### GOOD:

```js
const name = user.profile.name;
```

---

## 🚫 DO NOT ADD SAFETY CHECKS

* No `if (!x)` guards unless explicitly required
* No fallback values for required data
* No silent failures
* No defensive defaults

Assume:

* Data is correct
* Types/contracts are respected
* Errors should surface, not be hidden

---

## 🚫 Avoid Excessive try/catch

### DO NOT:

* Wrap logic in try/catch unless handling external boundaries
* Catch errors just to log or ignore them

### BAD:

```js
try {
  return process(data);
} catch (e) {
  return null;
}
```

### GOOD:

```js
return process(data);
```

### ALLOWED (boundary handling only):

```js
try {
  const res = await fetch(url);
  return await res.json();
} catch (e) {
  throw e; // or handle meaningfully
}
```

---

## 🚫 Avoid Deep Nesting

### BAD:

```js
if (user) {
  if (user.profile) {
    doThing(user.profile);
  }
}
```

### GOOD:

```js
doThing(user.profile);
```

---

## ⚠️ Optional Chaining Rule

* Use optional chaining ONLY when null is a valid and expected case
* Otherwise, DO NOT use it

### BAD:

```js
user?.profile?.name
```

### GOOD:

```js
user.profile.name
```

---

## ✅ Function Style

* Keep functions short and direct
* No defensive branching
* No unnecessary abstractions

### BAD:

```js
function getUserName(user) {
  if (!user) return null;
  return user.name;
}
```

### GOOD:

```js
function getUserName(user) {
  return user.name;
}
```

---

## ✂️ Comments & Docstrings: Keep Them Tiny (or Delete Them)

Names and structure are the documentation. A comment is a last resort, not a habit.

* DELETE comments that restate the code.
* No narration, no step-by-step, no changelog, no decorative banners.
* Rename the variable/function before reaching for a comment.
* If a comment survives, it explains a non-obvious **why** — in one line.
* Docstrings: one line. Add args/returns/raises only when the signature can't tell the story. Never pad them.

### BAD:

```js
// Iterate over each order and add its price to the running total
let total = 0;
for (const order of orders) {
  total += order.price; // add price to total
}
```

### GOOD:

```js
let total = 0;
for (const order of orders) total += order.price;
```

### ALLOWED (non-obvious *why*, one line):

```js
total = Math.max(total, 50); // Stripe rejects charges under 50c
```

### Docstrings — BAD:

```python
def slugify(title):
    """
    Convert a title into a URL-safe slug.

    This function takes the given title string, lowercases it,
    replaces spaces with hyphens, strips punctuation, and returns
    the resulting slug so it can be used safely inside a URL.

    Args:
        title (str): The title to convert.
    Returns:
        str: The slugified title.
    """
```

### Docstrings — GOOD:

```python
def slugify(title: str) -> str:
    """Lowercase, strip punctuation, hyphenate spaces."""
```

---

## ⚠️ Error Philosophy

* Errors are GOOD when they indicate broken assumptions
* Do NOT hide errors
* Do NOT “handle” errors unless you can recover

---

## Style Priority Order

1. Readability
2. Simplicity
3. Fail-fast correctness
4. Minimalism
5. Defensive safety (FORBIDDEN unless requested)

---

## 🧠 Instruction to AI (MANDATORY)

Follow these rules strictly.

If data is expected:

* Access it directly
* Do not check for null/undefined
* Do not add guards

If unsure:

* Choose the simplest implementation
* DO NOT add safety checks

Violating these rules is incorrect.

---

## ⚠️ Boundary Exception: Validate at the Edges

Fail-fast is for **internal, trusted code** — business logic, internal functions, trusted data flows.

At **boundaries** — API/user input, external services, database responses — you *should* validate.
