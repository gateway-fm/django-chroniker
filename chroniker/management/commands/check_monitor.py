import sys
from django.core.management.base import BaseCommand
from chroniker.models import get_current_job
from django.apps import apps


class Command(BaseCommand):
    help = "Runs a specific monitoring routine."

    def add_arguments(self, parser):
        parser.add_argument("model", help="Model in the format app_label.ModelName")
        parser.add_argument(
            "--filter",
            dest="filter",
            help="Django ORM filter string, e.g., name=John,active=True",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Show verbose output"
        )

    def handle(self, *args, **options):
        model_path = options["model"]
        filter_arg = options.get("filter")
        verbose = options["verbose"]

        try:
            app_label, model_name = model_path.split(".")
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError) as e:
            self.stderr.write(f"Invalid model: {model_path}. Error: {e}")
            return

        filters = {}
        if filter_arg:
            try:
                for part in filter_arg.split(","):
                    key, value = part.split("=")
                    # Convert basic types
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    filters[key] = value
            except ValueError:
                self.stderr.write(
                    "Invalid filter format. Expected key=value,key2=value2"
                )
                return

        if verbose:
            print(f"Filtering {model} with: {filters}")

        q = model.objects.filter(**filters)

        job = get_current_job()
        if job:
            job.monitor_records = q.count()
            job.save()

        output = f"{q.count()} records require attention."
        print(output, file=sys.stderr if q.exists() else sys.stdout)
