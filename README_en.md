English | [简体中文](README.md)

<div align="center">

# Agent Workflow Builder

**An agent-agnostic Skill for designing, running, auditing, and reusing business workflows: verifiable outcomes, controlled risk, and traceable evidence.**

[![Build status](https://github.com/async-artisan/workflow-builder/actions/workflows/validate.yml/badge.svg)](https://github.com/async-artisan/workflow-builder/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/async-artisan/workflow-builder?label=release)](https://github.com/async-artisan/workflow-builder/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)

![Agent Workflow Builder flow from design and trial runs to evidence validation and reuse](docs/images/workflow-overview.svg)

</div>

> Last updated: 2026-10-27 ｜ Current version: v0.1.2.

## Contents

- [Overview](#overview)
- [Core capabilities](#core-capabilities)
- [Quick start](#quick-start)
- [Requirements](#requirements)
- [Installation and integration](#installation-and-integration)
- [Common usage](#common-usage)
- [Project structure](#project-structure)
- [Evidence boundaries](#evidence-boundaries)
- [Development and regression](#development-and-regression)
- [FAQ](#faq)
- [Contributing and community](#contributing-and-community)
- [License](#license)

## Overview

`workflow-builder` helps agents turn recurring business tasks into executable, inspectable, recoverable, and reusable workflows. It is intended for users who need process design, real trial runs, human acceptance, failure recovery, outcome evaluation, or workflow audits.

The core uses Markdown, the open Agent Skills directory structure, and optional Python standard-library scripts. **It is not tied to Codex, Claude, WorkBuddy, or any specific model or platform.** Hosts without script execution can still use its SOP, risk-control, and acceptance methods.

## Core capabilities

- Route design, build, execution, and audit requests without forcing one-off tasks into workflows.
- Guide vague requests through discovery interviews, playback, and output-sample confirmation while letting clear requests skip the interview.
- Generate Agent Skills from parameterized SOP templates.
- Select platforms through a decision matrix and pluggable adapter contracts.
- Compose external tools, MCP, APIs, CLIs, and existing Skills with explicit fallback paths.
- Derive lifecycle status from run evidence, side-effect receipts, and recovery checks.
- Apply read-only, reversible-write, and restricted-write risk tiers with budget stops.
- Bind approvals and evaluations to a content-addressed `release_id` and detect dependency drift.
- Evaluate baselines, business oracles, acceptance thresholds, and cost per accepted outcome.
- Preserve human feedback, inspection evidence, signoff records, and knowledge-base maintenance procedures.

## Quick start

No third-party Python packages are required. Clone the repository and generate an independent Skill from the read-only synthetic example:

```bash
git clone https://github.com/async-artisan/workflow-builder.git
cd workflow-builder
python scripts/sop_to_skill.py examples/readonly-minutes/workflow.sop.md --check
python scripts/sop_to_skill.py examples/readonly-minutes/workflow.sop.md --output-dir build
```

Then inspect:

```text
build/readonly-minutes/SKILL.md
```

This only proves that the example SOP can be validated and converted. It does not prove installation, loading, or real business acceptance.

## Requirements

| Item | Requirement | When required |
| --- | --- | --- |
| Agent host | Markdown reading; progressive loading requires Agent Skills or an equivalent mechanism | Always |
| Python | 3.9+, standard library only | Generation, release binding, and validation tools |
| Node.js | 22.20+ | Installation through Skills CLI |
| Git | For cloning and source updates | Source installation |
| Operating system | A host-supported Windows, macOS, or Linux environment; CI currently runs on Ubuntu | Depends on host |

## Installation and integration

### Install through Skills CLI

Run this in a project that supports Skills CLI:

```bash
npx skills add async-artisan/workflow-builder
```

The repository has been verified to expose `workflow-builder` through this command. Follow the prompts to select target agents and installation scope. Node.js 22.20 or later is required. See the [Skills CLI documentation](https://github.com/vercel-labs/skills).

For cross-host installs, prefer the Release ZIP below; it contains only the fixed runtime file list. Skills CLI applies its own repository discovery and host security checks. If installing from the source repository triggers extra warnings, use the minimal package and verify its SHA-256 first. Host scanners differ, so the minimal package cannot guarantee that every platform will suppress warnings.

### Install from the Release ZIP

Download `workflow-builder-v0.1.2.zip` from [Releases](https://github.com/async-artisan/workflow-builder/releases), extract it, and place the `workflow-builder` directory in the appropriate Skills directory below. The install package contains only Skill instructions, references, templates, optional validation tools, and the license; it excludes examples, evaluations, tests, and build scripts. The release SHA-256 file checks download integrity, not publisher identity.

### Build a Codex / ChatGPT plugin package

The repository includes an Agent Plugins 1.0 manifest and build script. No MCP server is required:

```bash
python scripts/build_plugin.py --check
python scripts/build_plugin.py --format skill
python scripts/build_plugin.py
```

Use `--format skill` to build the direct install ZIP. By default, the generated `dist/agent-workflow-builder-v0.1.2-plugin.zip` contains `plugin.json` at its root and places the Skill under `skills/workflow-builder/`. Both formats use a fixed runtime file list and exclude development evaluations, tests, and examples. The builder rejects symlinks and ZIP entries outside the allowlist. Local checks validate package structure only; they do not establish host review approval or publisher identity.

### Hosts that support Agent Skills

For manual integration, copy, link, or import the `workflow-builder` directory from the Release ZIP into the host's Skills directory. Do not use the full development repository as an install package; its examples, evaluations, and tests are for maintenance and validation:

| Host | Example user-level path |
| --- | --- |
| Codex | `~/.codex/skills/workflow-builder/` |
| Claude Code | `~/.claude/skills/workflow-builder/` |
| WorkBuddy | `~/.workbuddy/skills/workflow-builder/` |

For other agents, use their Skill discovery or import mechanism. `agents/openai.yaml` is an optional OpenAI/Codex presentation adapter and can be ignored by other hosts.

### Hosts that only support Markdown instructions

Include `SKILL.md` in custom instructions, rules, or system prompts, and provide relevant `references/` content for the task. If linked resources cannot be loaded automatically, attach the required files explicitly.

### Troubleshooting integration

First ensure `SKILL.md` is at the root of the skill directory rather than nested inside an extra repository directory. Then check whether the host has rescanned its Skills. If automatic discovery is unsupported, provide `SKILL.md` explicitly.

## Common usage

### Invoke through natural language

```text
Use workflow-builder to turn this recurring business task into a verifiable, reusable workflow.
```

In Codex, use `$workflow-builder`. To request an audit:

```text
Use workflow-builder to audit whether this process closes the loop. Return evidence-backed findings.
```

For an unclear request, simply say that you want automation but do not know where to start. The Skill will ask about a concrete recurring task, then confirm the first version through playback and an output sample. See the [vague-to-MVP example](examples/discovery/vague-to-mvp.md) and [discovery interview guide](references/discovery-interview.md).

For external tools or other Skills, follow [tool and Skill capability composition](references/capability-composition.md) to reuse capabilities, verify calls, and design fallbacks. The [software testing composition example](examples/software-testing/capability-plan.md) shows how document, spreadsheet, browser, and reporting Skills can cooperate.

### Generate a Skill from an SOP

Copy `assets/sop.template.md`, fill in the business content, and run:

```bash
python scripts/sop_to_skill.py /path/to/example.sop.md --check
python scripts/sop_to_skill.py /path/to/example.sop.md --output-dir /path/to/skills
```

Replace `/path/to/` with the actual path. Parameters:

| Parameter | Meaning | Default |
| --- | --- | --- |
| `--check` | Validate the SOP without writing files | Off |
| `--output-dir` | Root directory for generated Skills | Required in generation mode |
| `--force` | Allow overwriting an existing generated file | Off |

See [standard SOP and Skill generation](references/sop-format.md).

### Bind a release and validate run evidence

These commands use repository examples directly:

```bash
python scripts/build_release.py examples/readonly-minutes/workflow.sop.md examples/readonly-minutes/input.md examples/readonly-minutes/expected.md evals/cases/readonly-minutes.json --base-dir . --output build/release.json
python scripts/build_release.py --check build/release.json --base-dir .
```

For an actual run, embed the generated `release` object in the run manifest and execute:

```bash
python scripts/validate_run.py /path/to/run.json --json
```

Replace `/path/to/run.json` with the completed manifest. Start from `assets/run-manifest.template.json`. The validator rejects inconsistent states such as unsupported completion, approvals bound to an older release, blind retries after unknown external outcomes, and budget overruns.

## Project structure

```text
workflow-builder/
├── SKILL.md
├── agents/openai.yaml          # Optional host adapter
├── assets/                    # SOP, run manifest, and signoff templates
├── references/                # Methods, evaluation, risk, release, and platform guides
├── scripts/                   # Generation, release binding, and evidence validation tools
├── evals/                     # Trigger tests and business evaluation cases
├── examples/                  # Synthetic end-to-end examples
├── tests/                     # Positive and negative regression tests
├── docs/images/               # README diagrams
└── .github/workflows/         # Automated validation
```

## Evidence boundaries

- A generated Skill is not necessarily installed, loaded, or runtime-validated.
- `validate_run.py` checks evidence relationships; it does not prove that evidence is authentic or that an approver is authorized.
- Synthetic fixtures validate tool behavior, not real business outcomes or cross-host compatibility.
- Reuse validation requires unseen inputs, an actual baseline, and a pre-frozen acceptance threshold.
- Silence is not approval, and agent-to-agent review is not human business acceptance.

## Development and regression

```bash
python scripts/check_repository.py
python -m unittest discover -s tests -v
```

GitHub Actions checks structure, internal links, JSON, Python syntax, SOP generation, and positive and negative tool cases. Cross-host triggering and real business outcomes require separate validation in the target environments.

## FAQ

### Is this a Codex-only Skill?

No. The core targets any agent that can read Markdown. Codex, Claude Code, and WorkBuddy are example hosts, and other hosts can ignore `agents/openai.yaml`.

### Can I use it without Python?

Yes. The SOP, platform adapter, risk-control, and acceptance methods remain usable. SOP generation, release binding, run-manifest validation, and automated tests require Python 3.9+.

### Does SOP validation prove that a workflow is reliable?

No. Validation only proves structural validity. Reliability also requires real inputs, business assertions, failure checks, human acceptance, and reruns with different inputs.

### Does a valid run manifest prove that all evidence is authentic?

No. The tool checks consistency between states and evidence. Original evidence, approval authority, and external system state still require direct verification.

### How do I upgrade an older source installation?

Back up customized SOPs, templates, and run records first. In a clean clone, run `git pull`, then run the development and regression commands. Rescan Skills or start a new session if the host caches them.

## Contributing and community

Use [GitHub Issues](https://github.com/async-artisan/workflow-builder/issues) to report problems, discuss requirements, or share real evaluation results. [Pull Requests](https://github.com/async-artisan/workflow-builder/pulls) are welcome. Run both development and regression commands before submitting, and add positive and negative tests when changing validation logic.

## License

This project is released under the [MIT License](LICENSE). Keep the original copyright and license notices when using, modifying, or redistributing it. The software is provided “as is,” without express or implied warranties.
