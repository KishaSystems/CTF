#!/usr/bin/env python3
"""ORION CTF - a local Capture The Flag environment.

Usage:
    python ctf.py                      Interactive menu
    python ctf.py list [category]      List challenges
    python ctf.py show <id>            Show challenge details
    python ctf.py hint <id>            Reveal the next hint (costs points)
    python ctf.py submit <id> <flag>   Submit a flag
    python ctf.py score                Show your score
    python ctf.py serve <id>           Start a local web challenge
    python ctf.py reset [--yes]        Reset progress
"""

import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
CHAL_DIR = os.path.join(ROOT, "challenges")
STATE_DIR = os.path.join(ROOT, "state")
PROGRESS_FILE = os.path.join(STATE_DIR, "progress.json")

if os.name == "nt":
    os.system("")

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

CATEGORY_ORDER = ["Misc", "Crypto", "Forensics", "Web", "Reversing"]
CATEGORY_CODES = {
    "Misc": "36",
    "Crypto": "35",
    "Forensics": "34",
    "Web": "32",
    "Reversing": "33",
}


def paint(text, code):
    if not USE_COLOR:
        return text
    return "\033[{}m{}\033[0m".format(code, text)


def bold(text):
    return paint(text, "1")


def dim(text):
    return paint(text, "2")


def red(text):
    return paint(text, "31")


def green(text):
    return paint(text, "32")


def yellow(text):
    return paint(text, "33")


def cyan(text):
    return paint(text, "36")


def category_label(category):
    return paint(category, CATEGORY_CODES.get(category, "37"))


def ensure_built():
    marker = os.path.join(CHAL_DIR, "misc-welcome", "challenge.json")
    if os.path.isfile(marker):
        return
    print(yellow("Challenges are not built yet. Building them now..."))
    build_script = os.path.join(ROOT, "build.py")
    if not os.path.isfile(build_script):
        print(red("build.py not found; cannot build challenges."))
        sys.exit(1)
    result = subprocess.run([sys.executable, build_script], cwd=ROOT, check=False)
    if result.returncode != 0:
        print(red("Build failed. Run 'python build.py' to see the full error."))
        sys.exit(1)
    print(green("Challenges built."))


def load_challenges():
    if not os.path.isdir(CHAL_DIR):
        print(red("No challenges found. Run: python build.py"))
        sys.exit(1)

    challenges = []
    for name in sorted(os.listdir(CHAL_DIR)):
        json_path = os.path.join(CHAL_DIR, name, "challenge.json")
        if not os.path.isfile(json_path):
            continue
        with open(json_path, encoding="utf-8") as handle:
            challenge = json.load(handle)
        challenge["_dir"] = os.path.join(CHAL_DIR, name)
        challenges.append(challenge)

    if not challenges:
        print(red("No challenges found. Run: python build.py"))
        sys.exit(1)
    return challenges


def load_progress():
    if os.path.isfile(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, encoding="utf-8") as handle:
                data = json.load(handle)
            data.setdefault("solved", {})
            data.setdefault("hints", {})
            return data
        except (ValueError, OSError):
            pass
    return {"solved": {}, "hints": {}}


def save_progress(progress):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as handle:
        json.dump(progress, handle, indent=2)


def find_challenge(challenges, challenge_id):
    needle = challenge_id.strip().lower()
    if not needle:
        return None
    for challenge in challenges:
        if challenge["id"].lower() == needle:
            return challenge
    matches = [c for c in challenges if needle in c["id"].lower()]
    if len(matches) == 1:
        return matches[0]
    return None


def points_for(challenge, progress):
    solved = progress["solved"].get(challenge["id"])
    if solved:
        return solved.get("points", challenge["points"])
    base = challenge["points"]
    used = progress["hints"].get(challenge["id"], [])
    penalty = round(base * 0.1) * len(used)
    return max(base - penalty, 0)


