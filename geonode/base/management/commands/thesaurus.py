import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from geonode.base.management.command_utils import setup_logger
from geonode.base.management.commands.thesaurus_subcommands.dump import (
    dump_thesaurus,
    DUMP_FORMATS,
    DUMP_FORMAT_DEFAULT,
    DUMP_FORMAT_SORTED,
)
from geonode.base.management.commands.thesaurus_subcommands.list import list_thesauri
from geonode.base.management.commands.thesaurus_subcommands.load import load_thesaurus, ACTIONS, ACTION_CREATE, ACTION_UPDATE

logger = setup_logger()

COMMAND_LIST = "list"
COMMAND_DUMP = "dump"
COMMAND_LOAD = "load"
COMMAND_AUTOLOAD = "autoload"
COMMANDS = [COMMAND_LIST, COMMAND_LOAD, COMMAND_DUMP, COMMAND_AUTOLOAD]


class Command(BaseCommand):
    help = f"Handles thesaurus commands {COMMANDS}"

    def add_arguments(self, parser):
        parser.add_argument("subcommand", nargs="?", choices=COMMANDS, help="thesaurus operation to run")

        common_group = parser.add_argument_group("Common params")
        common_group.add_argument(
            "-i",
            "--identifier",
            nargs="?",
            help="Thesaurus identifier. \nDump: required.\nLoad: optional - if omitted will be created out of the filename ",
        )

        load_group = parser.add_argument_group('Params for "load" subcommand')
        load_group.add_argument("-f", "--file", nargs="?", help="Full path to a thesaurus in RDF format")
        load_group.add_argument(
            "--action",
            default=ACTION_CREATE,
            choices=ACTIONS,
            help="Actions to run upon data loading (default: create)",
        )

        dump_group = parser.add_argument_group('Params for "dump" subcommand')
        dump_group.add_argument("-o", "--out", nargs="?", help="Full path to the output file to be created")
        dump_group.add_argument(
            "--include",
            dest="include",
            action="append",
            help="Inclusion filter (wildcard is * as suffix or prefix); can be repeated",
        )
        dump_group.add_argument(
            "--exclude",
            dest="exclude",
            action="append",
            help="Exclusion filter (wildcard is * as suffix or prefix); can be repeated",
        )
        dump_group.add_argument(
            "--format",
            dest="format",
            default=DUMP_FORMAT_DEFAULT,
            choices=DUMP_FORMATS,
            help=f"Format string supported by rdflib, or {DUMP_FORMAT_SORTED} (default: {DUMP_FORMAT_DEFAULT})",
        )
        def_lang = getattr(settings, "THESAURUS_DEFAULT_LANG", None)
        dump_group.add_argument(
            "--default-lang",
            dest="lang",
            default=def_lang,
            help=f"Default language code for untagged string literals (default: {def_lang})",
        )

    def handle(self, *args, **options):
        subcommand = options["subcommand"]
        logger.info("THESAURUS COMMAND INIT")

        if not subcommand:
            logger.warning("Missing thesaurus subcommand.")
            self.print_help("manage.py", "thesaurus")

        elif subcommand == COMMAND_LIST:
            list_thesauri()

        elif subcommand == COMMAND_DUMP:
            identifier = options.get("identifier")
            include = options.get("include") or []
            exclude = options.get("exclude") or []
            output_file = options.get("out")
            format = options.get("format")
            lang = options.get("lang")

            if not identifier:
                raise CommandError("'dump' command requires the <identifier> parameter.")

            dump_thesaurus(identifier, format, lang, include, exclude, output_file)

        elif subcommand == COMMAND_LOAD:
            input_file = options.get("file")
            action = options.get("action")
            identifier = options.get("identifier")

            if not input_file:
                raise CommandError("'load' command requires the <file> parameter.")

            if not action:
                action = ACTION_CREATE
                logger.info(f"Missing action param: setting actions as '{action}'")

            load_thesaurus(input_file, identifier, action)

        elif subcommand == COMMAND_AUTOLOAD:
            autoload_thesauri()

        else:
            raise CommandError(f"Unknown subcommand: {subcommand}")


def autoload_thesauri():
    """
    Discover and load all thesauri (.rdf files) found in a `thesauri/` directory
    within each installed Django app. Uses the `update` action so existing entries
    are updated and new ones are created without duplicates.
    """
    loaded = 0
    for app_config in apps.get_app_configs():
        thesauri_dir = os.path.join(app_config.path, "thesauri")
        if not os.path.isdir(thesauri_dir):
            continue
        rdf_files = [f for f in os.listdir(thesauri_dir) if f.lower().endswith(".rdf")]
        for rdf_file in sorted(rdf_files):
            rdf_path = os.path.join(thesauri_dir, rdf_file)
            logger.info(f"Autoloading thesaurus from app '{app_config.name}': {rdf_path}")
            try:
                load_thesaurus(rdf_path, identifier=None, action=ACTION_UPDATE)
                loaded += 1
            except Exception as e:
                logger.error(f"Failed to load thesaurus '{rdf_path}': {e}")
    logger.info(f"Autoload complete: {loaded} thesaurus file(s) loaded.")
