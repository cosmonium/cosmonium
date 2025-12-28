#!/usr/bin/env python3
#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

"""
Standalone tool to convert Celestia CMOD files to Panda3D EGG format.

Usage:
    python cmod2egg.py input.cmod [output.egg]

If output.egg is not specified, the output will be written to input.egg
(same name as input but with .egg extension).
"""

import argparse
import os
import sys

# Add parent directory to path to import cosmonium modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cosmonium.cmod.cmod_parser import CMODParser  # noqa: E402
from cosmonium.cmod.egg_writer import EggWriter  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description='Convert Celestia CMOD files to Panda3D EGG format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s model.cmod
  %(prog)s model.cmod output.egg
  %(prog)s spacecraft.cmod -o converted.egg

This tool converts Celestia Model (CMOD) files to Panda3D's EGG format.
Both binary and ASCII CMOD formats are supported.
        """,
    )

    parser.add_argument('input', help='Input CMOD file path')
    parser.add_argument(
        'output', nargs='?', help='Output EGG file path (optional, defaults to input name with .egg extension)'
    )
    parser.add_argument(
        '-o',
        '--output-file',
        dest='output_alt',
        help='Alternative way to specify output file (cannot be used with positional output argument)',
    )
    parser.add_argument('-f', '--force', action='store_true', help='Force overwrite if output file exists')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Determine input and output paths
    input_path = args.input

    # Output can be specified either as positional argument or via -o flag, but not both
    if args.output and args.output_alt:
        print("Error: Cannot specify output both as positional argument and via -o flag", file=sys.stderr)
        return 1

    output_path = args.output or args.output_alt

    if not output_path:
        # Default: replace .cmod extension with .egg
        base, ext = os.path.splitext(input_path)
        if ext.lower() != '.cmod':
            print(f"Warning: Input file '{input_path}' does not have .cmod extension", file=sys.stderr)
        output_path = base + '.egg'

    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found", file=sys.stderr)
        return 1

    # Check if output file exists and --force not specified
    if os.path.exists(output_path) and not args.force:
        print(f"Error: Output file '{output_path}' already exists. Use --force to overwrite.", file=sys.stderr)
        return 1

    # Perform conversion
    try:
        if args.verbose:
            print(f"Converting '{input_path}' to '{output_path}'...")

        # Parse CMOD file
        parser = CMODParser()
        try:
            model_data = parser.parse(input_path)
        except Exception as e:
            raise ValueError(f"Failed to parse CMOD file '{input_path}': {str(e)}")

        # Write EGG file
        writer = EggWriter()
        try:
            writer.write(output_path, model_data)
        except Exception as e:
            raise ValueError(f"Failed to write EGG file '{output_path}': {str(e)}")

        if args.verbose:
            print(f"Successfully converted to '{output_path}'")
        else:
            print(f"Converted: {output_path}")

        return 0

    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
