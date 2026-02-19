import os

import click

from ic.utils.filter_utils import check_url
from ic.config import *


@click.command()
@click.argument("input_file_path", type=click.Path(exists=True, dir_okay=False))
def clean_hosts(input_file_path: str):
    """
    Clean up the list of hosts by removing duplicates and unwanted entries.
    """
    with open(input_file_path, "r", encoding="UTF-8") as f:
        hosts = [line.lower().strip() for line in f.readlines()]
        click.echo(f"Loaded {len(hosts)} hosts from file")

    hosts = set(hosts)
    click.echo(f"Loaded {len(hosts)} unique hosts from file")

    # Filter hosts
    hosts = [host for host in hosts if check_url(host, is_host=True)]
    click.echo(f"{len(hosts)} hosts after filtering")

    # Count PLDs
    plds = {}
    for host in hosts:
        pld = host.split(".")[-2] + "." + host.split(".")[-1]
        if pld not in plds:
            plds[pld] = 0
        plds[pld] += 1

    click.echo(f"{len(plds)} unique PLDs")
    click.echo("PLD counts:")
    for pld, count in sorted(plds.items(), key=lambda item: item[1], reverse=True):
        if count < 100:
            break
        click.echo(f"{pld}: {count}")

    # Sort hosts for consistent processing order
    hosts = sorted(hosts)

    # Save in file
    new_file_path = input_file_path.replace(".txt", "_cleaned.txt")
    with open(
        new_file_path,
        "w",
        encoding="UTF-8",
    ) as f:
        for host in hosts:
            f.write(host + "\n")

    click.echo("Done")
