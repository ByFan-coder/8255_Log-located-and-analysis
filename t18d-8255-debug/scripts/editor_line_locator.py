"""Read-only locator: CRLF, LF and lone CR delimit editor physical lines."""
import argparse
import gzip
import io
import json
from pathlib import Path


def iter_editor_lines(path, encoding="utf-8-sig"):
    path = Path(path)
    with path.open("rb") as raw:
        compressed = raw.read(2) == b"\x1f\x8b"
        raw.seek(0)
        source = gzip.GzipFile(fileobj=raw) if compressed else raw
        # Universal newlines recognize only CRLF, CR and LF; no splitlines().
        with io.TextIOWrapper(source, encoding=encoding, errors="strict", newline=None) as text:
            for number, value in enumerate(text, 1):
                yield number, value[:-1] if value.endswith("\n") else value


def locate(path, *, needle=None, line=None, encoding="utf-8-sig", max_hits=20):
    results = []
    limited = False
    for number, value in iter_editor_lines(path, encoding):
        if (line is not None and number == line) or (needle is not None and needle in value):
            if len(results) == max_hits:
                limited = True
                break
            results.append({"editor_line": number, "text": value})
        if line is not None and number >= line:
            break
    return {
        "path": str(Path(path).resolve()),
        "counting": "1-based; CRLF=one newline; lone CR/LF=one; gzip counts decompressed text",
        "matches": results,
        "more_matches": limited,
    }


def positive(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="case-sensitive literal fragment within a physical line")
    group.add_argument("--line", type=positive, help="read a 1-based editor physical line")
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--max-hits", type=positive, default=20)
    args = parser.parse_args()
    if args.text is not None and (not args.text or "\n" in args.text or "\r" in args.text):
        parser.error("--text must be nonempty and confined to one physical line")
    try:
        result = locate(args.path, needle=args.text, line=args.line,
                        encoding=args.encoding, max_hits=args.max_hits)
    except (OSError, UnicodeError, LookupError, EOFError) as error:
        parser.exit(2, "Read failed; verify format/encoding: " + str(error) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
