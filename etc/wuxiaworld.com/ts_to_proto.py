#!/usr/bin/env python3
"""
Convert protobuf-ts generated TypeScript (``*.ts``) back into ``.proto`` files.

protobuf-ts embeds the full schema as runtime reflection data
(``super("pkg.Msg", [{ no: 1, name: "x", kind: "scalar", T: 5 }, ...])``),
``@generated`` doc comments and ``import`` lines.  This tool reads exactly
those, so nothing is guessed:

* nesting comes from the real message names, not from splitting ``A_B`` on ``_``
* cross-file imports come from the TS ``import`` lines, no hard-coded type table
* enum value names come from the ``@generated ... enum value:`` comments
* field options are passed through verbatim (``(pkg.range) = {...}``)
* streaming RPCs, ``oneof``, ``map`` and unpacked ``repeated`` are supported

Library use:   ``convert_dir(ts_root, out_dir)``
CLI use:       ``python ts_to_proto.py <ts-dir|ts-file> [out-dir] [options]``
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PACKAGE = "wuxiaworld.api.v2"
EXTRA_FIELDOPTION = "extra_fieldoption_wuxiaworld.proto"
ROOT_PROTO = "wuxia.proto"

# protobuf ScalarType codes (the "T: n" numbers in reflection info)
SCALARS = {1: "double", 2: "float", 3: "int64", 4: "uint64", 5: "int32", 6: "fixed64",
           7: "fixed32", 8: "bool", 9: "string", 12: "bytes", 13: "uint32", 15: "sfixed32",
           16: "sfixed64", 17: "sint32", 18: "sint64"}
NON_PACKABLE = {9, 12}

# Custom FieldOptions the site uses: name -> (message type from options.proto, field number)
EXTENSIONS = {
    "stringLength": ("FieldStringLengthOptions", 50001),
    "wordLength": ("FieldWordLengthOptions", 50002),
    "required": ("FieldRequiredOption", 50003),
    "display": ("FieldDisplayOption", 50004),
    "range": ("FieldRangeOption", 50005),
}


@dataclass
class Options:
    package: str = DEFAULT_PACKAGE   # every file is unified into this package
    native_maps: bool = False        # True: map<K,V>;  False: repeated MapEntry_N messages
    explicit_optional: bool = True   # True: `optional` on every singular field
    verbose: bool = False


# ----------------------------------------------------------------------------
# tiny text helpers (string-aware bracket matching, no full JS parser needed)
# ----------------------------------------------------------------------------
def _skip_string(s: str, i: int) -> int:
    i += 1
    while i < len(s):
        if s[i] == "\\":
            i += 2
        elif s[i] == '"':
            return i + 1
        else:
            i += 1
    return i


def _match_close(s: str, i: int, op: str, cl: str) -> int:
    """Index just past the bracket that closes the one at s[i]."""
    depth = 0
    while i < len(s):
        c = s[i]
        if c == '"':
            i = _skip_string(s, i)
            continue
        if c == op:
            depth += 1
        elif c == cl:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError(f"unbalanced {op}{cl}")


def _split_objects(body: str) -> list[str]:
    """Top-level ``{...}`` chunks of an array body."""
    out, i = [], 0
    while i < len(body):
        if body[i] == "{":
            j = _match_close(body, i, "{", "}")
            out.append(body[i:j])
            i = j
        elif body[i] == '"':
            i = _skip_string(body, i)
        else:
            i += 1
    return out


def _pop_block(text: str, key: str):
    """Remove ``key: { ... }`` from text; return (inner, remaining_text)."""
    m = re.search(r"\b%s:\s*\{" % key, text)
    if not m:
        return None, text
    start = m.end() - 1
    end = _match_close(text, start, "{", "}")
    return text[start + 1:end - 1], text[:m.start()] + text[end:]


_COMMENT = re.compile(r"/\*.*?\*/", re.S)


# ----------------------------------------------------------------------------
# parsed model
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class TypeRef:
    kind: str                    # scalar | enum | message
    scalar: int | None = None
    ident: str | None = None     # TS identifier of the enum / message type


@dataclass
class Field:
    no: int
    name: str
    kind: str                    # scalar | enum | message | map
    type: TypeRef | None = None
    repeat: int = 0              # 0 none, 1 packed, 2 unpacked
    oneof: str | None = None
    opt: bool = False
    json_name: str | None = None
    options: list = field(default_factory=list)   # [(option name, text-format value)]
    key: int | None = None       # map key scalar code
    value: TypeRef | None = None  # map value type


@dataclass
class Message:
    ident: str
    full: str
    fields: list


@dataclass
class Enum:
    ident: str
    full: str
    values: list                 # [(name, number)]


@dataclass
class Rpc:
    name: str
    req: str
    res: str
    client_stream: bool
    server_stream: bool


@dataclass
class Service:
    name: str
    rpcs: list


@dataclass
class TsFile:
    path: Path
    package: str | None
    imports: dict                # local ident -> (original ident, module path)
    messages: list
    enums: list
    services: list

    @property
    def stem(self) -> str:
        return self.path.stem

    def local(self, full: str) -> str:
        """Name relative to the file's own package."""
        if self.package and full.startswith(self.package + "."):
            return full[len(self.package) + 1:]
        return full


