# This file is part of rudd.
#
# rudd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rudd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rudd.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from pyparsing import Group, Literal, StringEnd, StringStart, Word, ZeroOrMore
from pyparsing import printables, QuotedString


class Entry:
    def __init__(self, path, options):
        self.path = path
        self.options = options

    def __eq__(self, other):
        return self.path == other.path and self.options == other.options

    def __repr__(self):
        opts = []
        for o in self.options:
            opts.append(str(o))

        return "{} {{ {} }}".format(self.path, " ".join(opts))


class Option:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value

    def __repr__(self):
        return "{} {}".format(self.name, self.value)


def sanitize(path):
    return path.strip('"')


def remove_comments(s):
    res = []
    for l in s.splitlines():
        if not l.strip().startswith("#"):
            res.append(l)

    return "\n".join(res)


def parse(s):
    path = Word(printables) ^ QuotedString('"')
    option_name = Literal("exec") ^ Literal("include") ^ Literal("exclude")
    option_value = path
    option = Group(option_name + option_value)
    options_list = Group(ZeroOrMore(option))
    path_entry = Group(path + Literal("{") + \
                       options_list + \
                       Literal("}"))
    path_entries_list = ZeroOrMore(path_entry)
    config = StringStart() + path_entries_list + StringEnd()

    entries = []
    for e in config.parseString(remove_comments(s)):
        opts = []
        if len(e) == 4:
            for o in e[2]:
               opts.append(Option(o[0], sanitize(o[1])))
        entries.append(Entry(sanitize(e[0]), opts))

    return entries


def parse_file(path):
    with open(path, "r") as f:
        return parse(f.read())


class TestParse(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse(""), [])
        self.assertEqual(parse('"/foo bar" { }'),
                         [Entry("/foo bar", [])])
        self.assertEqual(parse("/foo { }"),
                         [Entry("/foo", [])])
        self.assertEqual(parse("/foo { include * }"),
                         [Entry("/foo", [Option("include", "*")])])
        self.assertEqual(parse("/foo { include * exclude bar }"),
                         [Entry("/foo", [Option("include", "*"),
                                         Option('exclude', 'bar')])])
        self.assertEqual(parse("/foo { include a } /bar { exclude b }"),
                         [Entry("/foo", [Option("include", "a")]),
                          Entry("/bar", [Option("exclude", "b")])])

    def test_ignore_comments(self):
        cfg = "/foo {}\n" \
              "# A comment\n" \
              "/bar {}\n"

        self.assertEqual(parse(cfg),
                         [Entry("/foo", []), Entry("/bar", [])])
