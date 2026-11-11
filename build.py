#!/usr/bin/env python3
"""Build the ORION local CTF environment.

Run this once before playing:

    python build.py

This script creates the challenges/ directory, generates every artifact,
and writes a challenge.json (with a SHA-256 flag hash) for each challenge.
It never touches your saved progress in state/.
"""

import base64
import codecs
import hashlib
import json
import os
import struct
import zipfile
import zlib

ROOT = os.path.dirname(os.path.abspath(__file__))
CHAL_DIR = os.path.join(ROOT, "challenges")


def write_text(path, text):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_bytes(path, data):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)


# ---------------------------------------------------------------------------
# Challenge artifact builders
# ---------------------------------------------------------------------------

def build_welcome(path, flag):
    blob = base64.b64encode(flag.encode()).decode()
    text = (
        "Welcome, agent.\n\n"
        "This is your first assignment. The flag is hidden in this file,\n"
        "but it is not in plain sight. Decode the base64 blob below.\n\n"
        f"{blob}\n"
    )
    write_text(os.path.join(path, "readme.txt"), text)
    return ["readme.txt"]


def caesar_shift(text, shift):
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - ord("a") + shift) % 26 + ord("a")))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - ord("A") + shift) % 26 + ord("A")))
        else:
            out.append(ch)
    return "".join(out)


def build_caesar(path, flag):
    ciphertext = caesar_shift(flag, 7)
    text = (
        "Intercepted transmission (channel 7):\n\n"
        f"{ciphertext}\n\n"
        "The key was not recovered. Brute force is your friend.\n"
    )
    write_text(os.path.join(path, "ciphertext.txt"), text)
    return ["ciphertext.txt"]


def build_xor(path, flag):
    key = 0x5A
    data = bytes(byte ^ key for byte in flag.encode())
    write_text(os.path.join(path, "secret.hex"), data.hex() + "\n")
    return ["secret.hex"]


def build_layers(path, flag):
    layer1 = base64.b64encode(flag.encode()).decode()
    layer2 = layer1.encode().hex()
    layer3 = codecs.encode(layer2, "rot_13")
    write_text(os.path.join(path, "layers.txt"), layer3 + "\n")
    return ["layers.txt"]


DECOY_LINES = [
    "Meeting notes - Project ORION",
    "Attendees: A. Rao, J. Chen, M. Silva",
    "Action items:",
    "- Review the quarterly report",
    "- Update the onboarding docs",
    "- Schedule the security training",
    "The printer on floor 3 is broken again.",
    "Coffee machine cleaned on Tuesday.",
    "Remember to water the office plants.",
    "The quick brown fox jumps over the lazy dog.",
    "Pack my box with five dozen liquor jugs.",
    "Sphinx of black quartz, judge my vow.",
    "How vexingly quick daft zebras jump.",
    "The five boxing wizards jump quickly.",
    "Bright vixens jump; dozy fowl quack.",
    "Jackdaws love my big sphinx of quartz.",
    "We promptly judged antique ivory buckles.",
    "A very bad quack might jinx zippy fowls.",
    "Few quips galvanized the mock jury box.",
    "A large fawn jumped quickly over white zinc boxes.",
    "The public was amazed to view the quick brown fox.",
    "We are all in the gutter, but some of us look at stars.",
    "Do not go gentle into that good night.",
    "All that we see or seem is but a dream within a dream.",
    "Once upon a midnight dreary, while I pondered, weak and weary.",
    "It was the best of times, it was the worst of times.",
    "Call me Ishmael.",
    "Happy families are all alike.",
    "Many years later, as he faced the firing squad.",
    "The sky above the port was the color of television.",
    "End of notes.",
]


def build_whitespace(path, flag):
    encoded = []
    for ch in flag:
        bits = format(ord(ch), "08b")
        encoded.append("".join(" " if bit == "0" else "\t" for bit in bits))

    lines = []
    for index, line in enumerate(DECOY_LINES):
        trailer = encoded[index] if index < len(encoded) else ""
        lines.append(line + trailer)
    for index in range(len(DECOY_LINES), len(encoded)):
        lines.append("note " + str(index) + encoded[index])

    write_text(os.path.join(path, "message.txt"), "\n".join(lines) + "\n")
    return ["message.txt"]