# ----------------------------------------------------------------------------
# TS parsing
# ----------------------------------------------------------------------------
_HEADER = re.compile(r'@generated from protobuf file "[^"]*" \((?:package "([^"]+)",\s*)?syntax')
_IMPORT = re.compile(r'import\s+(?:type\s+)?\{([^}]*)\}\s+from\s+"([^"]+)"')
_CLASS = re.compile(r"class\s+([\w$]+?)\$Type\s+extends\s+MessageType")
_ENUM_DOC = re.compile(r"@generated from protobuf enum ([\w.]+)\s*\*/\s*export\s+(?:const\s+)?enum\s+(\w+)\s*\{")
_ENUM_ANY = re.compile(r"export\s+(?:const\s+)?enum\s+(\w+)\s*\{")
_SERVICE = re.compile(r'new\s+ServiceType\(\s*"([^"]+)"\s*,\s*\[')


def _parse_type(kind: str, text: str) -> TypeRef:
    if kind == "scalar":
        return TypeRef("scalar", scalar=int(re.search(r"\bT:\s*(\d+)", text).group(1)))
    m = re.search(r"\bT:\s*\(\)\s*=>\s*(\[[^\]]*\]|[\w$.]+)", text)
    if not m:
        raise ValueError(f"cannot read {kind} type from: {text[:80]}")
    tok = m.group(1)
    if tok.startswith("["):      # ["pkg.Enum", Enum, "PREFIX_"?]
        return TypeRef(kind, ident=re.findall(r'"[^"]*"|[\w$]+', tok[1:-1])[1])
    return TypeRef(kind, ident=tok)


def _parse_options(block: str) -> list:
    out, pos, pat = [], 0, re.compile(r'"([^"]+)"\s*:\s*\{')
    while True:
        m = pat.search(block, pos)
        if not m:
            return out
        start = m.end() - 1
        end = _match_close(block, start, "{", "}")
        out.append((m.group(1), re.sub(r"\s+", " ", block[start:end]).strip()))
        pos = end


def _parse_field(obj: str) -> Field:
    inner = obj[1:-1]
    opts, inner = _pop_block(inner, "options")
    vblk, inner = _pop_block(inner, "V")
    no = re.search(r"\bno:\s*(\d+)", inner)
    name = re.search(r'\bname:\s*"([^"]+)"', inner)
    kind = re.search(r'\bkind:\s*"(\w+)"', inner)
    if not (no and name and kind):
        raise ValueError(f"unrecognised field: {obj[:80]}")
    f = Field(int(no.group(1)), name.group(1), kind.group(1))
    oneof = re.search(r'\boneof:\s*"([^"]+)"', inner)
    repeat = re.search(r"\brepeat:\s*(\d)", inner)
    js = re.search(r'\bjsonName:\s*"([^"]+)"', inner)
    f.oneof = oneof.group(1) if oneof else None
    f.repeat = int(repeat.group(1)) if repeat else 0
    f.opt = bool(re.search(r"\bopt:\s*true", inner))
    f.json_name = js.group(1) if js else None
    f.options = _parse_options(opts) if opts else []
    if f.kind == "map":
        f.key = int(re.search(r"\bK:\s*(\d+)", inner).group(1))
        f.value = _parse_type(re.search(r'\bkind:\s*"(\w+)"', vblk).group(1), vblk)
    else:
        f.type = _parse_type(f.kind, inner)
    return f


