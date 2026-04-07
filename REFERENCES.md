# References

This document records the primary citation targets for the Lorentz Prime Predictor repository. It exists so that later implementation, benchmark, and release documents cite a stable, declared reference set rather than ad hoc sources.

The list is intentionally narrow. It covers the main asymptotic backbone, the classical and modern nth-prime comparator literature, asymptotic inversion references relevant to inverse-logarithmic-integral comparators, and exact-oracle references relevant to future benchmark runs.

## Prime Number Theorem Foundations

- Jacques Hadamard, "Sur la distribution des zéros de la fonction $\zeta(s)$ et ses conséquences arithmétiques," *Bulletin de la Société Mathématique de France* 24 (1896), 199-220.
- Charles-Jean de la Vallée Poussin, "Recherches analytiques sur la théorie des nombres premiers," *Annales de la Société Scientifique de Bruxelles* 20 (1896), 183-256.
- Charles-Jean de la Vallée Poussin, "Sur la fonction $\zeta(s)$ de Riemann et le nombre des nombres premiers inférieurs à une limite donnée," *Mémoires couronnés et autres mémoires publiés par l'Académie royale des sciences, des lettres et des beaux-arts de Belgique* 59 (1899), 1-74.

These are the classical sources for the prime number theorem and its stronger error-term context.

## Classical $p_n$ Asymptotics and Expansions

- Michele Cipolla, "La determinazione assintotica dell' $n$-esimo numero primo," *Rendiconti della Accademia delle Scienze Fisiche e Matematiche di Napoli* 8 (1902), 132-166.
- Bruno Salvy, "Fast Computation of Some Asymptotic Functional Inverses," *Journal of Symbolic Computation* 17(3) (1994), 227-236. [DOI](https://doi.org/10.1006/jsco.1994.1014)
- L. Panaitopol, "A formula for $\pi(x)$ applied to a result of Koninck-Ivić," *Nieuw Archief voor Wiskunde* (5) 1 (2000), 55-56.

Cipolla is the classical nth-prime asymptotic source. Salvy and Panaitopol are the main inversion-era references relevant to explicit asymptotic manipulations and to later inverse-logarithmic-integral style comparators.

## Practical Explicit Bounds and Comparator Literature

- J. Barkley Rosser, "The $n$-th prime is greater than $n \log n$," *Proceedings of the London Mathematical Society* (2) 45 (1939), 21-44.
- J. Barkley Rosser and Lowell Schoenfeld, "Approximate Formulas for Some Functions of Prime Numbers," *Illinois Journal of Mathematics* 6 (1962), 64-94.
- Pierre Dusart, "Inégalités explicites pour $\psi(X)$, $\theta(X)$, $\pi(X)$ et les nombres premiers," *C. R. Math. Acad. Sci. Soc. R. Can.* 21 (1999), 53-59.
- Pierre Dusart, "The $k$-th prime is greater than $k(\ln k + \ln \ln k - 1)$ for $k \geq 2$," *Mathematics of Computation* 68 (1999), 411-415.
- Pierre Dusart, "Explicit estimates of some functions over primes," *Ramanujan Journal* 45 (2018), 227-251.
- Pierre Dusart, "Estimates of the $k$th prime under the Riemann hypothesis," *Ramanujan Journal* 47 (2018), 141-154.
- Christian Axler, "New Estimates for the $n$th Prime Number," *Journal of Integer Sequences* 22 (2019), Article 19.4.2. [Journal page](https://cs.uwaterloo.ca/journals/JIS/VOL22/Axler/axler17.html)

This is the main comparator spine for future benchmark tables. If the repository reports a modern explicit practical comparator, the exact comparator should cite one or more of these sources directly.

If the repository later implements a specific numerical scheme for the $\operatorname{li}^{-1}(n)$ comparator, that implementation should add its exact method citation in the benchmark artifact or implementation notes rather than assuming this baseline list is already specific enough.

## Exact Prime-Counting and Prime-Generation Oracles

- Jeffrey C. Lagarias, Victor S. Miller, and Andrew M. Odlyzko, "Computing $\pi(x)$: The Meissel-Lehmer Method," *Mathematics of Computation* 44(170) (1985), 537-560.
- Kim Walisch, `primecount`, official repository. [GitHub](https://github.com/kimwalisch/primecount)
- Kim Walisch, `primesieve`, official repository. [GitHub](https://github.com/kimwalisch/primesieve)

These references are relevant to exact benchmark oracles. Future benchmark runs must still declare the actual oracle implementation and version used. This file does not precommit the repository to a single oracle implementation.

## Use Rule

This repository should cite primary sources when stating mathematical formulas, validity regimes, or explicit inequalities. Secondary summaries may be useful for local orientation, but public documents should cite the primary item whenever one is already listed here.