def _png_chunk(chunk_type, data):
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def _make_png(width, height, rgb):
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b""
    for _ in range(height):
        raw += b"\x00" + bytes(rgb) * width
    idat = zlib.compress(raw)
    return (
        signature
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", idat)
        + _png_chunk(b"IEND", b"")
    )


def build_png(path, flag):
    png = _make_png(1, 1, (30, 144, 255))
    payload = ("\nFLAG: " + flag + "\n").encode()
    write_bytes(os.path.join(path, "image.png"), png + payload)
    return ["image.png"]


def build_zip(path, flag):
    archive = os.path.join(path, "archive.zip")
    os.makedirs(path, exist_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
        handle.writestr(
            "notes.txt",
            "Quarterly numbers are looking good.\nNothing to see here.\n",
        )
        handle.writestr(
            "todo.txt",
            "1. Buy coffee\n2. Fix printer\n3. Do not read the archive comment\n",
        )
        handle.comment = ("Recovered archive. " + flag).encode()
    return ["archive.zip"]


def build_web_robots(path, flag):
    site = os.path.join(path, "site")
    write_text(
        os.path.join(site, "index.html"),
        """<!DOCTYPE html>
<html><head><title>ORION Corp</title></head>
<body>
<h1>ORION Corp</h1>
<p>Building the future, one satellite at a time.</p>
<ul>
  <li><a href="about.html">About us</a></li>
  <li><a href="careers.html">Careers</a></li>
</ul>
</body></html>
""",
    )
    write_text(
        os.path.join(site, "about.html"),
        """<!DOCTYPE html>
<html><head><title>About - ORION Corp</title></head>
<body><h1>About</h1><p>Founded in 1999. We like space.</p></body></html>
""",
    )
    write_text(
        os.path.join(site, "careers.html"),
        """<!DOCTYPE html>
<html><head><title>Careers - ORION Corp</title></head>
<body><h1>Careers</h1><p>No open positions right now.</p></body></html>
""",
    )
    write_text(os.path.join(site, "robots.txt"), "User-agent: *\nDisallow: /s3cr3t/\n")
    write_text(
        os.path.join(site, "s3cr3t", "admin.html"),
        f"""<!DOCTYPE html>
<html><head><title>Admin</title></head>
<body>
<h1>Internal admin panel</h1>
<!-- TODO: remove this before deploying to production. Flag: {flag} -->
<p>Nothing to see here.</p>
</body></html>
""",
    )
    return [
        "site/index.html",
        "site/about.html",
        "site/careers.html",
        "site/robots.txt",
        "site/s3cr3t/admin.html",
    ]


def build_web_cookie(path, flag):
    template = '''#!/usr/bin/env python3
import http.server
import socketserver

FLAG = __FLAG__
PORT = 8000

PAGE = """<!DOCTYPE html>
<html><head><title>ORION Portal</title></head>
<body>
<h1>ORION Portal</h1>
<p>Welcome, guest. Your session cookie has been set.</p>
<p>Administrators can visit <a href="/admin">/admin</a>.</p>
</body></html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        cookie = self.headers.get("Cookie", "")
        if self.path.startswith("/admin"):
            if "admin=true" in cookie:
                self.send_response(200)
                body = "<html><body><h1>Admin panel</h1><p>Flag: " + FLAG + "</p></body></html>"
            else:
                self.send_response(403)
                body = "<html><body><h1>403 Forbidden</h1><p>Admins only.</p></body></html>"
        else:
            self.send_response(200)
            body = PAGE
        self.send_header("Set-Cookie", "admin=false; Path=/")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print("ORION Portal running at http://localhost:%d" % PORT)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nStopped.")
'''
    code = template.replace("__FLAG__", json.dumps(flag))
    write_text(os.path.join(path, "server.py"), code)
    return ["server.py"]


def build_license(path, flag):
    encoded = [ord(ch) ^ ((index * 7 + 3) & 0xFF) for index, ch in enumerate(flag)]
    template = '''#!/usr/bin/env python3
"""ORION license checker. Enter a valid key to activate."""

_ENC = __ENC__


def check(key):
    if len(key) != len(_ENC):
        return False
    for i, ch in enumerate(key):
        if (ord(ch) ^ ((i * 7 + 3) & 0xFF)) != _ENC[i]:
            return False
    return True


def main():
    key = input("License key: ").strip()
    if check(key):
        print("License valid. Welcome, operator.")
    else:
        print("Invalid license key.")


if __name__ == "__main__":
    main()
'''
    code = template.replace("__ENC__", repr(encoded))
    write_text(os.path.join(path, "license_check.py"), code)
    return ["license_check.py"]


def build_rsa(path, flag):
    p = 1009
    q = 1013
    n = p * q
    e = 65537
    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    ciphertext = [pow(byte, e, n) for byte in flag.encode()]
    data = {
        "n": n,
        "e": e,
        "ciphertext": ciphertext,
        "note": "Each byte of the flag was encrypted separately with RSA.",
    }
    write_text(os.path.join(path, "rsa.json"), json.dumps(data, indent=2) + "\n")
    return ["rsa.json"]


# ---------------------------------------------------------------------------
# Challenge definitions
# ---------------------------------------------------------------------------

CHALLENGES = [
    {
        "id": "misc-welcome",
        "name": "Welcome to the Game",
        "category": "Misc",
        "points": 10,
        "difficulty": "Easy",
        "flag": "CTF{w3lc0me_t0_th3_g4m3}",
        "description": (
            "Every journey starts somewhere. Open readme.txt and decode what you find."
        ),
        "hints": [
            "Base64 text often ends with '=' or '=='.",
            "Try: python -c \"import base64;print(base64.b64decode('PASTE_BLOB_HERE'))\"",
        ],
        "build": build_welcome,
    },
    {
        "id": "crypto-caesar",
        "name": "Ancient Transmission",
        "category": "Crypto",
        "points": 50,
        "difficulty": "Easy",
        "flag": "CTF{c43s4r_c1ph3r_1s_4nc13nt}",
        "description": (
            "An old transmission was recovered. The letters look shifted. "
            "Recover the flag from ciphertext.txt."
        ),
        "hints": [
            "Julius Caesar used a fixed shift of the alphabet.",
            "There are only 26 possible shifts. Try them all.",
        ],
        "build": build_caesar,
    },
    {
        "id": "crypto-xor",
        "name": "Single Byte Secrets",
        "category": "Crypto",
        "points": 75,
        "difficulty": "Easy",
        "flag": "CTF{x0r_1s_n0t_s3cur3}",
        "description": (
            "The secret was encrypted by XORing each byte with a single key byte. "
            "The hex-encoded ciphertext is in secret.hex."
        ),
        "hints": [
            "A single-byte XOR key has only 256 possibilities.",
            "Look for the plaintext that starts with 'CTF{'.",
        ],
        "build": build_xor,
    },
    {
        "id": "misc-layers",
        "name": "Three Layers Deep",
        "category": "Misc",
        "points": 50,
        "difficulty": "Easy",
        "flag": "CTF{l4y3r3d_3nc0d1ng}",
        "description": (
            "Three layers of encoding protect this message in layers.txt. "
            "Peel them in the right order: ROT13, then hex, then base64."
        ),
        "hints": [
            "Apply ROT13 first.",
            "After ROT13, the text is hexadecimal.",
        ],
        "build": build_layers,
    },
    {
        "id": "misc-whitespace",
        "name": "Invisible Ink",
        "category": "Misc",
        "points": 100,
        "difficulty": "Medium",
        "flag": "CTF{wh1t3sp4c3_m4tt3rs}",
        "description": (
            "message.txt looks like ordinary meeting notes, but the invisible "
            "characters at the end of each line tell a different story. "
            "Space = 0, tab = 1."
        ),
        "hints": [
            "Only the whitespace at the very end of each line matters.",
            "Each line encodes one 8-bit character, most significant bit first.",
        ],
        "build": build_whitespace,
    },
    {
        "id": "forensics-png",
        "name": "Beyond the Pixels",
        "category": "Forensics",
        "points": 100,
        "difficulty": "Medium",
        "flag": "CTF{png_1s_jus7_4_c0nt41n3r}",
        "description": (
            "image.png should be a plain 1x1 pixel, but something is hiding "
            "after the end of the PNG data. Find the flag."
        ),
        "hints": [
            "PNG files end with the IEND chunk.",
            "Try strings, a hex editor, or binwalk on image.png.",
        ],
        "build": build_png,
    },
    {
        "id": "forensics-zip",
        "name": "Archive Whispers",
        "category": "Forensics",
        "points": 75,
        "difficulty": "Easy",
        "flag": "CTF{z1p_c0mm3nt5_c4n_t4lk}",
        "description": (
            "A ZIP archive was recovered from a workstation. The files inside "
            "are boring, but the archive itself has something to say."
        ),
        "hints": [
            "ZIP archives can store a comment after the file entries.",
            "Try unzip -z archive.zip, 7z l archive.zip, or strings archive.zip.",
        ],
        "build": build_zip,
    },
    {
        "id": "web-robots",
        "name": "Forbidden Paths",
        "category": "Web",
        "points": 75,
        "difficulty": "Easy",
        "flag": "CTF{4lw4ys_r34d_r0b0ts_txt}",
        "description": (
            "ORION Corp's website is running locally. Robots are told where "
            "not to go. Maybe you should go there anyway. Start it with: "
            "python ctf.py serve web-robots"
        ),
        "hints": [
            "Check /robots.txt first.",
            "The Disallow path is a strong hint.",
        ],
        "build": build_web_robots,
        "serve": {"cwd": "site", "args": ["-m", "http.server", "8000", "--bind", "127.0.0.1"]},
    },
    {
        "id": "web-cookie",
        "name": "Trust Issues",
        "category": "Web",
        "points": 100,
        "difficulty": "Medium",
        "flag": "CTF{c00k13s_4r3_n0t_s3ss10ns}",
        "description": (
            "The ORION portal trusts a cookie a little too much. "
            "Start it with: python ctf.py serve web-cookie"
        ),
        "hints": [
            "Look at the Set-Cookie header the server sends.",
            "Try sending 'Cookie: admin=true' with curl, or edit the cookie in your browser dev tools.",
        ],
        "build": build_web_cookie,
        "serve": {"cwd": ".", "args": ["server.py"]},
    },
    {
        "id": "rev-license",
        "name": "Crack the License",
        "category": "Reversing",
        "points": 125,
        "difficulty": "Medium",
        "flag": "CTF{r3v3rs1ng_1s_fun}",
        "description": (
            "A license checker validates a secret key. Reverse the check in "
            "license_check.py to recover the key (which is the flag)."
        ),
        "hints": [
            "The transformation is reversible.",
            "For each character: encrypted = ord(char) XOR ((index*7+3) & 0xFF). Invert it.",
        ],
        "build": build_license,
    },
    {
        "id": "crypto-rsa",
        "name": "Tiny RSA",
        "category": "Crypto",
        "points": 150,
        "difficulty": "Hard",
        "flag": "CTF{sm4ll_pr1m3s_4r3_b4d}",
        "description": (
            "A tiny RSA implementation encrypted each byte of the flag "
            "separately. The public key and ciphertext are in rsa.json. "
            "Factor n, recover d, and decrypt."
        ),
        "hints": [
            "n is small enough to factor by trial division.",
            "phi = (p-1)*(q-1), d = inverse(e, phi), plaintext byte = pow(c, d, n).",
        ],
        "build": build_rsa,
    },
]


def main():
    os.makedirs(CHAL_DIR, exist_ok=True)
    total = 0
    for challenge in CHALLENGES:
        challenge_id = challenge["id"]
        path = os.path.join(CHAL_DIR, challenge_id)
        os.makedirs(path, exist_ok=True)

        files = challenge["build"](path, challenge["flag"]) or []

        metadata = {
            "id": challenge_id,
            "name": challenge["name"],
            "category": challenge["category"],
            "points": challenge["points"],
            "difficulty": challenge["difficulty"],
            "description": challenge["description"],
            "files": files,
            "hints": challenge["hints"],
            "flag_sha256": hashlib.sha256(challenge["flag"].encode()).hexdigest(),
            "flag_format": "CTF{...}",
        }
        if "serve" in challenge:
            metadata["serve"] = challenge["serve"]

        write_text(
            os.path.join(path, "challenge.json"),
            json.dumps(metadata, indent=2) + "\n",
        )

        total += challenge["points"]
        print(
            "[+] built {:<20} {:<11} {:>3} pts".format(
                challenge_id, challenge["category"], challenge["points"]
            )
        )

    print()
    print("Built {} challenges worth {} points.".format(len(CHALLENGES), total))
    print("Play with: python ctf.py")
    print()
    print("Note: this file contains the plaintext flags used to generate the")
    print("challenges. Avoid reading it if you want to solve them honestly.")


if __name__ == "__main__":
    main()
