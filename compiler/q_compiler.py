#!/usr/bin/env python3
"""
q_compiler_stub.py
Developer stub for the q_compiler worker.
Usage:
    python q_compiler_stub.py <job_dir>

Produces:
 - tokens.json
 - ast.dot
 - semantic_report.json
 - optimization_log.json
 - EnhancedPaper.tex (and tries to compile to EnhancedPaper.pdf)
 - AnalysisReport.tex (and tries to compile to AnalysisReport.pdf)
 - progress.json (simple phase markers)
"""
import sys, os, json, time
from pathlib import Path
import subprocess

def write_progress(job_dir, phase, status, message=""):
    p = Path(job_dir) / "progress.json"
    try:
        cur = {}
        if p.exists():
            cur = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        cur = {}
    cur[phase] = {"status": status, "ts": int(time.time()), "message": message}
    p.write_text(json.dumps(cur, indent=2), encoding="utf-8")

def phase1_tokens(job_dir, input_text):
    write_progress(job_dir, "phase1", "running", "tokenizing")
    tokens = []
    lines = input_text.splitlines()
    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if not s:
            continue
        # simple heuristics
        if s.startswith("[HEADER]") or s.startswith("[/HEADER]") or s.startswith("[QUESTION_LIST]") or s.startswith("[/QUESTION_LIST]"):
            tok = "T_TAG"
        elif s.upper().startswith("SUBJECT:"):
            tok = "T_SUBJECT"
        elif s.upper().startswith("TOTAL_MARKS:"):
            tok = "T_TOTAL_MARKS"
        elif s.upper().startswith("Q_TEXT"):
            tok = "T_Q_TEXT"
        elif s.upper().startswith("Q_MARKS"):
            tok = "T_Q_MARKS"
        else:
            tok = "T_RAW"
        tokens.append({"token": tok, "value": s, "line": i})
    (Path(job_dir)/"tokens.json").write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    write_progress(job_dir, "phase1", "done", f"{len(tokens)} tokens")
    return tokens

def phase2_ast(job_dir, tokens):
    write_progress(job_dir, "phase2", "running", "building ast")
    # very small AST: root plus question nodes
    qnodes = []
    current_text = None
    current_marks = 0
    for t in tokens:
        if t["token"] == "T_Q_TEXT":
            current_text = t["value"].split(":",1)[1].strip().strip('"')
        if t["token"] == "T_Q_MARKS":
            try:
                current_marks = int(''.join([c for c in t["value"] if c.isdigit()]))
            except:
                current_marks = 0
        # when we have text+marks -> push node
        if current_text is not None:
            qnodes.append({"text": current_text, "marks": current_marks})
            current_text = None
            current_marks = 0

    # fallback: if no qnodes, create one sample from tokens
    if not qnodes:
        # combine raw lines into one question example
        raw = "\n".join([t["value"] for t in tokens if t["token"] in ("T_RAW","T_Q_TEXT")])
        qnodes = [{"text": raw[:800], "marks": 0}]

    # write ast.dot
    lines = ["digraph AST {", "  node [shape=record];", f'  root [label="{{Paper|stub}}"];']
    for i,q in enumerate(qnodes, start=1):
        safe = q["text"].replace('"','\\"').replace("\n","\\n")
        lines.append(f'  q{i} [label="{{Q{i}|Marks: {q["marks"]}\\n{safe[:120]}...}}"];')
        lines.append(f'  root -> q{i};')
    lines.append("}")
    (Path(job_dir)/"ast.dot").write_text("\n".join(lines), encoding="utf-8")
    write_progress(job_dir, "phase2", "done", f"{len(qnodes)} nodes")
    return qnodes

