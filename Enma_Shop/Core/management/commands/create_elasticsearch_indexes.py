import time
from django.core.management.base import BaseCommand
from elasticsearch import ConnectionError, TransportError
from Core.utils.elasticsearch.indexes import create_all_indexes


class Command(BaseCommand):
    help = "Create Elasticsearch indexes if they do not exist."

    def add_arguments(self, parser):
        parser.add_argument(
            "--retries",
            type=int,
            default=30,
            help="Number of retries while waiting for Elasticsearch.",
        )
        parser.add_argument(
            "--sleep",
            type=int,
            default=2,
            help="Seconds to sleep between retries.",
        )

    def handle(self, *args, **options):
        retries = options["retries"]
        sleep = options["sleep"]
        for attempt in range(1, retries + 1):
            try:
                create_all_indexes()
                self.stdout.write(
                    self.style.SUCCESS(
                        "Elasticsearch indexes checked/created successfully."
                    )
                )
                return

            except (ConnectionError, TransportError) as exc:
                self.stdout.write(
                    self.style.WARNING(
                        f"Elasticsearch is not ready yet. "
                        f"Attempt {attempt}/{retries}. Error: {exc}"
                    )
                )
                if attempt == retries:
                    raise
                time.sleep(sleep)
