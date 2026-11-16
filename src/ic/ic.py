import click

from ic.cli.clean_hosts import clean_hosts
from ic.cli.evaluate import evaluate
from ic.cli.fetch import fetch
from ic.cli.geocode import geocode
from ic.cli.merge import merge
from ic.cli.process_llm import process_llm
from ic.cli.stats import stats
from ic.cli.upload_postgresql import upload_postgresql
from ic.cli.upload_opensearch import upload_opensearch


@click.group()
def main():
    """
    Imprints Collection

    Collecting impressum pages from German websites.
    """
    pass


main.add_command(fetch)
main.add_command(merge)
main.add_command(clean_hosts)
main.add_command(process_llm)
main.add_command(geocode)
main.add_command(evaluate)
main.add_command(stats)
main.add_command(upload_postgresql)
main.add_command(upload_opensearch)


if __name__ == "__main__":
    main()
