# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2022 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import argparse
import json
import logging
import os
import random
import re
import string
import sys
import ast

dir_path = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def shuffle(chars):
    chars_as_list = list(chars)
    random.shuffle(chars_as_list)
    return "".join(chars_as_list)

_simple_chars = shuffle(string.ascii_letters + string.digits)
_strong_chars = shuffle(string.ascii_letters + string.digits + "#%*._~")

def generate_env_file(args):
    # validity checks
    if not os.path.exists(args.sample_file):
        logger.error(f"File does not exists {args.sample_file}")
        raise FileNotFoundError

    if args.file and not os.path.isfile(args.file):
        logger.error(f"File does not exists: {args.file}")
        raise FileNotFoundError

    if args.https and not args.email:
        raise Exception("With HTTPS enabled, the email parameter is required")

    _sample_file = None
    with open(args.sample_file, "r+") as sample_file:
        _sample_file = sample_file.read()

    if not _sample_file:
        raise Exception("Sample file is empty!")

    def _get_vals_to_replace(args):
        _config = ["sample_file", "file", "env_type", "https", "email"]
        _jsfile = {}
        if args.file:
            with open(args.file) as _json_file:
                _jsfile = json.load(_json_file)

        _vals_to_replace = {key: _jsfile.get(key, val) for key, val in vars(args).items() if key not in _config}
        tcp = "https" if ast.literal_eval(f"{_jsfile.get('https', args.https)}".capitalize()) else "http"

        _vals_to_replace["public_port"] = (
            "443" if ast.literal_eval(f"{_jsfile.get('https', args.https)}".capitalize()) else "80"
        )
        _vals_to_replace["http_host"] = _jsfile.get("hostname", args.hostname) if tcp == "http" else ""
        _vals_to_replace["https_host"] = _jsfile.get("hostname", args.hostname) if tcp == "https" else ""

        _vals_to_replace["siteurl"] = f"{tcp}://{_jsfile.get('hostname', args.hostname)}"
        _vals_to_replace["secret_key"] = _jsfile.get("secret_key", args.secret_key) or "".join(
            random.choice(_strong_chars) for _ in range(50)
        )
        _vals_to_replace["letsencrypt_mode"] = (
            "disabled"
            if not _vals_to_replace.get("https_host")
            else "staging"
            if _jsfile.get("env_type", args.env_type) in ["test"]
            else "production"
        )
        _vals_to_replace["debug"] = False if _jsfile.get("env_type", args.env_type) in ["prod", "test"] else True
        _vals_to_replace["email"] = _jsfile.get("email", args.email)

        if tcp == "https" and not _vals_to_replace["email"]:
            raise Exception("With HTTPS enabled, the email parameter is required")

        return {**_jsfile, **_vals_to_replace}

    for key, val in _get_vals_to_replace(args).items():
        _val = val or "".join(random.choice(_simple_chars) for _ in range(15))
        if isinstance(val, bool) or key in ["email", "http_host", "https_host"]:
            _val = str(val)
        _sample_file = re.sub(
            "{" + key + "}",
            lambda _: _val,
            _sample_file,
        )

    with open(f"{dir_path}/.env", "w+") as output_env:
        output_env.write(_sample_file)
    logger.info(f".env file created: {dir_path}/.env")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ENV file builder",
        description="Tool for generate environment file automatically. The information can be passed or via CLI or via JSON file ( --file /path/env.json)",
        usage="python create-envfile.py localhost -f /path/to/json/file.json",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--noinput",
        "--no-input",
        action="store_false",
        dest="confirmation",
        help=("skips prompting for confirmation."),
    )
    parser.add_argument(
        "-hn",
        "--hostname",
        help=f"Host name, default localhost",
        default="localhost",
    )

    # expected path as a value
    parser.add_argument(
        "-sf",
        "--sample_file",
        help=f"Path of the sample file to use as a template. Default is: {dir_path}/.env.sample",
        default=f"{dir_path}/.env.sample",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="absolute path of the file with the configuration. Note: we expect that the keys of the dictionary have the same name as the CLI params",
    )
    # booleans
    parser.add_argument("--https", action="store_true", default=False, help="If provided, https is used")
    # strings
    parser.add_argument("--email", help="Admin email, this field is required if https is enabled")

    parser.add_argument("--geonodepwd", help="GeoNode admin password")
    parser.add_argument("--geoserverpwd", help="Geoserver admin password")
    parser.add_argument("--pgpwd", help="PostgreSQL password")
    parser.add_argument("--dbpwd", help="GeoNode DB user password")
    parser.add_argument("--geodbpwd", help="Geodatabase user password")
    parser.add_argument("--clientid", help="Oauth2 client id")
    parser.add_argument("--clientsecret", help="Oauth2 client secret")
    parser.add_argument("--secret_key", help="Django Secret Key")

    parser.add_argument(
        "--env_type",
        help="Development/production or test",
        choices=["prod", "test", "dev"],
        default="prod",
    )

    args = parser.parse_args()

    if not args.confirmation:
        generate_env_file(args)
    else:
        overwrite_env = input("This action will overwrite any existing .env file. Do you wish to continue? (y/n)")
        if overwrite_env not in ["y", "n"]:
            logger.error("Please enter a valid response")
        if overwrite_env == "y":
            generate_env_file(args)
