#!/usr/bin/env python3
"""
Replace legacy \hline uses with booktabs \midrule and fix caption/label ordering
in LaTeX files under docs/reports/latex.

Run this from the repo root or directly. Creates .bak files for changed files.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'reports' / 'latex'

def process_file(path: Path):
    text = path.read_text(encoding='utf-8')
    orig = text

    # Remove temporary mapping in main.tex
    if path.name == 'main.tex':
        text = re.sub(r"\\let\\Oldhline\\hline\s*", '', text)
        text = re.sub(r"\\renewcommand\{\\hline\}\{\\midrule\}\s*", '', text)

    # Replace \hline with \midrule (booktabs)
    text = text.replace('\\hline', '\\midrule')

    # Fix label before caption inside figure/table environments
    def fix_env(match):
        env = match.group(0)
        # find first \label and first \caption
        lab_m = re.search(r"\\label\{[^}]+\}", env)
        cap_m = re.search(r"\\caption\s*\{", env)
        if lab_m and cap_m and lab_m.start() < cap_m.start():
            # move label to immediately after caption block
            label = lab_m.group(0)
            env_wo_label = env[:lab_m.start()] + env[lab_m.end():]
            # find end of caption (closing brace) starting at cap_m.start()
            cap_start = cap_m.start()
            # naive find matching brace for caption
            i = cap_start + len(cap_m.group(0))
            depth = 1
            while i < len(env_wo_label) and depth > 0:
                if env_wo_label[i] == '{':
                    depth += 1
                elif env_wo_label[i] == '}':
                    depth -= 1
                i += 1
            # insert label after caption end
            new_env = env_wo_label[:i] + '\\n' + label + env_wo_label[i:]
            return new_env
        return env

    env_re = re.compile(r"\\begin\{(?:figure|table)\}.*?\\end\{(?:figure|table)\}", re.DOTALL)
    text = env_re.sub(fix_env, text)

    if text != orig:
        bak = path.with_suffix(path.suffix + '.bak')
        bak.write_text(orig, encoding='utf-8')
        path.write_text(text, encoding='utf-8')
        print(f"Modified: {path.relative_to(ROOT.parent.parent)}")

def main():
    if not ROOT.exists():
        print(f"Root not found: {ROOT}")
        return
    for p in ROOT.rglob('*.tex'):
        process_file(p)

if __name__ == '__main__':
    main()
