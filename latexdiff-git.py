#!/usr/bin/env python3
"""
Save changes between commits and revise them.

File: latexdiff-git.py

Copyright 2016 Ankur Sinha
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import sys


class _HelpAction(argparse._HelpAction):

    """
    Custom help handler.

    http://stackoverflow.com/a/24122778/375067
    """

    def __call__(self, parser, namespace, values, option_string=None):
        """Custom call method."""
        parser.print_help()
        print("\n")

        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                print("Subcommand: '{}'".format(choice))
                print(subparser.format_help())


class LatexDiffGit:

    """Something something."""

    def setup(self):
        """Setup things."""
        self.parser = argparse.ArgumentParser(prog="latexdiff-git",
                                              add_help=False)
        self.parser.add_argument("-h", "--help", action=_HelpAction,
                                 help="View complete help document")

        self.subparser = self.parser.add_subparsers(
            help="additional help")

        self.revise_parser = self.subparser.add_parser(
            "revise",
            help="Interactive revision (WIP)",
        )

        self.diff_parser = self.subparser.add_parser(
            "diff",
            help="Generate changes output"
        )
        self.diff_parser.add_argument("-s", "--rev1",
                                      help="First revision to diff against")
        self.diff_parser.add_argument("-t", "--rev2",
                                      help="Second revision to diff with.")

    def run(self):
        """Main runner method."""
        if len(sys.argv) == 1:
            self.parser.print_help()
            sys.exit(1)
        self.parser.parse_args()


if __name__ == "__main__":
    runner_instance = LatexDiffGit()
    runner_instance.setup()
    runner_instance.run()