def parse_ts(path: Path) -> TsFile:
    raw = path.read_text(encoding="utf-8")
    code = _COMMENT.sub("", raw)          # reflection data never needs comments

    hm = _HEADER.search(raw)
    package = hm.group(1) if hm else None

    imports = {}
    for m in _IMPORT.finditer(code):
        module = m.group(2)
        if module.startswith("@protobuf-ts"):
            continue
        for part in m.group(1).split(","):
            part = part.strip()
            if part:
                orig, _, alias = part.partition(" as ")
                imports[(alias or orig).strip()] = (orig.strip(), module)

    messages = []
    starts = [(m.start(), m.end(), m.group(1)) for m in _CLASS.finditer(code)]
    for n, (_, end, ident) in enumerate(starts):
        limit = starts[n + 1][0] if n + 1 < len(starts) else len(code)
        sm = re.compile(r'super\(\s*"([^"]+)"\s*,\s*\[').search(code, end, limit)
        if not sm:
            continue
        arr_start = sm.end() - 1
        arr = code[arr_start:_match_close(code, arr_start, "[", "]")]
        fields = sorted((_parse_field(o) for o in _split_objects(arr[1:-1])), key=lambda f: f.no)
        messages.append(Message(ident, sm.group(1), fields))

    enums, seen = [], set()
    for m in _ENUM_DOC.finditer(raw):
        body = raw[m.end():raw.find("\n}", m.end())]
        vals = [(a, int(b)) for a, b in re.findall(r"enum value:\s*(\w+)\s*=\s*(-?\d+)", body)]
        if not vals:                       # no doc comments: fall back to TS names
            vals = [(a, int(b)) for a, b in re.findall(r"(\w+)\s*=\s*(-?\d+)", _COMMENT.sub("", body))]
        enums.append(Enum(m.group(2), m.group(1), vals))
        seen.add(m.group(2))
    for m in _ENUM_ANY.finditer(code):     # enums generated without doc comments
        if m.group(1) not in seen:
            body = code[m.end():code.find("\n}", m.end())]
            vals = [(a, int(b)) for a, b in re.findall(r"(\w+)\s*=\s*(-?\d+)", body)]
            enums.append(Enum(m.group(1), (package + "." if package else "") + m.group(1), vals))

    services = []
    for m in _SERVICE.finditer(code):
        arr_start = m.end() - 1
        arr = code[arr_start:_match_close(code, arr_start, "[", "]")]
        rpcs = []
        for o in _split_objects(arr[1:-1]):
            _, o = _pop_block(o, "options")
            rpcs.append(Rpc(re.search(r'\bname:\s*"(\w+)"', o).group(1),
                            re.search(r"\bI:\s*([\w$]+)", o).group(1),
                            re.search(r"\bO:\s*([\w$]+)", o).group(1),
                            bool(re.search(r"\bclientStreaming:\s*true", o)),
                            bool(re.search(r"\bserverStreaming:\s*true", o))))
        services.append(Service(m.group(1).rsplit(".", 1)[-1], rpcs))

    return TsFile(path, package, imports, messages, enums, services)


# ----------------------------------------------------------------------------
# cross-file type resolution
# ----------------------------------------------------------------------------
class Registry:
    def __init__(self, files: list[TsFile]):
        self.files = {f.stem: f for f in files}
        if len(self.files) != len(files):
            raise ValueError("two TS files share the same file name")
        self.idents: dict[tuple[str, str], str] = {}   # (stem, TS ident) -> local proto name
        owner: dict[str, str] = {}
        for f in files:
            for d in [*f.messages, *f.enums]:
                local = f.local(d.full)
                if owner.setdefault(local, f.stem) != f.stem:
                    raise ValueError(f"'{local}' is defined in both {owner[local]} and {f.stem} "
                                     f"(packages are unified, so names must be unique)")
                self.idents[(f.stem, d.ident)] = local

    def resolve(self, f: TsFile, ident: str):
        """-> (proto type name, import path or None)."""
        if (f.stem, ident) in self.idents:
            return self.idents[(f.stem, ident)], None
        if ident in f.imports:
            orig, module = f.imports[ident]
            g = re.search(r"(?:^|/)google/protobuf/(\w+)$", module)
            if g:                                         # well-known type, provided by protoc
                return f"google.protobuf.{orig}", f"google/protobuf/{g.group(1)}.proto"
            stem = module.rsplit("/", 1)[-1]
            if (stem, orig) in self.idents:
                return self.idents[(stem, orig)], f"{stem}.proto"
        raise KeyError(f"{f.path.name}: cannot resolve type '{ident}'")


