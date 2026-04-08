# Review Findings

This document records recent review findings for the repository, why they mattered, and how they were addressed in the current remediation pass.

## P1: Oracle tests still verified the removed `primecount` workflow

- Severity: `P1`
- Owner: repository maintenance
- Status: resolved on the current branch
- Affected files:
  - `tests/python/test_primecount_oracle_scripts.py`
  - `tests/python/test_off_lattice_benchmark.py`
- Symptom observed:
  - the default `pytest -q` path was red
  - the oracle tests still expected the old `primecount` execution flow even though the four oracle scripts are now hard-stop stubs
- Why it mattered:
  - the repository instructions ban `primecount`
  - the test suite was asserting a workflow the repository no longer supports
  - the default validation path failed before it could say anything useful about the shipped implementation
- Evidence:
  - `pytest -q` failed during collection and execution on the stale oracle tests
  - the four scripts now raise a fixed ban message instead of exposing subprocess or manifest helpers
- Remediation:
  - rewrote the oracle-script tests around the current stub contract
  - removed duplicate oracle tests from the off-lattice benchmark test module
  - verified the scripts fail fast through subprocess execution by file path and emit the stable leading ban message

## P2: Generated artifact links were machine-local

- Severity: `P2`
- Owner: repository maintenance
- Status: resolved on the current branch
- Affected files:
  - `scripts/probe_cipolla_repacked.py`
  - `scripts/probe_nonheuristic_complexity_ladder.py`
  - benchmark and documentation Markdown that contained `/Users/velocityworks/...` repo-self links
- Symptom observed:
  - generated and committed Markdown linked to one local filesystem path instead of the repository layout
- Why it mattered:
  - links broke on GitHub and in any other clone
  - regenerating benchmark notes would keep reintroducing non-portable paths
- Evidence:
  - repo search found repo-self absolute links in generated probe READMEs and hand-written reference docs
- Remediation:
  - changed the affected generators to emit repo-relative Markdown links
  - patched the committed Markdown artifacts that already contained repo-self absolute links
  - preserved intentional absolute references to the archived Z5D reference outside this repository

## P3: Core predictor used a deprecated GMPY2 context API

- Severity: `P3`
- Owner: repository maintenance
- Status: resolved on the current branch
- Affected files:
  - `src/python/lpp/predictor.py`
  - `tests/python/test_lpp.py`
- Symptom observed:
  - the shipping predictor path emitted a `DeprecationWarning` because it still used `gp.local_context`
- Why it mattered:
  - the warning fired on passing test runs
  - future GMPY2 updates could break the shipping predictor path before benchmark code noticed
- Evidence:
  - direct test runs reported `local_context() is deprecated, use context(get_context()) instead.`
- Remediation:
  - replaced the deprecated context manager with `gp.context(gp.get_context(), precision=precision)`
  - kept precision selection, constants, rounding, and seed assembly unchanged
  - added a regression test that exercises `lpp_seed` and fails if that local deprecation warning returns
