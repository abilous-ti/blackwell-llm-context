# Separation point n*: smallest n at which a stark pair (n/n vs 0/n) verifies under the mixture CS at alpha/2,
# per corpus alpha = eta/(2|D_clean|). Sequential verification can only save draws when nmax > n*.
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seq_replay import av_interval, cp_interval
ETA = 0.10
for name, Dclean in (("harness", 6), ("tokenguard", 5), ("incomparability", 3)):
    alpha = ETA / (2 * Dclean); a1 = alpha / 2
    nstar = next(n for n in range(4, 60) if av_interval(n, n, a1)[0] - av_interval(0, n, a1)[1] > 0)
    ncp = next(n for n in range(4, 60) if cp_interval(n, n, a1)[0] - cp_interval(0, n, a1)[1] > 0)
    print(f"{name:<16} alpha={alpha:.4f}  AV n*={nstar:>2}  CP n*={ncp:>2}  "
          f"L16={av_interval(16,16,a1)[0]-av_interval(0,16,a1)[1]:+.2f}  L24={av_interval(24,24,a1)[0]-av_interval(0,24,a1)[1]:+.2f}")