# ----------------------------------------------------------------------------
# .proto rendering
# ----------------------------------------------------------------------------
def render(f: TsFile, reg: Registry, opt: Options) -> str:
    imports: set[str] = set()
    msg_kids, enum_kids = defaultdict(list), defaultdict(list)
    for m in f.messages:
        local = f.local(m.full)
        msg_kids[local.rpartition(".")[0]].append((local, m))
    for e in f.enums:
        local = f.local(e.full)
        enum_kids[local.rpartition(".")[0]].append((local, e))

    def ref(t: TypeRef) -> str:
        if t.kind == "scalar":
            return SCALARS[t.scalar]
        name, imp = reg.resolve(f, t.ident)
        if imp:
            imports.add(imp)
        return name

    def field_options(fl: Field) -> str:
        parts = []
        for name, text in fl.options:
            if name.rpartition(".")[2] in EXTENSIONS and name.rpartition(".")[0] == DEFAULT_PACKAGE:
                parts.append(f"({name}) = {text}")
                imports.add(EXTRA_FIELDOPTION)
            else:
                print(f"  warning: {f.path.name}: unknown field option '{name}' skipped", file=sys.stderr)
        if fl.json_name:
            parts.append(f'json_name = "{fl.json_name}"')
        if fl.repeat == 2 and fl.kind in ("scalar", "enum") and not (
                fl.kind == "scalar" and fl.type.scalar in NON_PACKABLE):
            parts.append("packed = false")
        return f" [{', '.join(parts)}]" if parts else ""

    def emit_enum(local, e, ind):
        out = [f"{ind}enum {local.rpartition('.')[2]} {{"]
        out += [f"{ind}    {n} = {v};" for n, v in e.values]
        out.append(f"{ind}}}")
        return out

    def emit_message(local, m, ind):
        name = local.rpartition(".")[2]
        out = [f"{ind}message {name} {{"]
        for sub_local, sub in msg_kids.get(local, []):
            out += emit_message(sub_local, sub, ind + "    ") + [""]
        for sub_local, sub in enum_kids.get(local, []):
            out += emit_enum(sub_local, sub, ind + "    ") + [""]

        entry_names = {}                     # compat map mode: field no -> MapEntry_N
        if not opt.native_maps:
            n = 0
            for fl in m.fields:
                if fl.kind == "map":
                    entry_names[fl.no] = f"MapEntry_{n}"
                    n += 1
                    opt_ = "optional " if opt.explicit_optional else ""
                    out += [f"{ind}    message {entry_names[fl.no]} {{",
                            f"{ind}        {opt_}{SCALARS[fl.key]} key = 1;",
                            f"{ind}        {opt_}{ref(fl.value)} value = 2;",
                            f"{ind}    }}", ""]

        oneofs = {}
        for fl in m.fields:
            if fl.oneof:
                oneofs.setdefault(fl.oneof, []).append(fl)
        for oname, members in oneofs.items():
            out.append(f"{ind}    oneof {oname} {{")
            out += [f"{ind}        {ref(fl.type)} {fl.name} = {fl.no}{field_options(fl)};" for fl in members]
            out += [f"{ind}    }}", ""]

        for fl in m.fields:
            if fl.oneof:
                continue
            if fl.kind == "map":
                if opt.native_maps:
                    typ = f"map<{SCALARS[fl.key]}, {ref(fl.value)}>"
                    prefix = ""
                else:
                    typ, prefix = f"{local}.{entry_names[fl.no]}", "repeated "
            else:
                typ = ref(fl.type)
                if fl.repeat:
                    prefix = "repeated "
                elif fl.opt or opt.explicit_optional:
                    prefix = "optional "
                else:
                    prefix = ""
            out.append(f"{ind}    {prefix}{typ} {fl.name} = {fl.no}{field_options(fl)};")
        out.append(f"{ind}}}")
        return out

    body: list[str] = []
    for local, e in enum_kids.get("", []):
        body += emit_enum(local, e, "") + [""]
    for local, m in msg_kids.get("", []):
        body += emit_message(local, m, "") + [""]
    for svc in f.services:
        body.append(f"service {svc.name} {{")
        for r in svc.rpcs:
            req = ("stream " if r.client_stream else "") + ref(TypeRef("message", ident=r.req))
            res = ("stream " if r.server_stream else "") + ref(TypeRef("message", ident=r.res))
            body.append(f"    rpc {r.name}({req}) returns ({res});")
        body.append("}")

    head = ['syntax = "proto3";', f"package {opt.package};"]
    if imports:
        head += [""] + [f'import "{i}";' for i in sorted(imports)]
    return "\n".join(head + [""] + body).rstrip("\n") + "\n"


