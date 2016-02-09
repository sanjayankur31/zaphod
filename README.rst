latexdiff-git
-------------

A simple script that generates a nice pdf with changes between two git commits.
Only works for git. Written because latexdiff-vc --flatten doesn't seem to find
differences in the included tex files.

    usage: latexdiff-git [-h] {revise,diff} ...

    positional arguments:
      {revise,diff}  additional help
        revise       Interactive revision (UNIMPLEMENTED)
        diff         Generate changes output

    optional arguments:
      -h, --help     View subcommand help

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


    Subcommand: 'revise'
    usage: latexdiff-git revise [-h]

    optional arguments:
      -h, --help  show this help message and exit

    NOTE: This feature is not yet implemented.

    Subcommand: 'diff'
    usage: latexdiff-git diff [-h] [-r REV1] [-t REV2] [-m MAIN] [-s SUBDIR]

    optional arguments:
      -h, --help            show this help message and exit
      -r REV1, --rev1 REV1  First revision to diff against
      -t REV2, --rev2 REV2  Second revision to diff with.
      -m MAIN, --main MAIN  Name of main file. Only used to generate final pdf
                            with changes. Default: main.tex
      -s SUBDIR, --subdir SUBDIR
                            Name of subdirectory where main file resides. Default:

