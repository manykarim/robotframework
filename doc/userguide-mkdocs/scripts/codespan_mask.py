"""Shared inline-code-span masking for the RST→MkDocs conversion pipeline.

Under `.. default-role:: code` (roles.rst) a single-backtick `text` is literal
inline code. RST anonymous/named reference resolution must NOT run over such a
span's interior or across its boundary — otherwise an underscore-bearing token
(`number.__abs__()`, `__intro__`) is mis-read as a reference, or the resolver
straddles from one span's CLOSING backtick across the prose to the next span
and eats its leading underscore, e.g.::

    `**this is bold**` or `__this is bold__`
      ->  `**this is bold**[ or ](#-or-)this is bold__`

An opening-backtick lookbehind is NOT sufficient (a closing backtick may be
preceded by `*`, `>`, `)`, … which the lookbehind permits). The reliable fix is
to pair backticks strictly left-to-right (1st-2nd, 3rd-4th, …): a span whose
CLOSING backtick is followed by `_` is a genuine `text`_ / `text`__ reference
and is left intact for the reference passes; every other span is a code span and
is replaced with an inert Private-Use-Area sentinel (0xE010, outside the
0xE000-0xE005 role-placeholder range). Restore afterwards so nothing leaks.

Usage:
    masked, saved = mask_code_spans(text)
    ...run reference regexes on `masked`...
    text = restore_code_spans(masked, saved)
"""

import re

MASK = chr(0xE010)
_RESTORE_RE = re.compile(re.escape(MASK) + r'(\d+)' + re.escape(MASK))


def mask_code_spans(text: str):
    """Return (masked_text, saved_spans). Code spans become `<MASK><i><MASK>`;
    genuine `text`_ / `text`__ references (closing backtick followed by `_`) are
    left untouched."""
    saved = []
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '`':
            j = text.find('`', i + 1)
            if j == -1:
                # No closing backtick at all — leave this stray one untouched.
                out.append(ch)
                i += 1
                continue
            # Pair backticks strictly left-to-right, matching how the reference
            # regexes pair them (their `[^`]+` spans a newline too). Restricting a
            # pair to a single line would leave a multi-line reference's opening
            # backtick unpaired and then mis-read its closing backtick as an
            # opening one — masking the prose after it and desyncing everything
            # downstream (the ConfiguringExecution `<running.TestSuite_>` rows).
            span = text[i:j + 1]
            after = text[j + 1] if j + 1 < n else ''
            if after == '_':
                out.append(span)  # `text`_ / `text`__ reference — keep intact
            else:
                saved.append(span)
                out.append(f'{MASK}{len(saved) - 1}{MASK}')
            i = j + 1
        else:
            out.append(ch)
            i += 1
    return ''.join(out), saved


def restore_code_spans(text: str, saved) -> str:
    """Inverse of mask_code_spans()."""
    if not saved:
        return text
    return _RESTORE_RE.sub(lambda m: saved[int(m.group(1))], text)
