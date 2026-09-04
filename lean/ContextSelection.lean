/-
  Machine-checked formalization of the two impossibility results of

    "Context selection as a partial order:
     A Blackwell framework and verified LLM evidence"

  Theorem 2 (thm:incomparable) : no query-INDEPENDENT scalar score ranks an
                                 incomparable pair correctly on all tasks.
  Proposition 3 (prop:trap-constrained) : no TOPICAL query-conditioned score
                                 ranks the trap task correctly.

  This file depends only on the Lean 4 core library (no Mathlib), so it can be
  checked with a bare `lean` binary.

  The order on the score codomain is supplied explicitly as a structure rather
  than taken from a typeclass hierarchy.  This is deliberate: it makes visible
  that the impossibility is driven by *totality* of the induced ranking alone,
  not by any special property of the reals.  Every scalar score in the excluded
  class (relevance, mutual information, V-usable information, perplexity gap,
  fixed-prior EIG) lands in a totally ordered codomain, hence is covered.
-/

namespace ContextSelection

universe u v w

variable {Source : Type u} {Task : Type v} {α : Type w}

/-- A total ("linear") relation on the score codomain.  Only totality is
    assumed; reflexivity is derived (`TotalPre.refl`). -/
structure TotalPre (α : Type w) where
  le    : α → α → Prop
  total : ∀ x y, le x y ∨ le y x

/-- Totality gives reflexivity for free. -/
theorem TotalPre.refl (O : TotalPre α) (x : α) : O.le x x :=
  (O.total x x).elim id id

/-
  Throughout, `Beats W W' T` means: source `W` strictly outperforms `W'` on
  task `T`.  In the paper this is instantiated by `V*` (optimal value) and,
  under the value-attainment assumption, by realized `PASS_M`.
-/

