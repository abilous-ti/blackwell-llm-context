"""Add the academic positions from the author table to the title block."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:\Users\AndriyBilous\Documents\GitHub\tokenguard\research\out"
P = os.path.join(D, "blackwell-paper.tex")
NL = chr(10)
s = open(P, "rb").read().decode("utf-8").replace("\r\n", "\n")

old = NL.join([
r"  \normalsize \texttt{andriy.bilous@uitware.com} (A.B.); \texttt{petro.y.pukach@lpnu.ua} (P.P.); \\",
r"  \normalsize \texttt{vasyl.v.lytvyn@lpnu.ua} (V.L.); \texttt{zoriana.l.rybchak@lpnu.ua} (Z.R.) \\[3pt]"])

new = NL.join([
r"  \normalsize P.P.: Dr.Sc., Professor, Director of the Institute;"
r" V.L.: Dr.Sc., Full Professor, Head of Department; \\",
r"  \normalsize Z.R.: PhD, Associate Professor \\[3pt]",
r"  \normalsize \texttt{andriy.bilous@uitware.com} (A.B.); \texttt{petro.y.pukach@lpnu.ua} (P.P.); \\",
r"  \normalsize \texttt{vasyl.v.lytvyn@lpnu.ua} (V.L.); \texttt{zoriana.l.rybchak@lpnu.ua} (Z.R.) \\[3pt]"])

assert s.count(old) == 1, s.count(old)
open(P, "w", encoding="utf-8", newline="\n").write(s.replace(old, new))
print("positions added to the title block")
