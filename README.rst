latex-changes
-------------

A simple script that generates a nice pdf with changes between two git commits.
Only works for git. Written because latexdiff-vc --flatten doesn't seem to find
differences in the included tex files.


    usage: ./latexdiff-git.sh options

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

