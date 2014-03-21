#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import simplejson
import sys
from os import path

# The spec replaces most characters in the ISO-2022 C1 control code range
# (U+0080 through U+009F) with these characters, based on Windows 8-bit
# codepages.  This table is simply copy-pasted from the spec.
c1_replacements_table = u"""
0x00    U+FFFD  REPLACEMENT CHARACTER
0x80    U+20AC  EURO SIGN (€)
0x82    U+201A  SINGLE LOW-9 QUOTATION MARK (‚)
0x83    U+0192  LATIN SMALL LETTER F WITH HOOK (ƒ)
0x84    U+201E  DOUBLE LOW-9 QUOTATION MARK (&ldquor;)
0x85    U+2026  HORIZONTAL ELLIPSIS (&mldr;)
0x86    U+2020  DAGGER (†)
0x87    U+2021  DOUBLE DAGGER (‡)
0x88    U+02C6  MODIFIER LETTER CIRCUMFLEX ACCENT (ˆ)
0x89    U+2030  PER MILLE SIGN (‰)
0x8A    U+0160  LATIN CAPITAL LETTER S WITH CARON (Š)
0x8B    U+2039  SINGLE LEFT-POINTING ANGLE QUOTATION MARK (‹)
0x8C    U+0152  LATIN CAPITAL LIGATURE OE (Œ)
0x8E    U+017D  LATIN CAPITAL LETTER Z WITH CARON (&Zcaron;)
0x91    U+2018  LEFT SINGLE QUOTATION MARK (‘)
0x92    U+2019  RIGHT SINGLE QUOTATION MARK (&rsquor;)
0x93    U+201C  LEFT DOUBLE QUOTATION MARK (“)
0x94    U+201D  RIGHT DOUBLE QUOTATION MARK (”)
0x95    U+2022  BULLET (&bullet;)
0x96    U+2013  EN DASH (–)
0x97    U+2014  EM DASH (—)
0x98    U+02DC  SMALL TILDE (˜)
0x99    U+2122  TRADE MARK SIGN (™)
0x9A    U+0161  LATIN SMALL LETTER S WITH CARON (š)
0x9B    U+203A  SINGLE RIGHT-POINTING ANGLE QUOTATION MARK (›)
0x9C    U+0153  LATIN SMALL LIGATURE OE (œ)
0x9E    U+017E  LATIN SMALL LETTER Z WITH CARON (&zcaron;)
0x9F    U+0178  LATIN CAPITAL LETTER Y WITH DIAERESIS (Ÿ)
"""

def rust_char_literal(codepoint):
    return r"'\U%08x'" % (codepoint,)

def print_header():
    print "// THIS FILE IS AUTOGENERATED - DO NOT EDIT"
    print
    print "use phf::PhfMap;"

def print_c1_replacements():
    tbl = [None] * 32
    for ln in c1_replacements_table.splitlines():
        if not ln:
            continue
        parts = ln.split(None, 2)
        assert parts[0][:2] == '0x'
        assert parts[1][:2] == 'U+'

        ix = int(parts[0][2:], 16)
        if ix == 0:
            # NULL isn't in 0x80..0x9F.  It's handled by non-generated code.
            continue

        tbl[ix - 0x80] = int(parts[1][2:], 16)

    print "pub static c1_replacements: [Option<char>, ..32] = ["

    for t in tbl:
        if t is None:
            print "    None,"
        else:
            print "    Some(%s)," % (rust_char_literal(t),)

    print "];"

def print_entities():
    # from http://www.whatwg.org/specs/web-apps/current-work/multipage/entities.json
    src_dir = sys.argv[1]
    with file(path.join(src_dir, 'data/entities.json')) as f:
        json = simplejson.load(f)

    entities = {'': [0,0]}

    for k,v in json.iteritems():
        codepoints = v['codepoints']

        # Unused char slots get filled with \0
        assert all(c != 0 for c in codepoints)
        assert 0 < len(codepoints) <= 2
        if len(codepoints) == 1:
            codepoints += [0]

        assert k[0] == '&'
        entities[k[1:]] = codepoints

    keys = entities.keys()
    for k in keys:
        for n in xrange(1, len(k)):
            entities.setdefault(k[:n], [0,0])

    print "pub static named_entities: PhfMap<[char, ..2]> = phf_map!("

    for k in sorted(entities.iterkeys()):
        print "    \"%s\" => [%s]," % \
            (k, ', '.join(map(rust_char_literal, entities[k])))

    print ");"

print_header()
print
print_c1_replacements()
print
print_entities()
