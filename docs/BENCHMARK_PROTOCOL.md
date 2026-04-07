# Benchmark Protocol

This document defines the benchmark rules for evaluating the Lorentz Prime Predictor against practical closed-form nth-prime comparators. Its purpose is to support bounded claims from declared evidence, not flattering tables.

## Evaluated Objects

Every benchmark must declare which estimand it measures:

- `lpp_seed`, the closed-form integer seed
- `lpp_refined_predictor`, the deterministic prime output obtained from that seed

These are separate estimands. Seed results may not be summarized as refined results, and refined results may not be used as evidence for closed-form superiority.

## Governing Invariants

Every benchmark in this repository must satisfy the following invariants:

1. the evaluated claim is stated before metrics are summarized
2. seed and refined results are reported separately
3. evaluation sets are deterministic
4. held-out sets are not used for parameter tuning
5. exact ground truth sources are declared per run
6. every comparator has a concrete implementation and a cited source
7. every run emits raw per-point artifacts and an environment manifest
8. summary language does not claim more than the measured predicate supports
9. practicality claims require declared cost measurements
10. repeated runs in the same pinned environment must reproduce identical non-timing artifacts

## Comparator Set

The minimum literature comparison set is:

- first-order PNT inversion: $n \log n$
- two-term PNT correction: $n(\log n + \log\log n - 1)$
- Cipolla through the $1/\log n$ term
- Cipolla through the $1/\log^2 n$ term
- inverse logarithmic integral seed: $li^{-1}(n)$
- at least one modern explicit practical comparator from Axler or Dusart, with exact source citation and validity regime declared before evaluation

If a cited Axler- or Dusart-derived object is a bound rather than a point estimate, it must be reported in a separate bound-validity table and not folded into seed ppm rankings.

## Oracle Rules

Each benchmark run must declare one exact ground-truth strategy for $p_n$ and, if rank error is reported, one exact ground-truth strategy for $\pi(x)$.

The repository uses three provenance classes for label sources:

- `published exact`: published external exact sources such as OEIS
- `reproducible exact`: declared exact local generation with committed artifacts and deterministic reproduction steps
- `local continuation`: local non-published continuation labels that are not claimed as published exact ground truth

Acceptable exact ground-truth sources are:

- a declared external exact dataset with recorded provenance and checksum
- a declared local implementation based on a cited exact algorithm or library, only when that implementation is intentionally part of the active workflow for the run

The report for each run must state:

- the ground-truth source name
- the provenance class
- the implementation or dataset version
- the numerical horizon supported by that source in the run

If exact $\pi(x)$ is unavailable beyond the declared horizon, rank error must be omitted beyond that horizon rather than approximated.

## Benchmark Families

The suite should contain at least six deterministic families.

### Contract Grid

A sparse exact grid used to verify that implementations reproduce expected results at known scales.

The current shipped contract-grid horizon is

$$ n = 10^0,\dots,10^{24}. $$

### Held-Out Off-Lattice Grid

Deterministic checkpoints not used in parameter fitting, such as $2 \cdot 10^k, 3 \cdot 10^k, \ldots, 9 \cdot 10^k$. This is the core held-out scientific accuracy set.

The first implemented held-out harness in this repository covers the exact range

$$ 10^4 \leq n \leq 10^{12} $$

on the family

$$ n = m \cdot 10^k,\ m \in \{2,\dots,9\},\ k \in \{4,\dots,12\}. $$

### Boundary Windows

For each declared decade boundary $10^k$ in the tested regime, evaluate the contiguous window

$$ [10^k - 128,\ 10^k + 128] $$

when the lower endpoint is defined. These windows are deterministic and must be reported as their own family.

The first implemented held-out harness also covers the exact range

$$ [10^k - 128,\ 10^k + 128],\ k \in \{4,\dots,12\}. $$

### Tail Regime

Large exact checkpoints selected before evaluation and reported separately. A method that wins broadly but loses in the deeper asymptotic tail should say so plainly.

