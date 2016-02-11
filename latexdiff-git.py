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
import os
import fnmatch
import re
import datetime


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
        self.filelist = []
        self.rev1filelist = []
        self.rev2filelist = []

        self.gitResetCommand = "git reset HEAD --hard".split()
        self.gitCheckoutCommand = "git checkout".split()
        self.gitAddCommand = "git add .".split()
        self.gitCommitCommand = "git commit -m".split()
        self.pdflatexCommand = "pdflatex -interaction batchmode".split()

        # regular expressions for revision
        self.rexepDelbegin = re.compile(r'\DIFdelbegin')
        self.rexepDelend = re.compile(r'\DIFdelend')
        self.rexepAddbegin = re.compile(r'\DIFaddbegin')
        self.rexepAddend = re.compile(r'\DIFaddend')
        self.regexBoth = re.compile(r'\DIFdelbegin\s*\DIFaddbegin')

    def diff(self, args):
        """Do the diff part."""
        self.rename_files_for_diff()
        # Checkout the first revision 1
        print("Checking out revision 1: {}".format(self.optionsDict['rev1']))
        command = (self.gitCheckoutCommand + (" -b " +
                                              self.rev1Branch).split() +
                   [self.optionsDict['rev1']])
        subprocess.call(command)

        # Rename files
        for i in range(0, len(self.filelist)):
            os.rename(self.filelist[i], self.rev1filelist[i])

        # Check out revision 2
        print("Checking out revision 2: {}".format(self.optionsDict['rev2']))
        command = (self.gitCheckoutCommand + (" -b " +
                                              self.rev2Branch).split() +
                   [self.optionsDict['rev2']])
        p = subprocess.Popen(command)
        p.wait()

        # Reset the state so that the files we deleted earlier are back
        subprocess.call(self.gitResetCommand)

        print("Checking out branch to save changes.")
        command = (self.gitCheckoutCommand + (" -b " +
                                              self.finalBranch).split() +
                   [self.rev2Branch])
        subprocess.call(command)

        # Rename files
        for i in range(0, len(self.filelist)):
            os.rename(self.filelist[i], self.rev2filelist[i])

        # Generate diffs
        for i in range(0, len(self.filelist)):
            command = (["latexdiff"] + ("--type=" + self.optionsDict['type'] +
                                        " --exclude-textcmd=" +
                                        self.optionsDict['exclude']).split() +
                       [self.rev1filelist[i], self.rev2filelist[i]])
            print(command)
            with open(self.filelist[i], "w") as stdout:
                p = subprocess.Popen(command, stdout=stdout)
                p.wait()

            os.remove(self.rev1filelist[i])
            os.remove(self.rev2filelist[i])

        # Generate pdf
        command = (self.pdflatexCommand + ("-jobname=diff-" +
                                           self.optionsDict['rev1'] + "-" +
                                           self.optionsDict['rev2']
                                           ).split() +
                   [self.optionsDict['main']])
        subprocess.call(command, cwd=self.optionsDict['subdir'])

        subprocess.call(self.gitAddCommand)

        command = (self.gitCommitCommand + ["Save annotated changes between " +
                                            self.optionsDict['rev1'] + " and "
                                            + self.optionsDict['rev2']])
        subprocess.call(command)

        print("\nCOMPLETE: The following branches have been created:\n" +
              self.rev1Branch + ": Revision 1.\n" +
              self.rev2Branch + ": Revision 2.\n" +
              self.finalBranch +
              ": Branch with annotated versions of sources and diff pdf.\n" +
              "The generated diff pdf is: " + self.optionsDict['subdir'] +
              "/diff-" + self.optionsDict['rev1'] + "-" +
              self.optionsDict['rev2'] + ".pdf.\n")

    def revise(self, args):
        """Do the revise part."""
        for i in range(0, len(self.filelist)):
            filetext = ""
            with open(self.filelist[i], "r") as thisfile:
                filetext = thisfile.read()
            print("Working on file: {}.".format(self.filelist[i]))

    def get_latex_files(self):
        """Get list of files with extension .tex."""
        for root, dirs, files in os.walk('.'):
            for filename in fnmatch.filter(files, "*.tex"):
                self.filelist.append(os.path.join(root, filename))
        if not len(self.filelist) > 0:
            print("No tex files found in this directory", file=sys.stderr)
            sys.exit(-1)
        print(self.filelist)

    def rename_files_for_diff(self):
        """Rename files as required for diff."""
        self.rev1filelist = []
        self.rev2filelist = []
        for filename in self.filelist:
            rev1name = (filename[:-4] + "-" + self.optionsDict['rev1'] +
                        ".tex")
            rev2name = (filename[:-4] + "-" + self.optionsDict['rev2'] +
                        ".tex")
            self.rev1filelist.append(rev1name)
            self.rev2filelist.append(rev2name)

    def setup(self):
        """Setup things."""
        self.timenow = datetime.datetime.strftime(datetime.datetime.today(),
                                                  "%Y%m%d%H%M")
        self.rev1Branch = self.timenow + "-latexdiff-rev1"
        self.rev2Branch = self.timenow + "-latexdiff-rev2"
        self.finalBranch = self.timenow + "-latexdiff-annotated"

        self.parser = argparse.ArgumentParser(
            prog="latexdiff-git",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self.usage_message,
            add_help=False
        )

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
        self.diff_parser.add_argument("-r", "--rev1",
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
        self.diff_parser.add_argument("-s", "--subdir",
                                      default=".",
                                      action="store",
                                      help="Name of subdirectory where main \
                                      file resides.\
                                      Default: ."
                                      )
        self.diff_parser.add_argument("-e", "--exclude",
                                      default="\"\"",
                                      action="store",
                                      help="Pass exclude options to latexdiff. \
                                      Please read man latexdiff for \
                                      information on --exclude-textcmd \
                                      and related options."
                                      )
        self.diff_parser.add_argument("-p", "--type",
                                      default="\"UNDERLINE\"",
                                      action="store",
                                      help="Pass markup type option to latexdiff. \
                                      Please read man latexdiff for options."
                                      )

    def run(self):
        """Main runner method."""
        if len(sys.argv) == 1:
            self.parser.print_help()
            sys.exit(1)

        self.options = self.parser.parse_args()
        self.optionsDict = vars(self.options)
        if len(self.optionsDict) != 0:
            # Check for latex files and get a list
            self.get_latex_files()

            print(self.optionsDict)
            self.options.func(self.options)


if __name__ == "__main__":
    runner_instance = LatexDiffGit()
    runner_instance.setup()
    runner_instance.run()
