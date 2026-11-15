"""Scan a tree (and optionally the staged git diff) for credentials before a commit or push.

Usage: python3 scripts/secret_scan.py [path] [--staged]
Exit code 1 and a list of file:line hits (the matched value is masked) if anything looks like a secret.
Patterns: Anthropic keys, xAI keys, GitHub tokens, a real-looking value assigned to ANTHROPIC_API_KEY or
XAI_API_KEY, and box-local paths that should never reach the public repo.
"""
import pathlib, re, subprocess, sys

PATTERNS = {
    "anthropic-key": re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}"),
    "xai-key": re.compile(r"xai-[A-Za-z0-9]{20,}"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"),
    "key-assignment": re.compile(r"(?:ANTHROPIC|XAI)_API_KEY\s*=\s*['\"]?(?!your|\$|<|\.\.\.)[A-Za-z0-9_\-]{12,}"),
    "box-path": re.compile(r"/home/box|\.secrets/"),
}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"}


def scan_text(name, text):
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for kind, rx in PATTERNS.items():
            if kind == "box-path" and name.endswith(".gitignore"):
                continue  # listing the secrets folder is the point of .gitignore
            if rx.search(line):
                hits.append(f"{name}:{n}: {kind}")
    return hits


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = pathlib.Path(args[0] if args else ".")
    hits = []
    for p in root.rglob("*"):
        if p.is_file() and not (set(p.relative_to(root).parts) & SKIP_DIRS) and p.name != "secret_scan.py":
            try:
                hits += scan_text(str(p.relative_to(root)), p.read_text(errors="ignore"))
            except OSError:
                pass
    if "--staged" in sys.argv:
        diff = subprocess.run(["git", "-C", str(root), "diff", "--cached", "-U0"], capture_output=True, text=True).stdout
        added = "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")
                          and "PATTERNS" not in l and "re.compile" not in l)
        hits += scan_text("<staged diff>", added)
    print("\n".join(hits) if hits else "secret scan: clean")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
