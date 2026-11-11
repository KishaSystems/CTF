#!/usr/bin/env python3
"""ORION license checker. Enter a valid key to activate."""

_ENC = [64, 94, 87, 99, 109, 21, 91, 7, 73, 49, 120, 62, 48, 1, 84, 31, 44, 28, 244, 230, 242]


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
