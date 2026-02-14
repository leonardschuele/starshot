"""Starshot IR CLI: parse, compile, and run .sir programs."""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from starshot.ir.parser import parse
from starshot.ir.lexer import LexError
from starshot.ir.parser import ParseError
from starshot.compiler.python_emitter import compile_to_python


def cmd_parse(args):
    """Parse a .sir file and print the AST."""
    source = Path(args.file).read_text()
    try:
        program = parse(source)
    except (LexError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Program with {len(program.types)} types, {len(program.graphs)} graphs")
    for td in program.types:
        print(f"  type {td.name}")
    for g in program.graphs:
        effects = ', '.join(g.effects)
        params = ', '.join(f"{n}" for n, _ in g.inputs)
        print(f"  graph {g.name}({params}) [{effects}]")


def cmd_compile(args):
    """Compile a .sir file to Python and print the output."""
    source = Path(args.file).read_text()
    try:
        program = parse(source)
        python_code = compile_to_python(program)
    except (LexError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    if args.output:
        Path(args.output).write_text(python_code)
        print(f"Compiled to {args.output}")
    else:
        print(python_code)


def cmd_run(args):
    """Compile a .sir file and execute the resulting Python."""
    source = Path(args.file).read_text()
    try:
        program = parse(source)
        python_code = compile_to_python(program)
    except (LexError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(python_code)
        tmp_path = f.name

    try:
        result = subprocess.run([sys.executable, tmp_path],
                                capture_output=not args.verbose,
                                text=True)
        if result.returncode != 0:
            if not args.verbose:
                print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
        if not args.verbose and result.stdout:
            print(result.stdout, end='')
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def cmd_check(args):
    """Type-check and effect-check a .sir file."""
    source = Path(args.file).read_text()
    try:
        program = parse(source)
    except (LexError, ParseError) as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    errors = []
    try:
        from starshot.compiler.type_checker import check_types
        errors.extend(check_types(program))
    except ImportError:
        pass

    try:
        from starshot.compiler.effect_checker import check_effects
        errors.extend(check_effects(program))
    except ImportError:
        pass

    if errors:
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print("All checks passed.")


def main():
    parser = argparse.ArgumentParser(
        prog='starshot',
        description='Starshot IR toolchain: parse, compile, and run .sir programs'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # parse
    p_parse = subparsers.add_parser('parse', help='Parse a .sir file and show AST summary')
    p_parse.add_argument('file', help='Path to .sir file')
    p_parse.set_defaults(func=cmd_parse)

    # compile
    p_compile = subparsers.add_parser('compile', help='Compile a .sir file to Python')
    p_compile.add_argument('file', help='Path to .sir file')
    p_compile.add_argument('-o', '--output', help='Output Python file path')
    p_compile.set_defaults(func=cmd_compile)

    # run
    p_run = subparsers.add_parser('run', help='Compile and run a .sir file')
    p_run.add_argument('file', help='Path to .sir file')
    p_run.add_argument('-v', '--verbose', action='store_true', help='Show Python output in real-time')
    p_run.set_defaults(func=cmd_run)

    # check
    p_check = subparsers.add_parser('check', help='Type-check and effect-check a .sir file')
    p_check.add_argument('file', help='Path to .sir file')
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
