---
bootstrapped_at: 2026-05-27T13:36:00Z
starter_id: django
starter_name: Django
project_name: analizator-wydatkow
language_family: python
package_manager: pdm
cwd_strategy: native-cwd
bootstrapper_confidence: verified
phase_3_status: ok
audit_command: pip-audit --format json
---

## Hand-off

```yaml
starter_id: django
package_manager: pdm
project_name: analizator-wydatkow
hints:
  language_family: python
  team_size: solo
  deployment_target: render
  ci_provider: github-actions
  ci_default_flow: auto-deploy-on-merge
  bootstrapper_confidence: verified
  path_taken: standard
  quality_override: false
  self_check_answers: null
  has_auth: true
  has_payments: false
  has_realtime: false
  has_ai: false
  has_background_jobs: false
```

### Why this stack

Django is the batteries-included Python web framework — it ships with authentication, ORM, migrations, and admin out of the box, matching the PRD's auth requirements (FR-001, FR-002) without additional setup. For a solo learner building a web app on a 3-week timeline targeting small scale, Django's convention-based structure and extensive documentation reduce setup friction and accelerate delivery. The built-in admin panel is a bonus for debugging and data inspection during development. Deploying to Render with GitHub Actions auto-deploy provides a straightforward CI/CD path with minimal configuration.

## Pre-scaffold verification

| Signal             | Value                              | Severity | Notes                              |
| ------------------ | ---------------------------------- | -------- | ---------------------------------- |
| npm package        | not run                            | —        | non-JS starter                     |
| GitHub repo        | not run                            | —        | docs_url is not a GitHub URL       |

No recency signal available for this starter.

## Scaffold log

**Resolved invocation**: `django-admin startproject analizator_wydatkow .`
**Strategy**: native-cwd
**Exit code**: 0
**Pre-flight files-to-touch**: manage.py, analizator_wydatkow/
**Files written by CLI**: 6
**Pre-existing files preserved**: context/, .agents/, .github/, skills-lock.json

## Post-scaffold audit

**Tool**: pip-audit --format json
**Status**: failed to run
**Reason**: pip-audit not installed in current environment

**Partial output (if any)**:

```
The term 'pip-audit' is not recognized as a name of a cmdlet, function, script file, or executable program.
```

**Recommended**: Install pip-audit (`pip install pip-audit`) and run manually to audit dependencies.

## Hints recorded but not acted on

| Hint                       | Value                              |
| -------------------------- | ---------------------------------- |
| bootstrapper_confidence    | verified                           |
| quality_override           | false                              |
| path_taken                 | standard                           |
| self_check_answers         | null                               |
| team_size                  | solo                               |
| deployment_target          | render                             |
| ci_provider                | github-actions                     |
| ci_default_flow            | auto-deploy-on-merge               |
| has_auth                   | true                               |
| has_payments               | false                              |
| has_realtime               | false                              |
| has_ai                     | false                              |
| has_background_jobs        | false                              |

## Next steps

Next: a future skill will set up agent context (CLAUDE.md, AGENTS.md). For now, your project is scaffolded and verified — happy hacking.

Useful manual steps in the meantime:
- `git init` (if you have not already) to start your own repo history.
- Review any `.scaffold` siblings the conflict policy created and decide which version of each file to keep.
- Address audit findings per your project's risk tolerance — the full breakdown is in this log.
- Since you chose pdm as your package manager, run `pdm init` and `pdm add django` to set up dependency management.