def phase3_semantic(job_dir, qnodes):
    write_progress(job_dir, "phase3", "running", "semantic analysis")
    # naive heuristics
    questions = []
    for q in qnodes:
        text = q.get("text","")
        marks = q.get("marks",0)
        # difficulty by simple rules
        dl = "Medium"
        tl = text.lower()
        if any(k in tl for k in ["design","create","construct","derive","prove"]):
            dl = "Hard"
        elif any(k in tl for k in ["explain","describe","compare","apply","solve"]):
            dl = "Medium"
        else:
            dl = "Easy" if marks < 5 else "Medium"
        est_time = max(1, int(marks / 1.5) + (5 if dl=="Hard" else 2 if dl=="Medium" else 0))
        syllabus_topic = "N/A"
        for tok in ["trees","sorting","graphs","stack","queue","grammar","compiler","parsing","chomsky"]:
            if tok in tl:
                syllabus_topic = tok.capitalize()
                break
        status_flag = 0 if syllabus_topic!="N/A" else 2
        questions.append({
            "text": text,
            "marks": marks,
            "difficulty": dl,
            "estimated_time": est_time,
            "syllabus_topic": syllabus_topic,
            "status_flag": status_flag
        })
    semantic = {
        "subject": "Stub Subject",
        "total_marks": sum(q["marks"] for q in questions),
        "total_time": sum(q["estimated_time"] for q in questions),
        "questions": questions
    }
    (Path(job_dir)/"semantic_report.json").write_text(json.dumps(semantic, indent=2), encoding="utf-8")
    write_progress(job_dir, "phase3", "done", f"{len(questions)} questions")
    return semantic

def phase45_opt(job_dir, semantic):
    write_progress(job_dir, "phase45", "running", "optimization")
    # simple empty log (no changes)
    log = [{"change":"NO_CHANGE","message":"stub"}]
    (Path(job_dir)/"optimization_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    write_progress(job_dir, "phase45", "done", "optimization complete")
    return log

def phase6_tex_and_pdf(job_dir, semantic):
    write_progress(job_dir, "phase6", "running", "generating latex")
    jobp = Path(job_dir)
    ep = jobp/"EnhancedPaper.tex"
    with open(ep, "w", encoding="utf-8") as f:
        f.write("\\documentclass{article}\n\\begin{document}\n")
        f.write("\\section*{Enhanced Paper - Stub}\n")
        for i,q in enumerate(semantic["questions"], start=1):
            safe = q["text"].replace("%","\\%")
            f.write(f"\\paragraph{{Q{i} ({q['marks']} marks)}} {safe}\n\n")
        f.write("\\end{document}\n")
    ar = jobp/"AnalysisReport.tex"
    with open(ar, "w", encoding="utf-8") as f:
        f.write("\\documentclass{article}\n\\begin{document}\n")
        f.write("\\section*{Analysis Report - Stub}\n")
        f.write(f"Total marks: {semantic.get('total_marks',0)}\\\\\n")
        for q in semantic["questions"]:
            f.write(f"{q['difficulty']} - {q['text'][:120].replace('%','\\%')} ({q['marks']} marks)\\\\\n")
        f.write("\\end{document}\n")
    # try to compile with pdflatex if present
    def try_pdflatex(texpath):
        try:
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory", str(jobp), str(texpath)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False
    try_pdflatex(ep)
    try_pdflatex(ar)
    write_progress(job_dir, "phase6", "done", "latex files written (pdf if pdflatex present)")
    return True

def main():
    if len(sys.argv) < 2:
        print("No input directory specified.")
        return
    job_dir = sys.argv[1]
    Path(job_dir).mkdir(parents=True, exist_ok=True)
    print("Stub q_compiler: processing", job_dir)
    # small delay to simulate processing
    time.sleep(0.5)
    # read input.qp if present, otherwise create a fallback
    input_p = Path(job_dir)/"input.qp"
    if input_p.exists():
        input_text = input_p.read_text(encoding="utf-8")
    else:
        input_text = "[HEADER]\nSUBJECT: \"Stub\"\n[/HEADER]\n[QUESTION_LIST]\n[QUESTION]\nQ_TEXT: \"Sample question\"\nQ_MARKS: 5\n[/QUESTION]\n[/QUESTION_LIST]\n"
    write_progress(job_dir, "started", "running", "stub started")
    tokens = phase1_tokens(job_dir, input_text)
    qnodes = phase2_ast(job_dir, tokens)
    semantic = phase3_semantic(job_dir, qnodes)
    phase45_opt(job_dir, semantic)
    phase6_tex_and_pdf(job_dir, semantic)
    write_progress(job_dir, "finished", "done", "stub complete")
    print("Stub finished. Artifacts written to", job_dir)

if __name__ == "__main__":
    main()
