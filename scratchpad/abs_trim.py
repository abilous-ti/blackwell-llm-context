import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:\Users\AndriyBilous\Documents\GitHub\tokenguard\research\out"
P = os.path.join(D, "blackwell-paper.tex")
NL, BS = chr(10), chr(92)
s = open(P, "rb").read().decode("utf-8").replace("\r\n", "\n")

ABS = NL.join([
r"Choosing what to put in a language model's prompt is usually done by scoring each candidate source",
r"with one number and keeping the top few. We argue this is the wrong abstraction. Two sources can be",
r"\emph{incomparable} in Blackwell's 1953 sense, and when they are, no per-source score, relevance or",
r"utility, can rank them correctly for every task. We test this by running each source through a",
r"battery of pass/fail tasks and comparing pass rates with exact confidence intervals, a",
r"distribution-free \emph{verification}. On six models from four vendors we verify ($\geq 90\%$",
r"confidence, both directions) that two hand-built sources are incomparable. On a designed trap, a",
r"lexical score, two dense retrievers and a cross-encoder all prefer the wrong source, while a",
r"listwise LLM reranker that reads the deciding detail gets it right, as the theory predicts. Adding",
r"a larger source can also hurt: pass rates fall from $100\%$ to $0\%$ on eleven of twelve cells,",
r"with controls ruling out length and position. The lesson is practical: treat context",
r"selection as a partial order and compare sources by a verified pass-rate test, not a relevance",
r"number. Scaling the implied selection rule to large corpora is the main open problem."])

i = s.index(r"\begin{abstract}"); j = s.index(r"\end{abstract}")
s = s[:i] + r"\begin{abstract}" + NL + ABS + NL + s[j:]
open(P, "w", encoding="utf-8", newline="\n").write(s)

tex = s[s.index(r"\begin{abstract}"): s.index(r"\end{abstract}")]
out, k = [], 0
while k < len(tex):
    ch = tex[k]
    if ch == BS:
        k += 1
        while k < len(tex) and tex[k].isalpha(): k += 1
        out.append(" ")
    elif ch in "{}$~%":
        out.append(" "); k += 1
    else:
        out.append(ch); k += 1
w = [x for x in "".join(out).split() if any(c.isalnum() for c in x)]
print("abstract words: %d  %s" % (len(w), "OK" if len(w) <= 200 else "STILL OVER"))
