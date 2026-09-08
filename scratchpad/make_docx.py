"""Resolve \ref/\eqref from the MAKE build's .aux so the DOCX has real numbers."""
import re, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
base = r"C:\Users\AndriyBilous\Documents\GitHub\tokenguard\research\out"
BS = chr(92)
tex = open(os.path.join(base, "blackwell-paper-make.tex"), encoding="utf-8").read()
aux = open(os.path.join(base, "blackwell-paper-make.aux"), encoding="utf-8").read()
labels = dict(re.findall(re.escape(BS) + r"newlabel\{([^}]+)\}\{\{([^}]+)\}", aux))
tex = re.sub(re.escape(BS) + r"eqref\{([^}]+)\}", lambda m: "(" + labels.get(m.group(1), "?") + ")", tex)
tex = re.sub(re.escape(BS) + r"ref\{([^}]+)\}", lambda m: labels.get(m.group(1), "?"), tex)
out = os.path.join(base, "_make_docx_tmp.tex")
open(out, "w", encoding="utf-8").write(tex)
print("labels resolved:", len(labels))