### Dense Deterministic Interval Family

For each declared interval $[a,b]$, evaluate the deterministic lattice

$$ n_j = \lfloor a + \frac{j(b-a)}{m-1} \rfloor,\ j = 0,1,\ldots,m-1 $$

with duplicates removed after construction. The repository default is $m = 1024$ per interval. Mean and median ppm claims should rely on this family or another deterministic family of comparable density, not on sparse landmark grids alone.

### Non-Decimal Landmarks

Include at least one non-decimal family to avoid a purely decimal evaluation surface. The repository default is the checkpoint family

$$ n = 2^k $$

over the declared tested regime.

## Row Metrics

At minimum, each row must report:

- exact $n$
- exact $p_n$
- predicted seed
- seed signed error
- seed absolute error
- seed relative error in ppm
- seed rank error $\Delta_{\pi}(n) = \pi(\widehat{p}_n) - n$, when exact $\pi(x)$ is available within the declared horizon
- refined prime output, if the benchmark includes refinement
- refined signed error, if the benchmark includes refinement
- refined absolute error, if the benchmark includes refinement
- refined relative error in ppm, if the benchmark includes refinement

## Aggregate Summaries

Aggregate summaries must include, for each estimand that is reported:

- mean signed error
- mean absolute error
- mean ppm
- median ppm
- max ppm
- RMS ppm
- sign ratio, defined as the fraction of positive signed errors
- mean absolute rank error, when rank error is available
- max absolute rank error, when rank error is available
- fraction of rows with zero rank error, when rank error is available
- worst-case rows
- separate summaries by benchmark family and by regime

## Calibration and Sensitivity Rules

If any constants are calibrated, the calibration surface must be declared explicitly and frozen before held-out evaluation.

Every report must distinguish between:

- calibration-set performance
- held-out performance

The held-out tables are the decisive tables for scientific comparison.

If any constants are calibrated, the held-out report must also include one-at-a-time sensitivity tables for each calibrated constant at:

- $-10\%$
- $+10\%$

with all other constants fixed.

## Refinement Rules

If refined predictors are compared, the refinement rule must be shared across predictors unless the goal is explicitly to compare complete predictor stacks.

That means the same:

- forward prime search rule
- primality predicate
- stopping rule

If the benchmark is about seed quality alone, no refinement step may be folded into the reported seed metrics.

## Cost Rules

If a report makes any claim that a predictor is practical, fast, efficient, or operationally preferable, it must include a cost section.

That section must declare:

- hardware and operating-system environment
- software environment and numeric library versions
- number of evaluations timed
- separate batch wall-clock times for seed evaluation and for full refined evaluation
- the identical timing harness used for every comparator

Cost results may support practicality claims, but they do not substitute for accuracy results.

## Artifact Rules

Each benchmark run must emit:

- a raw per-point CSV with LF line endings
- a summary table artifact
- a reproducible description of the exact ground-truth source used in the run
- the exact comparator list used in the run
- the declared computational horizon for rank error
- an environment manifest sufficient to reproduce the run in the same software stack

If plots are generated, they must be tied directly to the raw artifact and labeled by estimand.

## Claim-Language Rules

The benchmark report may say that a result is supported only when the measured predicate is explicit.

Examples of supported language:

- "best mean ppm on the dense deterministic interval family"
- "best worst-case ppm on the declared tested range"
- "smaller rank error than comparator X on this protocol"
- "lower batch seed-evaluation time than comparator X on the declared timing harness"

Examples of unsupported language without stronger evidence:

- "best formula in the literature"
- "asymptotically superior"
- "universally more accurate"
- "practically best" without declared cost measurements

## Target Outcome

The goal is not to produce flattering tables. The goal is to produce results that remain persuasive to a skeptical technical reader who can see exactly what was compared, how it was measured, what numerical horizon was actually covered, and what claim the evidence supports.
