from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from geonode.base.management.command_utils import setup_logger
from geonode.base.management.commands.thesaurus_subcommands.dump import dump_thesaurus, DUMP_FORMATS
from geonode.base.management.commands.thesaurus_subcommands.list import list_thesauri
from geonode.base.management.commands.thesaurus_subcommands.load import load_thesaurus, ACTIONS, ACTION_CREATE

logger = setup_logger()

COMMAND_LIST = "list"
COMMAND_DUMP = "dump"
COMMAND_LOAD = "load"
COMMANDS = [COMMAND_LIST, COMMAND_LOAD, COMMAND_DUMP]


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
            default="pretty-xml",
            choices=DUMP_FORMATS,
            help="Format string supported by rdflib (default: pretty-xml)",
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

        else:
            raise CommandError(f"Unknown subcommand: {subcommand}")
