Zaphod
------

A LaTeX change tracking tool.

.. image:: https://img.shields.io/github/license/sanjayankur31/zaphod.svg
    :target: https://github.com/sanjayankur31/zaphod/blob/master/LICENSE
    :alt: GPLv3 Licensed

.. image:: https://img.shields.io/github/release/sanjayankur31/zaphod.svg
    :target: https://github.com/sanjayankur31/zaphod/releases
    :alt: Releases

.. image:: https://img.shields.io/github/issues/sanjayankur31/zaphod.svg
    :target: https://github.com/sanjayankur31/zaphod/issues
    :alt: Issues


The name
========

Zaphod Beeblebrox is a fictional character in the various versions of the
humorous science fiction story The Hitchhiker's Guide to the Galaxy by Douglas
Adams.

The tool
========

A wrapper around `latexdiff <https://github.com/ftilmann/latexdiff>`__ that
recursively checks changes in LaTeX sources between two Git revisions and
generates a nice annotated PDF in a new Git branch. This Git branch sits on top
of the newer revision - after one has accepted/rejected changes, one can remove
the annotations and simply commit and merge to the master branch - a nice workflow.

It is rather simple at the moment and probably has heaps of issues. Feel free to
modify it to suit your purposes and open pull requests.

Here is a test repository with LaTeX sources and a resultant
latexdiff-annotated branch to play with:
https://github.com/sanjayankur31/latex-changes

Usage
=====

.. code:: bash

    usage: zaphod [-h] {revise,diff,clean} ...

    positional arguments:
      {revise,diff,clean}  additional help
        revise             Interactive revision
        diff               Generate changes output
        clean              Clean up Zaphod related branches

    optional arguments:
      -h, --help     View subcommand help

    NOTES:
        The idea of this program is to help LaTeX users track, review, and
        see changes that have been made in their source files. The script
        only works when git is used as a version control system.

    Expected workflow:
        - Make changes, commit
        - Run this program:
            It will generate a pdf with differences between the two
            provided Git revisions using latexdiff. It will also commit the
            annotated TeX sources in a new Git branch called "changes".
            - Review commits using generated PDF.
            - Accept/ignore changes.
            - Commit once finished.
            - Merge to master branch.
            - Profit.

    Requires:
        - latexdiff
        - Git
        - pdflatex
        - latexmk
        - bibtex or biber
        - Python3


    Subcommand: 'revise'
    usage: zaphod revise [-h] [-m MAIN] [-s SUBDIR]

    optional arguments:
      -h, --help            show this help message and exit
      -m MAIN, --main MAIN  Name of main file. Only used to generate final pdf
                            with changes.
                            Default: main.tex
      -s SUBDIR, --subdir SUBDIR
                            Name of subdirectory where main file resides.
                            Default: .
      -c, --citations       Document contains citations. Will run pdflatex and
                            bibtex as required. Default: False

    TIP: To accept all - switch to rev2 branch/revision.
    TIP: To reject all - switch to rev1 branch/revision.
    Yay! Git!

    Subcommand: 'diff'
    usage: zaphod diff [-h] [-r REV1] [-t REV2] [-m MAIN] [-s SUBDIR] [-l LATEXDIFFOPTS] [-c]

    optional arguments:
      -h, --help            show this help message and exit
      -r REV1, --rev1 REV1  First revision to diff against
      -t REV2, --rev2 REV2  Second revision to diff with.
      -m MAIN, --main MAIN  Name of main file. Only used to generate final pdf
                            with changes. Default: main.tex

      -s SUBDIR, --subdir SUBDIR
                            Name of subdirectory where main file resides.
                            Default: .

      -l LATEXDIFFOPTS, --latexdiffopts LATEXDIFFOPTS
                            Pass options to latexdiff. Please read man
                            latexdiff for available options. These must be
                            enclosed in single quotes to ensure they are passed
                            to latexdiff without any processing.
                            Default: --type=UNDERLINE

      -c, --citations       Document contains citations. Will add -bibtex to
                            latexmk.
                            Default: True


    Subcommand: 'clean'
    usage: zaphod clean [-h] [-y]

    optional arguments:
      -h, --help  show this help message and exit
      -y, --yes   Assume yes Please be careful when using this option. Default: False
