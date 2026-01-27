# AGENTS – Portable Guide to Cursor Rule Files

This document explains how **any** AI agent can discover and follow Cursor rule files in a repository.  Copy it into another project and it should still make sense without modification.

---
## 1. Rule File Locations

| Folder | Purpose |
| ------ | ------- |
| `.cursor/rules/` | Workspace-wide rules that always apply. This folder can exist inside any directory in the project—not just the root—and the rules apply from that directory downward. |

Rule files use the `.mdc` extension and are written in Markdown.

---
## 2. Discovering Relevant Rules (Generic Approach)

Agents have full read-access to the repository (and can write elsewhere), **but should never modify anything inside `.cursor/rules/`**.  Use the basic file-system commands or search utilities available in your environment to locate rule files:

1. **List the directory** – enumerate the contents of `.cursor/rules/`.
2. **Search for keywords** – look for filenames or file contents that match the topic at hand (e.g., “testing”, “database”, “security”).
3. **Open the candidate rule files** and keep their guidance in memory for the remainder of the task.

> Tip: If your environment supports parallel operations, use them to speed up directory scans and file reads.

---
## 3. Mandatory Pre-Task Checklist

Before writing code, answering a question, or running a command:

1. Identify all rules that might influence the task (search by topic or scan the directories).
2. Read them completely.
3. Apply them throughout the task—they are obligations, not suggestions.

---
## 4. Post-Task Responsibilities

If your work uncovers missing or outdated guidance:

1. **Do not** edit the rule files yourself.  Instead, flag the issue for human maintainers (e.g., by creating a ticket or leaving a comment in the development workflow).
2. Wherever possible, add or update tests to align with the existing rules.

---
## 5. Example Workflow (Language-Agnostic)

> Task: *“Add integration tests for feature Y.”*

1. Search `.cursor/rules/` for testing-related guidance (e.g., keywords like "test", "integration", "standards").
2. Read any matching rule files into context.
3. Follow those rules while implementing the tests.

---
### Final Note

When in doubt, **read the rules first**.  It saves time, avoids rework, and keeps your responses aligned with project expectations—regardless of the repository you are working in.