/-- A score ranks `W` strictly above `W'` when `W` is not `≤` `W'`. -/
def StrictAbove (O : TotalPre α) (s s' : α) : Prop := ¬ O.le s s'

/-- **Faithfulness of a query-independent score on a task.**  Every strict
    performance win on `T` must be reflected by a strict score gap.  Note the
    score `φ` does not depend on `T`: that is exactly query-independence. -/
def FaithfulOn (O : TotalPre α) (Beats : Source → Source → Task → Prop)
    (φ : Source → α) (T : Task) : Prop :=
  ∀ W W', Beats W W' T → StrictAbove O (φ W) (φ W')

/-- **Blackwell incomparability, in the form the theorem consumes.**  Each
    source strictly wins on some task; the two witnesses point opposite ways. -/
structure Incomparable (Beats : Source → Source → Task → Prop) (W₁ W₂ : Source) where
  Ta    : Task
  Tb    : Task
  wins₁ : Beats W₁ W₂ Ta
  wins₂ : Beats W₂ W₁ Tb

/-- **Theorem (C1): no query-independent scalar ranks incomparable sources.**

    For an incomparable pair `W₁, W₂` and *any* query-independent score
    `φ : Source → α` into *any* totally ordered codomain, `φ` fails to be
    faithful on at least one of the two witnessing tasks.

    The proof is the formal content of the informal argument: `φ` commits to a
    single ordered pair `(φ W₁, φ W₂)` once and for all, totality forces that
    pair into one of two orders, and each order is refuted by one witness. -/
theorem no_faithful_query_independent_score
    (O : TotalPre α) (Beats : Source → Source → Task → Prop)
    {W₁ W₂ : Source} (h : Incomparable Beats W₁ W₂) (φ : Source → α) :
    ¬ (FaithfulOn O Beats φ h.Ta ∧ FaithfulOn O Beats φ h.Tb) := by
  intro hf
  have h₁ : ¬ O.le (φ W₁) (φ W₂) := hf.1 W₁ W₂ h.wins₁
  have h₂ : ¬ O.le (φ W₂) (φ W₁) := hf.2 W₂ W₁ h.wins₂
  cases O.total (φ W₁) (φ W₂) with
  | inl hle => exact h₁ hle
  | inr hle => exact h₂ hle

/-- Contrapositive packaging: a score faithful everywhere cannot exist. -/
theorem no_globally_faithful_score
    (O : TotalPre α) (Beats : Source → Source → Task → Prop)
    {W₁ W₂ : Source} (h : Incomparable Beats W₁ W₂) (φ : Source → α)
    (hall : ∀ T : Task, FaithfulOn O Beats φ T) : False :=
  no_faithful_query_independent_score O Beats h φ ⟨hall h.Ta, hall h.Tb⟩

/-! ### Query-conditioned scores: the topicality boundary -/

/-- **Faithfulness of a query-conditioned score on a task.**  Here the score
    may depend on the task, so `Theorem no_faithful_query_independent_score`
    does not apply; a separate hypothesis (topicality) is needed. -/
def FaithfulOnQ (O : TotalPre α) (Beats : Source → Source → Task → Prop)
    (ψ : Source → Task → α) (T : Task) : Prop :=
  ∀ W W', Beats W W' T → StrictAbove O (ψ W T) (ψ W' T)

/-- **Topicality.**  `ψ` is measurable with respect to a feature map `feat`:
    it sees a source only through its topical features, and therefore cannot
    read the verifier-decisive coordinate directly. -/
def Topical {β : Type _} (feat : Source → Task → β) (ψ : Source → Task → α) : Prop :=
  ∃ g : β → α, ∀ W T, ψ W T = g (feat W T)

/-- **Proposition (topicality boundary): a topical score mis-ranks the trap.**

    On the trap task `Tc` the two sources are topically indistinguishable
    (`feat W₁ Tc = feat W₂ Tc`), yet `W₁` strictly beats `W₂` there because
    `Tc`'s decisive coordinate is supplied by `W₁`.  Any topical `ψ` is then
    blind to the distinction, must score the two sources equally, and so cannot
    rank `W₁` strictly above `W₂`.

    This is the formal reason a reranker that *reads the decisive coordinate*
    escapes: such a reranker is not `Topical`, so the hypothesis fails and the
    impossibility does not bind it. -/
theorem topical_score_misranks_trap
    {β : Type _} (O : TotalPre α) (Beats : Source → Source → Task → Prop)
    (feat : Source → Task → β) (ψ : Source → Task → α)
    (htop : Topical feat ψ)
    {W₁ W₂ : Source} {Tc : Task}
    (hblind : feat W₁ Tc = feat W₂ Tc)
    (hbeats : Beats W₁ W₂ Tc) :
    ¬ FaithfulOnQ O Beats ψ Tc := by
  intro hf
  obtain ⟨g, hg⟩ := htop
  have hEq : ψ W₁ Tc = ψ W₂ Tc := by
    rw [hg W₁ Tc, hg W₂ Tc, hblind]
  have hstrict : ¬ O.le (ψ W₁ Tc) (ψ W₂ Tc) := hf W₁ W₂ hbeats
  exact hstrict (hEq ▸ O.refl (ψ W₂ Tc))

/-- Consequence: no topical score is faithful on every task, once a trap exists. -/
theorem no_faithful_topical_score
    {β : Type _} (O : TotalPre α) (Beats : Source → Source → Task → Prop)
    (feat : Source → Task → β) (ψ : Source → Task → α)
    (htop : Topical feat ψ)
    {W₁ W₂ : Source} {Tc : Task}
    (hblind : feat W₁ Tc = feat W₂ Tc)
    (hbeats : Beats W₁ W₂ Tc)
    (hall : ∀ T : Task, FaithfulOnQ O Beats ψ T) : False :=
  topical_score_misranks_trap O Beats feat ψ htop hblind hbeats (hall Tc)

end ContextSelection

/-! ### Non-vacuity: a concrete instance, and the axiom footprint

    The theorems above are universally quantified, so it must be shown that
    their hypotheses are satisfiable.  We build the paper's two-source,
    two-task configuration explicitly and apply both results to it.          -/

namespace Demo

/-- The paper's two context sources: the API-call contract and the
    wire-encoding invariant. -/
inductive Src | W1 | W2
  deriving DecidableEq

/-- Three tasks: the two carrying cells and the trap. -/
inductive Tsk | api | enc | trap
  deriving DecidableEq

/-- The measured double crossover: `W1` carries the API cell, `W2` carries the
    encoding cell, and `W1` also carries the trap. -/
def Beats : Src → Src → Tsk → Prop
  | .W1, .W2, .api  => True
  | .W2, .W1, .enc  => True
  | .W1, .W2, .trap => True
  | _,   _,   _     => False

/-- The crossover witnesses incomparability. -/
def inc : ContextSelection.Incomparable Beats Src.W1 Src.W2 :=
  { Ta := .api, Tb := .enc, wins₁ := trivial, wins₂ := trivial }

open ContextSelection

/-- **Instance of the main theorem.**  No query-independent score, into any
    totally ordered codomain, is faithful on both carrying cells. -/
theorem demo_no_scalar {α : Type} (O : TotalPre α) (φ : Src → α) :
    ¬ (FaithfulOn O Beats φ Tsk.api ∧ FaithfulOn O Beats φ Tsk.enc) :=
  no_faithful_query_independent_score O Beats inc φ

/-- A topical feature map that is blind to which source carries the decisive
    coordinate: on the trap it returns the same features for both sources. -/
def feat : Src → Tsk → Nat
  | _, .trap => 0
  | .W1, _   => 1
  | .W2, _   => 2

/-- **Instance of the topicality boundary.**  Any score factoring through
    `feat` mis-ranks the trap, where `W1` in fact wins. -/
theorem demo_topical_fails {α : Type} (O : TotalPre α) (ψ : Src → Tsk → α)
    (htop : Topical feat ψ) :
    ¬ FaithfulOnQ O Beats ψ Tsk.trap :=
  topical_score_misranks_trap (W₁ := Src.W1) (W₂ := Src.W2)
    O Beats feat ψ htop rfl trivial

end Demo

/-! ### Axiom footprint -/

#print axioms ContextSelection.no_faithful_query_independent_score
#print axioms ContextSelection.topical_score_misranks_trap
#print axioms Demo.demo_no_scalar
#print axioms Demo.demo_topical_fails
