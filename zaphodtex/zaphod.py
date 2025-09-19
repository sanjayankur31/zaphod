#!/usr/bin/env python3
"""
A LaTeX change tracking tool.

File: zaphod.py

Copyright 2020 Ankur Sinha
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
import datetime
import fnmatch
import logging
import os
import re
import shutil
import subprocess
import sys
import textwrap

from zaphod import __version__


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
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                print(f"Subcommand: '{choice}'")
                print(subparser.format_help())


class Zaphod:
    """Main application class"""

    def __init__(self):
        """Init method."""
        self.usage_message = textwrap.dedent(
            f"""

        zaphod (version: {__version__}): A LaTeX change tracking tool

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
                *) Accept/ignore changes.
                *) Commit once finished.
                *) Merge to master branch.
                *) Profit.

        Requires:
            *) latexdiff
            *) Git
            *) pdflatex
            *) latexmk
            *) bibtex or biber
            *) Python3

            """
        )

        self.commandList = ["pdflatex", "latexdiff", "git"]
        self.timenow = datetime.datetime.strftime(
            datetime.datetime.today(), "%Y%m%d%H%M"
        )
        self.branchSpec = "-zaphod-"
        self.rev1Branch = self.timenow + self.branchSpec + "rev1"
        self.rev2Branch = self.timenow + self.branchSpec + "rev2"
        self.finalBranch = self.timenow + self.branchSpec + "annotated"

        self.filelist = []
        self.rev1filelist = []
        self.rev2filelist = []
        self.modifiedfiles = []

        self.gitResetCommand = "git reset HEAD --hard".split()
        self.gitCheckoutCommand = "git checkout".split()
        self.gitAddCommand = "git add .".split()
        self.gitCommitCommand = "git commit -m".split()
        self.gitBranchCommand = "git branch".split()
        self.gitBranchDeleteCommand = "git branch -D".split()
        self.latexmkCleanCommand = "latexmk -C".split()
        self.latexmkCommand = (
            "latexmk -pdf -recorder".split()
            + "-synctex=1 -use-make".split()
            + ["-pdflatex=pdflatex -interaction=nonstopmode"]
        )

        self.bibFlag = ["-bibtex"]
        self.nobibFlag = ["-nobibtex"]

        # regular expressions for revision
        self.rxDelbegin = re.compile(r"\\DIFdelbegin\s*")
        self.rxDelend = re.compile(r"\\DIFdelend\s*")

        self.rxAddbegin = re.compile(r"\\DIFaddbegin\s*")
        self.rxAddend = re.compile(r"\\DIFaddend\s*")

        self.rPreamble = (
            r"%DIF PREAMBLE EXTENSION ADDED BY LATEXDIFF.*"
            + r"%DIF END PREAMBLE EXTENSION ADDED BY LATEXDIFF\n"
        )
        self.rxPreamble = re.compile(self.rPreamble, flags=re.DOTALL)
        self.rxStray = (
            r"(\\DIFaddbegin\s*)|(\\DIFaddend\s*)"
            + r"(\\DIFdelbegin\s*)|(\\DIFdelend\s*)"
        )

        # set up a logger
        self.logger = logging.getLogger("zaphod")
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.logger.propagate = False

    def diff(self, args):
        """Do the diff part."""
        # Get all latex files in rev1
        command = (
            self.gitCheckoutCommand
            + (" -b " + self.rev1Branch).split()
            + [self.optionsDict["rev1"]]
        )
        p = subprocess.Popen(command)
        p.wait()
        self.zprint("Generating full file list.")
        self.filelist += self.get_latex_files()

        # Get all latex files in rev2
        command = (
            self.gitCheckoutCommand
            + (" -b " + self.rev2Branch).split()
            + [self.optionsDict["rev2"]]
        )
        p = subprocess.Popen(command)
        p.wait()
        self.filelist += self.get_latex_files()
        # remove duplicates
        self.filelist = list(set(self.filelist))
        self.zprint(f"File list generated:\n{self.filelist}")

        # Now that we have a complete list, we get to work
        self.zprint(f"Checking out revision 1: {self.optionsDict['rev1']}")
        command = self.gitCheckoutCommand + [self.rev1Branch]
        p = subprocess.Popen(command)
        p.wait()
        self.rev1filelist = self.generate_rev_filenames(self.optionsDict["rev1"])

        # Rename files
        for i in range(0, len(self.filelist)):
            # if a file doesn't exist in this revision, it has been removed, so
            # I create an empty file for latexdiff
            if not os.path.isfile(self.filelist[i]):
                dirname, filename = os.path.split(self.filelist[i])
                # also check if the directory structure exists
                if not os.path.exists(dirname):
                    os.makedirs(dirname, exist_ok=True)
                # then create the dummy file
                open(self.filelist[i], "a").close()
            os.rename(self.filelist[i], self.rev1filelist[i])

        # Check out revision 2
        self.zprint(f"Checking out revision 2: {self.optionsDict['rev2']}")
        command = self.gitCheckoutCommand + [self.rev2Branch]
        p = subprocess.Popen(command)
        p.wait()

        # Reset the state so that the files we deleted earlier are back
        subprocess.call(self.gitResetCommand)

        self.zprint("Checking out branch to save changes.")
        command = (
            self.gitCheckoutCommand
            + (" -b " + self.finalBranch).split()
            + [self.rev2Branch]
        )
        subprocess.call(command)

        self.rev2filelist = self.generate_rev_filenames(self.optionsDict["rev2"])
        # Rename files
        for i in range(0, len(self.filelist)):
            if not os.path.isfile(self.filelist[i]):
                open(self.filelist[i], "a").close()
            os.rename(self.filelist[i], self.rev2filelist[i])

        # Generate diffs
        for i in range(0, len(self.filelist)):
            command = (
                ["latexdiff"]
                + self.optionsDict["latexdiffopts"].split()
                + [self.rev1filelist[i], self.rev2filelist[i]]
            )
            # self.zprint(command)
            changedtext = None
            changedtext = subprocess.check_output(command)
            if changedtext is None:
                self.logger.error(
                    "Something went wrong "
                    + f"- not annotating file: {self.filelist[i]}\n",
                    file=sys.stderr,
                )
            else:
                newfile = open(self.filelist[i], "w")
                newfile.write(changedtext.decode("utf-8"))
                newfile.close()
                self.modifiedfiles += [self.filelist[i]]

            os.remove(self.rev1filelist[i])
            os.remove(self.rev2filelist[i])

        self.generate_pdf(
            "zaphod-diff-" + self.optionsDict["rev1"] + "-" + self.optionsDict["rev2"]
        )

        subprocess.call(self.gitAddCommand)

        command = self.gitCommitCommand + [
            "Save annotated changes between "
            + self.optionsDict["rev1"]
            + " and "
            + self.optionsDict["rev2"]
        ]
        subprocess.call(command)

        self.zprint("The following branches have been created:")
        self.zprint(self.rev1Branch + ": Revision 1.")
        self.zprint(self.rev2Branch + ": Revision 2.")
        self.zprint(self.finalBranch + ": Branch with annotated versions of sources")

    def revise(self, args):
        """Do the revise part."""
        self.filelist = self.get_modified_latex_files()
        self.originalfilelist = self.filelist
        while len(self.filelist) > 0:
            while True:
                self.zprint("LaTeX files with annotations:")
                for i in range(0, len(self.filelist)):
                    print(f"[{(i + 1)}] {self.filelist[i]}")

                print()
                filenumber = input(f"Pick file to revise? 1-{len(self.filelist)}/Q/q: ")
                print()

                if filenumber.isalpha():
                    if filenumber == "Q" or filenumber == "q":
                        self.remove_preamble()
                        self.generate_pdf("accepted")
                        self.save_changes()

                if filenumber.isdigit():
                    filenumber = int(filenumber)
                else:
                    self.zprint("Invalid input. Please try again.")
                    continue

                if filenumber > 0 and filenumber <= len(self.filelist):
                    self.modified = False
                    break
                else:
                    self.zprint("Invalid input. Please try again.")

            filetorevise = self.filelist[filenumber - 1]
            filetext = ""
            revisedfiletext = ""
            # Token at the head of a token
            head = 0
            # Token at the tail of previous token
            tail = 0
            with open(filetorevise, "r") as thisfile:
                filetext = thisfile.read()

            while head < len(filetext):
                # what's next - addition or deletion?
                del_start = 0
                delcheck = self.rxDelbegin.search(filetext[head:])
                add_start = 0
                addcheck = self.rxAddbegin.search(filetext[head:])
                preamble_start = 0
                preamblecheck = self.rxPreamble.search(filetext[head:])

                if preamblecheck is None:
                    preamble_start = len(filetext)
                else:
                    preamble_start = preamblecheck.start()
                if delcheck is None:
                    del_start = len(filetext)
                else:
                    del_start = delcheck.start()
                if addcheck is None:
                    add_start = len(filetext)
                else:
                    add_start = addcheck.start()

                # If both are at EOL
                if add_start == del_start:
                    revisedfiletext += filetext[head:]
                    # print("{}, {}".format(del_start, add_start))
                    break

                # Skip preamble here - remove it at the end if required
                if preamble_start < del_start and preamble_start < add_start:
                    tail = head + preamblecheck.end()
                    revisedfiletext += filetext[head:tail]
                    head = tail
                    # self.zprint("latexdiff preamble found and ignored.")
                    continue

                if del_start < add_start:
                    # It's a deletion
                    head = del_start + tail
                    revisedfiletext += filetext[tail:head]
                    tail = self.rxDelbegin.search(filetext[head:]).end() + head
                    head = self.rxDelend.search(filetext[tail:]).start() + tail
                    deletion = filetext[tail:head]
                    deletion = re.sub(
                        r"\\DIFdel\{(.*?)\}", r"\1", deletion, flags=re.DOTALL
                    )
                    print(f"====== {filetorevise} ======")
                    print("--- Deletion found ---")
                    print(deletion)
                    print("--- Deletion found ---")
                    while True:
                        userinput = input("Accept deletion? Y/N/Q/y/n/q: ")
                        if not userinput.isalpha():
                            self.zprint("Invalid input. Try again.")
                            continue

                        if userinput == "Y" or userinput == "y":
                            self.zprint("Deletion accepted.")
                            print()
                            self.modified = True
                            break
                        elif userinput == "N" or userinput == "n":
                            self.zprint("Ignored.")
                            revisedfiletext += deletion
                            break
                        elif userinput == "Q" or userinput == "q":
                            if self.modified:
                                while True:
                                    savepartial = input("Save partial file? Y/N/y/n: ")
                                    if not savepartial.isalpha():
                                        self.zprint("Invalid input." + "Try again.")
                                        continue

                                    if savepartial == "Y" or savepartial == "y":
                                        revisedfiletext += filetext[head:]
                                        outputfile = open(filetorevise, "w")
                                        outputfile.write(revisedfiletext)
                                        outputfile.close()
                                        self.modifiedfiles += [filetorevise]
                                        break
                                    elif savepartial == "N" or savepartial == "n":
                                        self.zprint("Discarding changes.")
                                        break
                                    else:
                                        self.zprint("Invalid input. " + "Try again.")

                            self.generate_pdf("accepted")
                            self.save_changes()
                        else:
                            self.zprint("Invalid input. Try again.")

                    head = self.rxDelend.search(filetext[tail:]).end() + tail
                    tail = head
                else:
                    # It's an addition
                    head = add_start + tail
                    revisedfiletext += filetext[tail:head]
                    tail = self.rxAddbegin.search(filetext[head:]).end() + head
                    head = self.rxAddend.search(filetext[tail:]).start() + tail
                    addition = filetext[tail:head]
                    addition = re.sub(
                        r"\\DIFadd\{(.*?)\}", r"\1", addition, flags=re.DOTALL
                    )
                    print(f"====== {filetorevise} ======")
                    print("+++ Addition found +++")
                    print(addition)
                    print("+++ Addition found +++")
                    while True:
                        userinput = input("Accept addition? Y/N/Q/y/n/q: ")
                        if not userinput.isalpha():
                            self.zprint("Invalid input. Try again.")
                            continue

                        if userinput == "Y" or userinput == "y":
                            self.zprint("Addition accepted.")
                            print()
                            revisedfiletext += addition
                            self.modified = True
                            break
                        elif userinput == "N" or userinput == "n":
                            self.zprint("Ignored.")
                            break
                        elif userinput == "Q" or userinput == "q":
                            if self.modified:
                                while True:
                                    savepartial = input("Save partial file? Y/N/y/n: ")
                                    if not savepartial.isalpha():
                                        self.zprint("Invalid input." + " Try again.")
                                        continue

                                    if savepartial == "Y" or savepartial == "y":
                                        revisedfiletext += filetext[head:]
                                        outputfile = open(filetorevise, "w")
                                        outputfile.write(revisedfiletext)
                                        outputfile.close()
                                        self.modifiedfiles += [filetorevise]
                                        break
                                    elif savepartial == "N" or savepartial == "n":
                                        self.zprint("Discarding changes.")
                                        break
                                    else:
                                        self.zprint("Invalid input. " + "Try again.")

                            self.remove_preamble()
                            self.generate_pdf("accepted")
                            self.save_changes()
                        else:
                            self.zprint("Invalid input. Try again.")
                    head = self.rxAddend.search(filetext[tail:]).end() + tail
                    tail = head

            outputfile = open(filetorevise, "w")
            outputfile.write(revisedfiletext)
            outputfile.close()
            self.modifiedfiles += [filetorevise]
            self.zprint(f"File {filetorevise} revised and saved.")
            self.filelist.remove(filetorevise)

        # Only remove preamble when all files have been modified, otherwise,
        # the pdf won't generate properly - no latexdiff commands will function
        # without the preamble
        self.remove_preamble()
        self.generate_pdf("accepted")
        self.save_changes()

    def clean(self, args):
        """
        Remove all branches created by Zaphod.
        """
        self.zprint("Getting branch list.")
        command = self.gitBranchCommand
        ps = subprocess.check_output(command)

        branches = ps.decode("ascii").split("\n")
        zaphodBranches = 0
        for line in branches:
            branchName = line.strip().replace("* ", "")
            if self.branchSpec in branchName:
                zaphodBranches += 1
                self.zprint(f"Found a zaphod branch: {branchName}")
                command = self.gitBranchDeleteCommand + [branchName]
                if self.optionsDict["yes"]:
                    self.zprint(f"Deleting branch {branchName}")
                    subprocess.call(command)
                else:
                    deletebranch = input("Delete branch? Y/y/N/n: ")
                    if deletebranch == "Y" or deletebranch == "y":
                        subprocess.call(command)
                    else:
                        self.zprint(f"Skipping branch {branchName}")

        if zaphodBranches == 0:
            self.zprint("No Zaphod branches found.")

    def remove_preamble(self):
        """Remove latexdiff preamble when all files have been revised."""
        # Confirm that no files now have annotations
        modifiedfiles = self.get_modified_latex_files()
        if len(modifiedfiles) == 0:
            self.zprint("All files have been revised.")
            self.zprint("Removing latexdiff preamble additions.")
            for filetorevise in self.modifiedfiles:
                with open(filetorevise, "r") as thisfile:
                    filetext = thisfile.read()

                # Replace preamble additions
                filetext = re.sub(
                    pattern=self.rPreamble, repl="", string=filetext, flags=re.DOTALL
                )

                outputfile = open(filetorevise, "w")
                outputfile.write(filetext)
                outputfile.close()
        else:
            self.zprint("Some files still have latexdiff annotations:")
            for i in range(0, len(modifiedfiles)):
                print(f"[{(i + 1)}] {modifiedfiles[i]}")
            print()

    def save_changes(self):
        """Commit changes."""
        if len(self.modifiedfiles) > 0:
            self.zprint("Following files have been revised (maybe partially):")
            for i in range(0, len(self.modifiedfiles)):
                print(f"[{(i + 1)}] {self.modifiedfiles[i]}")

            print()
            while True:
                savechanges = input("Commit current changes? Y/y/N/n: ")
                if savechanges == "y" or savechanges == "Y":
                    subprocess.call(self.gitAddCommand)
                    commitmessage = input("Enter commit message: ")

                    command = self.gitCommitCommand + [commitmessage]
                    subprocess.call(command)
                    self.zprint("Changes committed.\n")
                    break
                elif savechanges == "n" or savechanges == "N":
                    self.zprint("Exiting without committing.")
                    break
                else:
                    self.zprint("Invalid input. Please try again.")
        else:
            self.zprint("No files modified. Exiting.")

        sys.exit(0)

    def generate_pdf(self, filename):
        """Generate pdf file."""
        if len(self.modifiedfiles) > 0:
            while True:
                generatepdf = input("Generate pdf? Y/y/N/n: ")

                if generatepdf == "Y" or generatepdf == "y":
                    self.zprint("Removing temporary files")
                    command = (
                        self.latexmkCleanCommand
                        + ("-jobname=" + filename).split()
                        + [self.optionsDict["main"]]
                    )
                    try:
                        subprocess.check_call(command, cwd=self.optionsDict["subdir"])
                    except subprocess.CalledProcessError as E:
                        self.zprint("latexmk -c failed. Output below:")
                        if E.output:
                            print(E.output)
                        if E.stderr:
                            print(E.stderr)
                        return -1

                    if self.optionsDict["citations"]:
                        self.zprint("User has specified citations")
                        command = (
                            self.latexmkCommand
                            + self.bibFlag
                            + ("-jobname=" + filename).split()
                            + [self.optionsDict["main"]]
                        )
                    else:
                        command = (
                            self.latexmkCommand
                            + self.nobibFlag
                            + ("-jobname=" + filename).split()
                            + [self.optionsDict["main"]]
                        )
                    try:
                        subprocess.check_call(command, cwd=self.optionsDict["subdir"])
                    except subprocess.CalledProcessError as E:
                        self.zprint("pdflatex failed. Output below:")
                        if E.output:
                            print(E.output)
                        if E.stderr:
                            print(E.stderr)
                        return -1

                    self.zprint(
                        "PDF generated: "
                        + self.optionsDict["subdir"]
                        + "/"
                        + filename
                        + ".pdf"
                    )
                    break
                elif generatepdf == "N" or generatepdf == "n":
                    self.zprint("Not generating pdf.")
                    break
                else:
                    self.zprint("Invalid input. Please try again.")

    def get_latex_files(self):
        """Get list of files with extension .tex."""
        filelist = []
        for root, dirs, files in os.walk(self.optionsDict["subdir"]):
            for filename in fnmatch.filter(files, "*.tex"):
                if filename not in filelist:
                    filelist.append(os.path.join(root, filename))

        if not len(filelist) > 0:
            print("No tex files found in this directory", file=sys.stderr)
            sys.exit(-1)
        # print(filelist)
        return filelist

    def get_modified_latex_files(self):
        """Get list of files with latexdiff annotations."""
        filelist = []
        modified_filelist = []
        for root, dirs, files in os.walk(self.optionsDict["subdir"]):
            for filename in fnmatch.filter(files, "*.tex"):
                if filename not in filelist:
                    filelist.append(os.path.join(root, filename))

        if not len(filelist) > 0:
            print("No tex files found in this directory", file=sys.stderr)
            sys.exit(-1)

        for i in range(0, len(filelist)):
            filetorevise = filelist[i]

            with open(filetorevise, "r") as thisfile:
                filetext = thisfile.read()

            # Ignore preamble
            filetext = re.sub(
                pattern=self.rPreamble, repl="", string=filetext, flags=re.DOTALL
            )

            # Check for annotations
            del_start = 0
            delcheck = self.rxDelbegin.search(filetext[:])
            add_start = 0
            addcheck = self.rxAddbegin.search(filetext[:])
            if delcheck is None:
                del_start = len(filetext)
            else:
                del_start = delcheck.start()
            if addcheck is None:
                add_start = len(filetext)
            else:
                add_start = addcheck.start()

            # Only add to filelist if both aren't EOL (no latexdiff annotations
            # if they are)
            if not add_start == del_start:
                modified_filelist += [filetorevise]

        return modified_filelist

    def generate_rev_filenames(self, rev):
        """Rename files as required for diff."""
        revfilelist = []
        for filename in self.filelist:
            revname = filename[:-4] + "-" + rev + ".tex"
            revfilelist.append(revname)
        return revfilelist

    def setup(self):
        """Setup things."""
        self.parser = argparse.ArgumentParser(
            prog="zaphod",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self.usage_message,
            add_help=False,
        )

        self.parser.add_argument(
            "-h", "--help", action=_HelpAction, help="View subcommand help"
        )

        self.subparser = self.parser.add_subparsers(help="additional help")

        self.revise_parser = self.subparser.add_parser(
            "revise",
            help="Interactive revision\n",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="TIP: To accept all - switch to rev2 branch/revision.\n"
            + "TIP: To reject all - switch to rev1 branch/revision.\n"
            + "Yay! Git!",
        )
        self.revise_parser.set_defaults(func=self.revise)
        self.revise_parser.add_argument(
            "-m",
            "--main",
            action="store",
            default="main.tex",
            help="Name of main file. Only used to \
                                        generate final pdf with changes. \n\
                                        Default: main.tex",
        )
        self.revise_parser.add_argument(
            "-s",
            "--subdir",
            default=".",
            action="store",
            help="Name of subdirectory where main \
                                        file resides.\n\
                                        Default: .",
        )
        self.revise_parser.add_argument(
            "-c",
            "--citations",
            action="store_true",
            default=False,
            help="Document contains citations.\n\
                                        Will run pdflatex and bibtex as \
                                        required. \nDefault: False",
        )

        self.diff_parser = self.subparser.add_parser(
            "diff",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            help="Generate changes output",
        )
        self.diff_parser.set_defaults(func=self.diff)
        self.diff_parser.add_argument(
            "-r",
            "--rev1",
            default="master^",
            action="store",
            help="First revision to diff against",
        )
        self.diff_parser.add_argument(
            "-t",
            "--rev2",
            default="master",
            action="store",
            help="Second revision to diff with.",
        )
        self.diff_parser.add_argument(
            "-m",
            "--main",
            action="store",
            default="main.tex",
            help="Name of main file. Only used to \
                                      generate final pdf with changes. \n\
                                      Default: main.tex",
        )
        self.diff_parser.add_argument(
            "-s",
            "--subdir",
            default=".",
            action="store",
            help="Name of subdirectory where main \
                                      file resides.\n\
                                      Default: .",
        )
        self.diff_parser.add_argument(
            "-l",
            "--latexdiffopts",
            default="--type=UNDERLINE",
            action="store",
            help="Pass options to latexdiff. \
                                      Please read man latexdiff for \
                                      available options.\
                                      These must be enclosed in single quotes \
                                      to ensure they're passed to latexdiff \
                                      without any processing.\
                                      Default: --type=UNDERLINE",
        )
        self.diff_parser.add_argument(
            "-c",
            "--citations",
            action="store_true",
            default=True,
            help="Document contains citations.\n\
                                      Will add -bibtex to latexmk.\n\
                                      Default: True",
        )

        self.clean_parser = self.subparser.add_parser(
            "clean",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            help="Clean up Zaphod related branches\n",
        )
        self.clean_parser.set_defaults(func=self.clean)
        self.clean_parser.add_argument(
            "-y",
            "--yes",
            action="store_true",
            default=False,
            help="Assume yes \
                                       Please be careful when using \
                                       this option. \
                                       Default: False",
        )

    def check_setup(self):
        """Check if Git directory is clean."""
        command = "git status --porcelain".split()
        ps = subprocess.check_output(command)
        rpModified = re.compile(r"^\s*M")
        rpUntracked = re.compile(r"^\s*\?\?")

        if (
            rpModified.search(ps.decode("ascii")) is not None
            or rpUntracked.search(ps.decode("ascii")) is not None
        ):
            self.logger.error(
                "Modifed or untracked files found.\n"
                + "git status output:\n"
                + ps.decode("ascii")
                + "\nPlease stash or commit and rerun Zaphod.",
                file=sys.stderr,
            )
            sys.exit(-3)

        if (
            "subdir" in self.optionsDict
            and self.optionsDict["subdir"]
            and not os.path.isdir(self.optionsDict["subdir"])
        ):
            self.logger.error(
                f"Specified subdirectory not found at {self.optionsDict['subdir']}!\n"
                + "Please check your arguments.",
                file=sys.stderr,
            )
            sys.exit(-4)

        if (
            "main" in self.optionsDict
            and self.optionsDict["main"]
            and self.optionsDict["subdir"]
            and not os.path.isfile(
                os.path.join(self.optionsDict["subdir"], self.optionsDict["main"])
            )
        ):
            self.logger.error(
                f"Specified main file not found at {os.path.join(self.optionsDict['subdir'], self.optionsDict['main'])}!\n"
                + "Please check your arguments.",
                file=sys.stderr,
            )
            sys.exit(-4)

        for command in self.commandList:
            if not shutil.which(command):
                self.logger.error(command + " not found! Exiting!", file=sys.stderr)
                sys.exit(-5)

        if (
            "citations" in self.optionsDict
            and self.optionsDict["citations"]
            and not shutil.which("bibtex")
        ):
            self.logger.error("bibtex not found! Exiting!", file=sys.stderr)
            sys.exit(-6)

    def zprint(self, message):
        """Prepend all output messages with token."""
        print("[Zaphod] " + message)

    def run(self):
        """Main runner method."""
        if len(sys.argv) == 1:
            self.parser.print_help()
            sys.exit(1)

        self.options = self.parser.parse_args()
        self.optionsDict = vars(self.options)
        if len(self.optionsDict) != 0:
            # Check for latex files and get a list
            self.check_setup()
            #  print(self.optionsDict)
            self.options.func(self.options)


def cli():
    """Main cli runner"""
    runner_instance = Zaphod()
    runner_instance.setup()
    runner_instance.run()
    sys.exit(0)


if __name__ == "__main__":
    cli()
