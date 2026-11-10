"""Build the Stungeon German question bank (Das Leben B1, Einheiten 1-3).

Run:  python build.py  -> writes ../data/questions_german_b1.json and a review CSV.
Distractors are picked with a fixed random seed so the output is reproducible;
the game should still shuffle the answer order every time a question is shown.
"""
import csv, json, random, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from vocab import NOUNS, OTHERS
from grammar import GRAMMAR

random.seed(42)
OUT = Path(__file__).parent.parent / "data"   # questions/data/
OUT.mkdir(exist_ok=True)

STOP = {"to", "the", "a", "an", "of", "and", "or", "on", "in", "for", "with", "be", "(on", "stage)"}

def tokens(text):
    return {t for t in re.findall(r"[a-zA-Z]+", text.lower()) if len(t) > 3 and t not in STOP}

def pick_distractors(correct, pool, key, n=3):
    """Pick n distractors whose English meaning doesn't overlap with the correct one."""
    ct = tokens(correct["en"])
    cands = [p for p in pool if p is not correct and not (tokens(p["en"]) & ct)
             and key(p) != key(correct)]
    random.shuffle(cands)
    out, seen, used = [], {key(correct)}, set(ct)
    for c in cands:
        if key(c) not in seen and not (tokens(c["en"]) & used):
            out.append(c); seen.add(key(c)); used |= tokens(c["en"])
        if len(out) == n:
            break
    return out

# ---- normalise vocab into entries ----
entries = []
for e, rows in NOUNS.items():
    for art, word, pl, en, vi, src in rows:
        entries.append(dict(einheit=e, pos="noun", article=art, word=word, plural=pl,
                            de=f"{art} {word}", en=en, vi=vi, source=src))
for e, rows in OTHERS.items():
    for word, pos, en, vi, src in rows:
        entries.append(dict(einheit=e, pos=pos, word=word, de=word, en=en, vi=vi, source=src))

questions = []
counter = {}

def add(q):
    e, topic = q["einheit"], q["topic"]
    counter[(e, topic)] = counter.get((e, topic), 0) + 1
    q = {"id": f"de-b1-e{e}-{topic}-{counter[(e, topic)]:03d}", "subject": "german", "level": "B1", **q}
    questions.append(q)

for ent in entries:
    e = ent["einheit"]
    same_pos = [x for x in entries if x["pos"] == ent["pos"] or
                (ent["pos"] != "noun" and x["pos"] != "noun")]
    pool = [x for x in same_pos if x["einheit"] == e] or same_pos
    if len(pool) < 6:
        pool = same_pos
    base = dict(einheit=e, source=ent["source"], word=ent["de"], meaning_en=ent["en"], meaning_vi=ent["vi"])
    info = ent["de"] + (f" (pl. die {ent['plural']})" if ent.get("plural") else "") + f" = {ent['en']}"

    # 1) German -> English (easy)
    d = pick_distractors(ent, pool, key=lambda x: x["en"])
    if len(d) == 3:
        add(dict(base, topic="vocabulary", difficulty="easy", type="multiple_choice",
                 question=f"What does \"{ent['de']}\" mean?",
                 choices=[ent["en"]] + [x["en"] for x in d], answer=ent["en"], explanation=info))
    # 2) English -> German (medium)
    d = pick_distractors(ent, pool, key=lambda x: x["de"])
    if len(d) == 3:
        add(dict(base, topic="vocabulary", difficulty="medium", type="multiple_choice",
                 question=f"How do you say \"{ent['en']}\" in German?",
                 choices=[ent["de"]] + [x["de"] for x in d], answer=ent["de"], explanation=info))
    # 3) English -> German typed (hard)
    accept = []
    if ent["pos"] == "noun":
        prompt = f"Type the German noun WITH its article: \"{ent['en']}\""
    else:
        prompt = f"Type the German word: \"{ent['en']}\""
        if ent["de"].startswith("sich "):
            accept.append(ent["de"][5:])
    add(dict(base, topic="vocabulary", difficulty="hard", type="typed",
             question=prompt, answer=ent["de"], accept=accept, explanation=info))

    if ent["pos"] == "noun":
        # 4) article (medium)
        add(dict(base, topic="articles", difficulty="medium", type="multiple_choice",
                 question=f"___ {ent['word']}  ({ent['en']})",
                 choices=["der", "die", "das"], answer=ent["article"], explanation=info))
        # 5) plural typed (hard)
        if ent["plural"]:
            same = ent["plural"] == ent["word"]
            add(dict(base, topic="plurals", difficulty="hard", type="typed",
                     question=f"Type the plural: {ent['de']}  →  die ___",
                     answer=ent["plural"], accept=[f"die {ent['plural']}"],
                     explanation=info + (" (same form in the plural)" if same else "")))

# multi-select article round per Einheit (hard): pick all feminine / neuter nouns
for e in NOUNS:
    nouns = [x for x in entries if x["pos"] == "noun" and x["einheit"] == e]
    for target, label in (("die", "feminine (die)"), ("das", "neuter (das)"), ("der", "masculine (der)")):
        for _ in range(3):
            right = random.sample([x for x in nouns if x["article"] == target], 2)
            wrong = random.sample([x for x in nouns if x["article"] != target], 3)
            opts = right + wrong
            random.shuffle(opts)
            add(dict(einheit=e, source="vokabeln+einheit_text", topic="articles", difficulty="hard",
                     type="multi_select", question=f"Select ALL {label} nouns.",
                     choices=[x["word"] for x in opts], answer=[x["word"] for x in right],
                     explanation="; ".join(x["de"] for x in opts)))

for g in GRAMMAR:
    add(dict(g, source="einheit_text_grammar"))

# ---- sanity checks ----
for q in questions:
    if q["type"] == "multiple_choice":
        assert q["answer"] in q["choices"], q["id"]
        assert len(set(q["choices"])) == len(q["choices"]), q["id"]
    if q["type"] == "multi_select":
        assert all(a in q["choices"] for a in q["answer"]), q["id"]
ids = [q["id"] for q in questions]
assert len(ids) == len(set(ids))

bank = {
    "subject": "german",
    "level": "B1",
    "material": "Das Leben B1, Einheiten 1-3 (developer materials)",
    "version": 1,
    "einheiten": {1: "Bildung (er)leben", 2: "Vorhang auf!", 3: "Miteinander – füreinander!"},
    "difficulty_damage": {"easy": 10, "medium": 25, "hard": 50},
    "questions": questions,
}
(OUT / "questions_german_b1.json").write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")

with open(OUT / "questions_german_b1_review.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "einheit", "topic", "difficulty", "type", "question", "choices", "answer",
                "also_accepted", "explanation", "source", "ok? (reviewer)", "notes"])
    for q in questions:
        ans = q["answer"] if isinstance(q["answer"], str) else " | ".join(q["answer"])
        w.writerow([q["id"], q["einheit"], q["topic"], q["difficulty"], q["type"], q["question"],
                    " | ".join(q.get("choices", [])), ans, " | ".join(q.get("accept", [])),
                    q["explanation"], q["source"], "", ""])

# ---- stats ----
from collections import Counter
print("total", len(questions))
print("by einheit", Counter(q["einheit"] for q in questions))
print("by topic", Counter((q["einheit"], q["topic"]) for q in questions))
print("by difficulty", Counter(q["difficulty"] for q in questions))
print("by type", Counter(q["type"] for q in questions))
print("vocab entries", Counter((x["einheit"], x["source"]) for x in entries))
