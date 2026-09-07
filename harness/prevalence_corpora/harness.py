# Corpus 1: this harness (the fixed-n pilot corpus), re-exported for the sequential driver.
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import measure_prevalence as _mp
ROOT = str(HERE)
MODULES = ["measure_blackwell.py", "probe_select.py"]
TASKS = _mp.TASKS
REF = _mp.REF
WRONG = _mp.WRONG
PRE_SOL = _mp.PRE.split(chr(10))[0]
