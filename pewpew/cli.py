# -*- coding: utf-8 -*-

import click
import logging


@click.group()
def main(files=None):
    """ Common utilites for pewpew generated files
    """
    logging.basicConfig(level=logging.INFO)


@main.command()
def combine():
    """ for an input list of files, create a single output stream
    """
    pass


@main.command()
def dump():
    """
    """
    pass


if __name__ == "__main__":
    main()
