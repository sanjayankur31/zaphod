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
import textwrap
import subprocess


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

    def __init__(self):
        """Init method."""
        self.usage_message = textwrap.dedent(
            """
        NOTES:
            The idea of this program is to help LaTeX users track, review, and
            see changes that have been made in their source files. The script
            only works when git is used as a version control system.

        Expected workflow:
            *) Make changes, commit
            *) Run this program:
                It will generate a pdf with differences between the two
                provided Git revisions using latexdiff. It will also commit the
                annotated TeX sources in a new Git branch called "changes".
                *) Review commits using generated PDF.
                *) Accept/ignore commits using this program.
                *) Commit once finished.
                *) Merge to master branch.
                *) Profit.

        Requires:
            *) latexdiff
            *) latexrevise
            *) Git
            *) pdflatex
            *) Written in Python, so should work on any system where these are
               present.

            """)

        self.gitResetCommand = "git reset HEAD --hard"
        self.gitCheckoutCommand = "git checkout"
        self.gitStashPutCommand = "git stash -u"
        self.gitStashPopCommand = "git stash pop"
        self.renameCommand = "find . -name \"*.tex\" -exec rename -- \".tex\""

    def diff(self, args):
        """Do the diff part."""
        print("Yay")
        print("Checking out revision 1: {}".format(self.optionsDict['rev1']))
        command = (self.gitCheckoutCommand +
                   " -b changes" + self.optionsDict['rev1'])
        subprocess.call(command)
        command = (self.renameCommand + "\"-" + self.optionsDict['rev1'] +
                   ".tex\" '{}' \;")
        subprocess.call(command)
        subprocess.call(self.gitStashPutCommand)

    def revise(self, args):
        """Do the revise part."""
        print("No yay")

    def setup(self):
        """Setup things."""
        self.parser = argparse.ArgumentParser(prog="latexdiff-git",
                                              formatter_class=argparse.RawDescriptionHelpFormatter,
                                              epilog=self.usage_message,
                                              add_help=False)
        self.parser.add_argument("-h", "--help", action=_HelpAction,
                                 help="View subcommand help")

        self.subparser = self.parser.add_subparsers(
            help="additional help")

        self.revise_parser = self.subparser.add_parser(
            "revise",
            epilog="NOTE: This feature is not yet implemented.",
            help="Interactive revision (UNIMPLEMENTED)",
        )
        self.revise_parser.set_defaults(func=self.revise)

        self.diff_parser = self.subparser.add_parser(
            "diff",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            help="Generate changes output"
        )
        self.diff_parser.set_defaults(func=self.diff)
        self.diff_parser.add_argument("-s", "--rev1",
                                      default="master^",
                                      action="store",
                                      help="First revision to diff against")
        self.diff_parser.add_argument("-t", "--rev2",
                                      default="master",
                                      action="store",
                                      help="Second revision to diff with.")
        self.diff_parser.add_argument("-m", "--main",
                                      action="store",
                                      default="main.tex",
                                      help="Name of main file. Only used to \
                                      generate final pdf with changes. \
                                      Default: main.tex")

    def run(self):
        """Main runner method."""
        if len(sys.argv) == 1:
            self.parser.print_help()
            sys.exit(1)

        self.options = self.parser.parse_args()
        self.optionsDict = vars(self.options)
        if len(self.optionsDict) != 0:
            print(self.optionsDict)
            self.options.func(self.options)

if __name__ == "__main__":
    runner_instance = LatexDiffGit()
    runner_instance.setup()
    runner_instance.run()
