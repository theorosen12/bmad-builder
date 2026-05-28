#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Single source of truth for BMAD Module Manifest Spec v1.0.0 constants.

Transcribed verbatim from the authoritative marketplace tooling so the in-repo
Python tools (build-plugin-json.py, validate-plugin-json.py, discover-module.py)
stay byte-for-byte aligned with the Node gate:

  - RESERVED_CODES / CODE_REGEX / NAME_REGEX
        <- BMAD-METHOD/src/core-skills/bmad-module/scripts/lib/plugin-json.mjs
  - SPEC_VERSION / LATEST_KNOWN_BMAD / KNOWN_HOOK_EVENTS / KNOWN_OFFICIAL_SKILLS
        <- bmad-marketplace/scripts/validate-module.mjs

If the upstream sources change, refresh these constants and re-run the test
suites. The marketplace's validate-module.mjs remains the authoritative final
gate; this file exists only to mirror it without a Node dependency.
"""

import re

# Spec version this tooling targets (docs/spec.md §4, bmad.specVersion).
SPEC_VERSION = "1.0.0"

# Latest BMAD-METHOD release used for the W01 compatibility warning. Update
# when a new BMAD-METHOD ships so bmad.compatibility.bmadMethod warnings reflect
# current reality. (validate-module.mjs LATEST_KNOWN_BMAD)
LATEST_KNOWN_BMAD = "6.7.1"

# Reserved bmad.code values per spec §7.1. MUST match plugin-json.mjs and
# validate-module.mjs exactly.
RESERVED_CODES = frozenset(
    {
        # Official BMAD modules
        "core",
        "bmm",
        "bmb",
        "cis",
        "gds",
        "tea",
        "wds",
        "automator",
        # BMAD system directories
        "_config",
        "_memory",
        "custom",
        # Component directory names (collide with module layout)
        "agents",
        "hooks",
        "config",
        "commands",
        "skills",
    }
)

# Claude Code hook event names recognized by the loader. Unknown events are a
# warning (C12c), not an error — Anthropic may add new events.
# (validate-module.mjs KNOWN_HOOK_EVENTS)
KNOWN_HOOK_EVENTS = frozenset(
    {
        "SessionStart",
        "SessionEnd",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "Notification",
        "Stop",
        "SubagentStop",
        "PreCompact",
    }
)

# Representative official BMAD skill names for the W03 collision warning. Not
# exhaustive; refresh from BMAD-METHOD/src as needed.
# (validate-module.mjs KNOWN_OFFICIAL_SKILLS)
KNOWN_OFFICIAL_SKILLS = frozenset(
    {
        "bmad-help",
        "bmad-customize",
        "bmad-shard-doc",
        "bmad-index-docs",
        "bmad-distillator",
        "bmad-brainstorming",
        "bmad-advanced-elicitation",
        "bmad-party-mode",
        "bmad-document-project",
        "bmad-agent-analyst",
        "bmad-agent-architect",
        "bmad-agent-dev",
        "bmad-agent-pm",
        "bmad-agent-tech-writer",
        "bmad-agent-ux-designer",
        "bmad-agent-builder",
        "bmad-module-builder",
        "bmad-workflow-builder",
        "bmad-bmb-setup",
        "bmad-create-prd",
        "bmad-edit-prd",
        "bmad-validate-prd",
        "bmad-create-ux-design",
        "bmad-create-architecture",
        "bmad-create-epics-and-stories",
        "bmad-generate-project-context",
        "bmad-create-story",
        "bmad-dev-story",
        "bmad-code-review",
        "bmad-checkpoint-preview",
        "bmad-correct-course",
        "bmad-quick-dev",
        "bmad-retrospective",
        "bmad-sprint-planning",
        "bmad-sprint-status",
        "bmad-domain-research",
        "bmad-market-research",
        "bmad-technical-research",
        "bmad-prfaq",
        "bmad-product-brief",
        "bmad-tea",
        "bmad-teach-me-testing",
        "bmad-check-implementation-readiness",
    }
)

# Field-shape regexes. Raw strings mirror the JS literals; compiled patterns are
# provided for convenience. Length bounds (name 3-64, code via {1,31}) are
# enforced by callers, matching validate-module.mjs.
NAME_REGEX_SRC = r"^[a-z][a-z0-9-]+$"
CODE_REGEX_SRC = r"^[a-z][a-z0-9-]{1,31}$"
NAME_REGEX = re.compile(NAME_REGEX_SRC)
CODE_REGEX = re.compile(CODE_REGEX_SRC)

NAME_MIN_LEN = 3
NAME_MAX_LEN = 64

# Description length bounds (spec §4).
DESCRIPTION_MIN_LEN = 10
DESCRIPTION_MAX_LEN = 200


def is_reserved_code(code: str) -> bool:
    """True if `code` is reserved by the spec (§7.1)."""
    return code in RESERVED_CODES


def name_ok(name: str) -> bool:
    """True if `name` satisfies the spec §4 kebab-case + length rules."""
    return (
        isinstance(name, str)
        and bool(NAME_REGEX.match(name))
        and NAME_MIN_LEN <= len(name) <= NAME_MAX_LEN
    )


def code_ok(code: str) -> bool:
    """True if `code` satisfies the regex and is not reserved (§4, §7.1)."""
    return (
        isinstance(code, str)
        and bool(CODE_REGEX.match(code))
        and not is_reserved_code(code)
    )
