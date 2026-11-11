# ORION CTF - Writeups

Spoiler warning: this file contains every flag and solution. Try the
challenges first. Use `python ctf.py hint <id>` if you only need a nudge.

---

## misc-welcome (10 pts) - Welcome to the Game

`challenges/misc-welcome/readme.txt` contains a base64 blob.

```bash
python -c "import base64; print(base64.b64decode('Q1RGe3czbGMwbWVfdDBfdGgzX2c0bTN9').decode())"
```

Flag: `CTF{w3lc0me_t0_th3_g4m3}`

---

## crypto-caesar (50 pts) - Ancient Transmission

The text is a Caesar cipher with shift 7. Shift the letters back by 7 (or
try all 26 shifts).

```python
ct = "JAM{j43z4y_j1wo3y_1z_4uj13ua}"
for shift in range(26):
    pt = "".join(
        chr((ord(c) - 65 - shift) % 26 + 65) if c.isupper()
        else chr((ord(c) - 97 - shift) % 26 + 97) if c.islower()
        else c
        for c in ct
    )
    if pt.startswith("CTF{"):
        print(pt)
```

Flag: `CTF{c43s4r_c1ph3r_1s_4nc13nt}`

---

## crypto-xor (75 pts) - Single Byte Secrets

The ciphertext is hex in `secret.hex`. Brute force all 256 single-byte keys
and look for `CTF{`.

```python
data = bytes.fromhex(open("challenges/crypto-xor/secret.hex").read().strip())
for key in range(256):
    pt = bytes(b ^ key for b in data)
    if b"CTF{" in pt:
        print(key, pt.decode())
```

The key is `0x5A`.

Flag: `CTF{x0r_1s_n0t_s3cur3}`

---

## misc-layers (50 pts) - Three Layers Deep

Peel the layers in order: ROT13, hex, base64.

```python
import base64, codecs
text = open("challenges/misc-layers/layers.txt").read().strip()
text = codecs.encode(text, "rot_13")
text = bytes.fromhex(text).decode()
print(base64.b64decode(text).decode())
```

Flag: `CTF{l4y3r3d_3nc0d1ng}`

---

## misc-whitespace (100 pts) - Invisible Ink

Each line ends with a run of spaces and tabs. Space = 0, tab = 1, eight bits
per line, most significant bit first.

```python
lines = open("challenges/misc-whitespace/message.txt", encoding="utf-8").read().splitlines()
chars = []
for line in lines:
    trailer = line[len(line.rstrip(" \t")):]
    if not trailer:
        continue
    bits = "".join("0" if ch == " " else "1" for ch in trailer)
    chars.append(chr(int(bits, 2)))
print("".join(chars))
```

Flag: `CTF{wh1t3sp4c3_m4tt3rs}`

---

## forensics-png (100 pts) - Beyond the Pixels

The flag is appended after the PNG `IEND` chunk. `strings` finds it:

```bash
strings challenges/forensics-png/image.png
```

Or inspect the end of the file with a hex editor / `tail`. On Windows, a
Python one-liner works too:

```python
data = open("challenges/forensics-png/image.png", "rb").read()
print(data[data.rfind(b"IEND") + 8:].decode(errors="replace"))
```

Flag: `CTF{png_1s_jus7_4_c0nt41n3r}`

---

## forensics-zip (75 pts) - Archive Whispers

The flag is stored in the ZIP archive comment.

```bash
unzip -z challenges/forensics-zip/archive.zip
# or
7z l challenges/forensics-zip/archive.zip
# or
strings challenges/forensics-zip/archive.zip
```

Python works everywhere:

```python
import zipfile
print(zipfile.ZipFile("challenges/forensics-zip/archive.zip").comment.decode())
```

Flag: `CTF{z1p_c0mm3nt5_c4n_t4lk}`

---

## web-robots (75 pts) - Forbidden Paths

Start the site:

```bash
python ctf.py serve web-robots
```

Visit `http://localhost:8000/robots.txt`:

```
User-agent: *
Disallow: /s3cr3t/
```

Then open `http://localhost:8000/s3cr3t/admin.html`. The flag is in an HTML
comment.

Flag: `CTF{4lw4ys_r34d_r0b0ts_txt}`

---

## web-cookie (100 pts) - Trust Issues

Start the server:

```bash
python ctf.py serve web-cookie
```

The server sets `admin=false`. Request `/admin` with `admin=true`:

```bash
curl -b "admin=true" http://localhost:8000/admin
```

PowerShell equivalent:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/admin -Headers @{Cookie="admin=true"} | Select-Object -Expand Content
```

Or change the cookie in your browser dev tools (Application/Storage ->
Cookies) and reload `/admin`.

Flag: `CTF{c00k13s_4r3_n0t_s3ss10ns}`

---

## rev-license (125 pts) - Crack the License

`license_check.py` stores `_ENC`, where:

```
_ENC[i] = ord(flag[i]) XOR ((i * 7 + 3) & 0xFF)
```

XOR is its own inverse, so recover each character with the same expression:

```python
import importlib.util
spec = importlib.util.spec_from_file_location(
    "lc", "challenges/rev-license/license_check.py"
)
lc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lc)

flag = "".join(chr(value ^ ((i * 7 + 3) & 0xFF)) for i, value in enumerate(lc._ENC))
print(flag)
```

Flag: `CTF{r3v3rs1ng_1s_fun}`

---

## crypto-rsa (150 pts) - Tiny RSA

`rsa.json` has `n = 1022117`, `e = 65537`, and one ciphertext integer per
flag byte. Factor `n` by trial division, then decrypt each byte.

```python
import json

data = json.load(open("challenges/crypto-rsa/rsa.json"))
n, e, ciphertext = data["n"], data["e"], data["ciphertext"]

p = next(d for d in range(2, int(n ** 0.5) + 1) if n % d == 0)
q = n // p
phi = (p - 1) * (q - 1)
d = pow(e, -1, phi)

flag = "".join(chr(pow(c, d, n)) for c in ciphertext)
print(flag, "  p =", p, " q =", q)
```

Here `p = 1009`, `q = 1013`, `phi = 1020096`.

Flag: `CTF{sm4ll_pr1m3s_4r3_b4d}`

---

## Full flag list

```
CTF{w3lc0me_t0_th3_g4m3}
CTF{c43s4r_c1ph3r_1s_4nc13nt}
CTF{x0r_1s_n0t_s3cur3}
CTF{l4y3r3d_3nc0d1ng}
CTF{wh1t3sp4c3_m4tt3rs}
CTF{png_1s_jus7_4_c0nt41n3r}
CTF{z1p_c0mm3nt5_c4n_t4lk}
CTF{4lw4ys_r34d_r0b0ts_txt}
CTF{c00k13s_4r3_n0t_s3ss10ns}
CTF{r3v3rs1ng_1s_fun}
CTF{sm4ll_pr1m3s_4r3_b4d}
```