# ----------------------------------------------------------------------------
# directory-level API
# ----------------------------------------------------------------------------
def collect_ts(root: Path) -> list[Path]:
    """TS files that define schema: skips RPC clients, well-known google/* types, .ignor* dirs."""
    out = []
    for p in sorted(root.rglob("*.ts")):
        parent_dirs = p.relative_to(root).parts[:-1]
        if p.name.endswith((".client.ts", ".d.ts")):
            continue
        if "google" in parent_dirs or any(d.startswith(".ignor") for d in parent_dirs):
            continue
        out.append(p)
    return out


def extra_fieldoption_text(package: str = DEFAULT_PACKAGE) -> str:
    lines = ['syntax = "proto3";', f"package {package};", "",
             'import "google/protobuf/descriptor.proto";', 'import "options.proto";', "",
             "extend google.protobuf.FieldOptions {"]
    lines += [f"    {typ} {name} = {num};" for name, (typ, num) in EXTENSIONS.items()]
    return "\n".join(lines + ["}", ""])


def write_root_proto(out_dir: Path, stems, package: str = DEFAULT_PACKAGE, name: str = ROOT_PROTO) -> Path:
    lines = ['syntax = "proto3";', "", f'import "{EXTRA_FIELDOPTION}";']
    lines += [f'import "{s}.proto";' for s in sorted(stems)]
    lines += ["", f"package {package};", "", "// WUXIA API - imports every converted proto file", ""]
    path = out_dir / name
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def convert_dir(ts_root: Path, out_dir: Path, opt: Options | None = None,
                only: list[Path] | None = None, root_proto: str | None = None) -> list[str]:
    """Convert every schema .ts under ts_root into out_dir/<name>.proto. Returns the stems written."""
    opt = opt or Options()
    ts_root, out_dir = Path(ts_root), Path(out_dir)
    files = [parse_ts(p) for p in collect_ts(ts_root)]
    reg = Registry(files)
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = {Path(p).stem for p in only} if only else None

    written = []
    for f in files:
        if wanted and f.stem not in wanted:
            continue
        (out_dir / f"{f.stem}.proto").write_text(render(f, reg, opt), encoding="utf-8")
        written.append(f.stem)
        if opt.verbose:
            print(f"Generated: {out_dir / (f.stem + '.proto')}")
    (out_dir / EXTRA_FIELDOPTION).write_text(extra_fieldoption_text(opt.package), encoding="utf-8")
    if "options" not in reg.files:
        print("  warning: no options.ts found - extra_fieldoption_wuxiaworld.proto imports options.proto",
              file=sys.stderr)
    if root_proto:
        write_root_proto(out_dir, written, opt.package, root_proto)
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert protobuf-ts TypeScript to .proto files")
    ap.add_argument("input", help="TS directory, or one TS file (siblings are read to resolve imports)")
    ap.add_argument("output", nargs="?", help="output directory (default: next to the input)")
    ap.add_argument("--root", metavar="NAME", help=f"also write a root proto importing everything (e.g. {ROOT_PROTO})")
    ap.add_argument("--package", default=DEFAULT_PACKAGE, help="package for every generated file")
    ap.add_argument("--native-maps", action="store_true", help="emit real map<K,V> fields instead of MapEntry_N messages")
    ap.add_argument("--no-optional", action="store_true", help="don't put `optional` on every singular field")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)

    opt = Options(a.package, a.native_maps, not a.no_optional, a.verbose)
    src = Path(a.input)
    if src.is_dir():
        out = Path(a.output) if a.output else src
        stems = convert_dir(src, out, opt, root_proto=a.root)
    else:
        out = Path(a.output) if a.output else src.parent
        stems = convert_dir(src.parent, out, opt, only=[src], root_proto=a.root)
    print(f"Generated {len(stems)} proto file(s) in {out}")


if __name__ == "__main__":
    main()