def cmd_list(challenges, progress, category=None):
    groups = {}
    for challenge in challenges:
        if category and challenge["category"].lower() != category.lower():
            continue
        groups.setdefault(challenge["category"], []).append(challenge)

    total = sum(c["points"] for c in challenges)
    earned = sum(
        points_for(c, progress)
        for c in challenges
        if c["id"] in progress["solved"]
    )

    print()
    print(bold("  CHALLENGE                CATEGORY    PTS   STATUS"))
    print(dim("  " + "-" * 54))
    for name in CATEGORY_ORDER + [c for c in groups if c not in CATEGORY_ORDER]:
        if name not in groups:
            continue
        for challenge in groups[name]:
            solved = challenge["id"] in progress["solved"]
            status = green("SOLVED") if solved else dim("open")
            points = points_for(challenge, progress)
            points_text = str(points)
            if points != challenge["points"]:
                points_text += "*"
            padded_category = challenge["category"] + " " * (10 - len(challenge["category"]))
            print(
                "  {:<24} {} {:>4}  {}".format(
                    challenge["id"],
                    category_label(padded_category),
                    points_text,
                    status,
                )
            )
    print()
    print(
        "  {} / {} points   ({} / {} solved)".format(
            bold(str(earned)),
            total,
            len(progress["solved"]),
            len(challenges),
        )
    )
    print(dim("  * points reduced by revealed hints"))
    print()


def cmd_show(challenges, progress, challenge_id):
    challenge = find_challenge(challenges, challenge_id)
    if not challenge:
        print(red("No challenge matching '{}'.".format(challenge_id)))
        return

    points = points_for(challenge, progress)
    solved = challenge["id"] in progress["solved"]
    used = progress["hints"].get(challenge["id"], [])

    print()
    print(bold(challenge["name"]))
    print("  id         : {}".format(challenge["id"]))
    print("  category   : {}".format(category_label(challenge["category"])))
    if points != challenge["points"]:
        print("  points     : {} {}".format(points, dim("(base {})".format(challenge["points"]))))
    else:
        print("  points     : {}".format(points))
    print("  difficulty : {}".format(challenge["difficulty"]))
    print("  status     : {}".format(green("SOLVED") if solved else "open"))
    print()
    for line in challenge["description"].splitlines():
        print("  " + line)
    print()

    if challenge.get("files"):
        print(bold("  Files:"))
        for relative in challenge["files"]:
            print("    " + os.path.join(challenge["_dir"], relative))
        print()

    print(
        dim(
            "  Hints revealed: {}/{}  (python ctf.py hint {})".format(
                len(used), len(challenge["hints"]), challenge["id"]
            )
        )
    )
    print()


def cmd_hint(challenges, progress, challenge_id):
    challenge = find_challenge(challenges, challenge_id)
    if not challenge:
        print(red("No challenge matching '{}'.".format(challenge_id)))
        return

    used = progress["hints"].setdefault(challenge["id"], [])
    total_hints = len(challenge["hints"])
    if challenge["id"] in progress["solved"]:
        print(yellow("'{}' is already solved; hints are not needed.".format(challenge["id"])))
        return
    if len(used) >= total_hints:
        print(yellow("All hints have already been revealed."))
        for index, hint in enumerate(challenge["hints"], 1):
            print("  {}. {}".format(index, hint))
        return

    index = len(used)
    used.append(index)
    save_progress(progress)

    penalty = round(challenge["points"] * 0.1)
    print(
        yellow(
            "Hint {}/{} for '{}' (-{} points):".format(
                index + 1, total_hints, challenge["id"], penalty
            )
        )
    )
    print("  " + challenge["hints"][index])


