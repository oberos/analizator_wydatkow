---
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
---

## Why this stack

Django is the batteries-included Python web framework — it ships with authentication, ORM, migrations, and admin out of the box, matching the PRD's auth requirements (FR-001, FR-002) without additional setup. For a solo learner building a web app on a 3-week timeline targeting small scale, Django's convention-based structure and extensive documentation reduce setup friction and accelerate delivery. The built-in admin panel is a bonus for debugging and data inspection during development. Deploying to Render with GitHub Actions auto-deploy provides a straightforward CI/CD path with minimal configuration.
