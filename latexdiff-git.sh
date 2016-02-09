#!/bin/bash

# Copyright 2016 Ankur Sinha 
# Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com> 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# File : latexdiff-git.sh
# It appears that the --flatten option in latexdiff doesn't work with revision control for some reason. I'm not entirely sure why this is. 
# http://tex.stackexchange.com/questions/61405/latexdiff-svn-not-working-with-multiple-files-flatten
# Therefore, the workaround seems to be to scriptify it.

GITREPO=""
MAINFILE="main.tex"
SUBDIR="."
REV1FILE="rev1-main.tex"
REV2FILE="rev2-main.tex"
LATEXPANDFOUND="no"
LATEXDIFFFOUND="no"
GITFOUND="no"
PDFLATEXFOUND="no"
LATEXPANDPATH="/usr/bin/latexpand"
LATEXDIFFPATH="/usr/bin/latexdiff"
PDFLATEXPATH="/usr/bin/pdflatex"
GITPATH="/usr/bin/git"
REV1="master^"
REV2="master"
LOGFILE=""
CITATIONS="no"
BIBTEXFOUND="no"
BIBTEXPATH="/usr/bin/bibtex"
EXCLUDECOMMANDS="no"

function main ()
{
    TEMPDIR=$(mktemp -d)
    CLONEDIR="$TEMPDIR/tempclone"

    GITREPO=$(pwd)
    DIFFNAME="diff-$REV1-$REV2"
    LOGFILE="$TEMPDIR/$DIFFNAME"".log"

    pushd "$TEMPDIR" >> $LOGFILE 2>&1
        echo "Cloning repository $GITREPO"
        echo "Cloning repository $GITREPO" >> $LOGFILE
        git clone "$GITREPO" "$CLONEDIR" >> $LOGFILE 2>&1

        echo "Working ..."
        pushd "$CLONEDIR/$SUBDIR" >> $LOGFILE 2>&1
            git reset HEAD --hard >> $LOGFILE 2>&1
            git checkout -b temp-head-1 "$REV1" >> $LOGFILE 2>&1
            latexpand "$MAINFILE" -o "$REV1FILE"

            git checkout -b temp-head-2 "$REV2" >> $LOGFILE 2>&1
            latexpand "$MAINFILE" -o "$REV2FILE"

            if [ "no" == "$EXCLUDECOMMANDS" ]; then
                latexdiff --type=UNDERLINE "$REV1FILE" "$REV2FILE" > "$DIFFNAME"".tex"
            else
                latexdiff --type=UNDERLINE --exclude-textcmd="\"$EXCLUDECOMMANDS\"" "$REV1FILE" "$REV2FILE" > "$DIFFNAME"".tex"
            fi

            pdflatex -interaction batchmode "$DIFFNAME"".tex" >> $LOGFILE 2>&1
            if [ "yes" == "$CITATIONS" ]; then
                echo "Processing citations."
                echo "Processing citations." >> $LOGFILE 2>&1
                bibtex "$DIFFNAME"".tex" >> $LOGFILE 2>&1
                pdflatex -interaction batchmode "$DIFFNAME"".tex" >> $LOGFILE 2>&1
                pdflatex -interaction batchmode "$DIFFNAME"".tex" >> $LOGFILE 2>&1
            fi
            echo "Moving resultant tex and pdf to $GITREPO"
            mv "$DIFFNAME"".tex" "$GITREPO" -v >> $LOGFILE 2>&1
            mv "$DIFFNAME"".pdf" "$GITREPO" -v >> $LOGFILE 2>&1
        popd >> $LOGFILE 2>&1
    popd >> $LOGFILE 2>&1
    echo "Cleaning up"
    echo "Cleaning up" >> $LOGFILE 2>&1
    echo "DONE" >> $LOGFILE 2>&1
    mv $LOGFILE $GITREPO -v
    rm -fr "$TEMPDIR"
    echo "DONE"
}

function check_requirements ()
{
    if [ -x "$LATEXPANDPATH" ]; then
        LATEXPANDFOUND="yes"
    fi
    if [ -x "$LATEXDIFFPATH" ]; then
        LATEXDIFFFOUND="yes"
    fi
    if [ -x "$GITPATH" ]; then
        GITFOUND="yes"
    fi
    if [ -x "$PDFLATEXPATH" ]; then
        PDFLATEXFOUND="yes"
    fi

    if [ -x "$BIBTEXPATH" ] ; then
        BIBTEXFOUND="yes"
    fi

    if [ "yes" == "$LATEXPANDFOUND" ] &&  [ "yes" == "$LATEXDIFFFOUND" ] && [ "yes" == "$GITFOUND" ] && [ "yes" == "$PDFLATEXFOUND" ]; then
        echo "Found required binaries. Continuing."
    else
        echo "Did not find required binaries. Please check that latexpand, latexdiff, pdflatex and git are installed and the paths they're installed at are set correctly in the script."
        return -1
    fi

    if [ "yes" == "$CITATIONS" ] && [ "yes" == "$BIBTEXFOUND" ]; then
        echo "Bibtex found. Citations will be processed."
    else
        echo "Could not find Bibtex. Citations will not be processed."
        CITATIONS="no"
    fi
}

usage ()
{
    cat << EOF
    usage: $0 options

    This script generates a pdf diff from two git commits in the working directory.
    To be run in the root of the git repo.

    It's a very simple script. If it doesn't work, you're doing something wrong ;)

    latexdiff itself provides various output options. Please read the latexdiff manpage for more information.

    OPTIONS:
    -h  Show this message

    -m  Main file to be converted (in case of includes and so on). 
        Default: main.tex

    -s  Subdirectory which contains tex files. 
        Default: .

    -r  Revision 1 
        Default: HEAD~1

    -t  Revision 2 
        Default: HEAD

    -c  Process citations and bibliography
        Default: no

    -e  A list of latex commands to ignore
        Passes a list of commands to latexdiff to ignore. Read the latexdiff
        man page for more details on --exclude-textcmd
        Default:
        Suggested: -e "section,subsection"
        http://tex.stackexchange.com/a/88377/11281

    NOTES:
    Please use shortcommit references as far as possible since pdflatex and so
    on have difficulties with special characters in filenames - ~, ^ etc. may
    not always work. If they don't, look at the script output to understand
    why.

    In general, anything that can be checked out should work - branch names,
    tags, commits.

EOF
}

while getopts "hm:s:r:t:ce:" OPTION
do
    case $OPTION in
        h)
            usage
            exit 0
            ;;
        m) 
            MAINFILE=$OPTARG
            ;;
        s)
            SUBDIR=$OPTARG
            ;;
        r)
            REV1=$OPTARG
            ;;
        t)
            REV2=$OPTARG
            ;;
        c)
            CITATIONS="yes"
            ;;
        e)
            EXCLUDECOMMANDS=$OPTARG
            ;;
        ?)
            usage
            exit 0
            ;;
    esac
done

if [ "$#" -eq 0 ]; then
    usage
    exit 0
fi
check_requirements
main