def cmd_submit(challenges, progress, challenge_id, flag):
    challenge = find_challenge(challenges, challenge_id)
    if not challenge:
        print(red("No challenge matching '{}'.".format(challenge_id)))
        return

    if challenge["id"] in progress["solved"]:
        print(yellow("'{}' is already solved.".format(challenge["id"])))
        return

    digest = hashlib.sha256(flag.strip().encode()).hexdigest()
    if digest == challenge["flag_sha256"]:
        points = points_for(challenge, progress)
        progress["solved"][challenge["id"]] = {
            "points": points,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_progress(progress)
        print(green("Correct! +{} points. Flag accepted for '{}'.".format(points, challenge["id"])))
    else:
        print(red("Incorrect flag. Keep trying."))


def cmd_score(challenges, progress):
    total = sum(c["points"] for c in challenges)
    solved = [c for c in challenges if c["id"] in progress["solved"]]
    earned = sum(points_for(c, progress) for c in solved)
    percent = (earned / total * 100) if total else 0.0

    bar_width = 40
    filled = int(round(bar_width * percent / 100.0))
    bar = "#" * filled + "-" * (bar_width - filled)

    print()
    print(bold("  SCORE"))
    print("  [{}] {}/{} pts ({:.1f}%)".format(green(bar), earned, total, percent))
    print("  Solved {} of {} challenges.".format(len(solved), len(challenges)))
    print()
    for challenge in challenges:
        mark = green("[x]") if challenge["id"] in progress["solved"] else dim("[ ]")
        padded_category = challenge["category"] + " " * (10 - len(challenge["category"]))
        print(
            "   {} {:<24} {} {:>3} pts".format(
                mark, challenge["id"], category_label(padded_category), challenge["points"]
            )
        )
    print()


def cmd_serve(challenges, challenge_id):
    challenge = find_challenge(challenges, challenge_id)
    if not challenge:
        print(red("No challenge matching '{}'.".format(challenge_id)))
        return

    serve = challenge.get("serve")
    if not serve:
        print(red("'{}' is not a served challenge.".format(challenge["id"])))
        print("Its files are in: " + challenge["_dir"])
        return

    cwd = os.path.normpath(os.path.join(challenge["_dir"], serve.get("cwd", ".")))
    command = [sys.executable] + serve["args"]
    print(cyan("Starting: " + " ".join(command)))
    print(cyan("Working directory: " + cwd))
    print(dim("Press Ctrl+C to stop the server."))
    try:
        subprocess.run(command, cwd=cwd, check=False)
    except KeyboardInterrupt:
        print("\nStopped.")
    except FileNotFoundError as error:
        print(red("Failed to start: {}".format(error)))


def cmd_reset(progress, assume_yes=False):
    if not assume_yes:
        answer = input(yellow("Reset all progress? [y/N] ")).strip().lower()
        if answer not in ("y", "yes"):
            print("Cancelled.")
            return
    progress["solved"] = {}
    progress["hints"] = {}
    save_progress(progress)
    print(green("Progress reset."))


def interactive(challenges, progress):
    while True:
        print()
        print(bold("  ORION CTF"))
        print("  1) List challenges")
        print("  2) Show a challenge")
        print("  3) Submit a flag")
        print("  4) Show score")
        print("  5) Get a hint")
        print("  6) Serve a challenge")
        print("  7) Reset progress")
        print("  0) Exit")
        choice = input(cyan("  > ")).strip()

        if choice in ("0", "q", "quit", "exit"):
            print("Goodbye.")
            break
        if choice == "1":
            cmd_list(challenges, progress)
        elif choice == "2":
            cmd_show(challenges, progress, input("  challenge id: "))
        elif choice == "3":
            challenge_id = input("  challenge id: ")
            flag = input("  flag: ")
            cmd_submit(challenges, progress, challenge_id, flag)
        elif choice == "4":
            cmd_score(challenges, progress)
        elif choice == "5":
            cmd_hint(challenges, progress, input("  challenge id: "))
        elif choice == "6":
            cmd_serve(challenges, input("  challenge id: "))
        elif choice == "7":
            cmd_reset(progress)
        else:
            print(red("  Unknown option."))


def usage():
    print(
        """
Usage:
  python ctf.py                      Interactive menu
  python ctf.py list [category]      List challenges
  python ctf.py show <id>            Show challenge details
  python ctf.py hint <id>            Reveal the next hint (costs points)
  python ctf.py submit <id> <flag>   Submit a flag
  python ctf.py score                Show your score
  python ctf.py serve <id>           Start a local web challenge
  python ctf.py reset [--yes]        Reset progress
"""
    )


def main():
    ensure_built()
    challenges = load_challenges()
    progress = load_progress()
    args = sys.argv[1:]

    if not args:
        interactive(challenges, progress)
        return

    command = args[0].lower()
    if command == "list":
        cmd_list(challenges, progress, args[1] if len(args) > 1 else None)
    elif command == "show" and len(args) >= 2:
        cmd_show(challenges, progress, args[1])
    elif command == "hint" and len(args) >= 2:
        cmd_hint(challenges, progress, args[1])
    elif command == "submit" and len(args) >= 3:
        cmd_submit(challenges, progress, args[1], " ".join(args[2:]))
    elif command == "score":
        cmd_score(challenges, progress)
    elif command == "serve" and len(args) >= 2:
        cmd_serve(challenges, args[1])
    elif command == "reset":
        cmd_reset(progress, "--yes" in args)
    elif command in ("help", "-h", "--help"):
        usage()
    else:
        usage()


if __name__ == "__main__":
    main()
