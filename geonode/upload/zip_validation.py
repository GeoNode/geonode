#########################################################################
#
# Copyright (C) 2026 OSGeo
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

"""
Safety checks for uploaded zip archives (zip, kmz, xlsx, ...).

The upload handler's libmagic check rejects PE-prefixed self-extracting
archives, but legitimate zip archives can still carry path-traversal entries,
symlinks, or zip-bomb compression ratios. This module inspects the central
directory without extracting anything, and raises ZipValidationError on any
hostile structure.
"""

import os
import posixpath
import stat
import zipfile


MAX_ENTRIES = 10_000
MAX_TOTAL_UNCOMPRESSED = 2 * 1024 * 1024 * 1024  # 2 GiB
MAX_COMPRESSION_RATIO = 100
MIN_COMPRESSED_FOR_RATIO_CHECK = 1024  # bytes; ratios are meaningless below this


class ZipValidationError(Exception):
    """Raised when an uploaded archive fails a safety check."""


def validate_safe_zip(source):
    """
    Inspect an uploaded zip archive.

    source: filesystem path (str / os.PathLike) or a file-like object opened
    in binary mode and seekable.

    Raises ZipValidationError on any unsafe entry. Returns None on success.
    """
    try:
        with zipfile.ZipFile(source) as zf:
            infos = zf.infolist()
    except zipfile.BadZipFile as exc:
        raise ZipValidationError(f"Not a valid zip archive: {exc}") from exc

    if len(infos) > MAX_ENTRIES:
        raise ZipValidationError(f"Archive has {len(infos)} entries (max {MAX_ENTRIES}).")

    total_uncompressed = 0
    for info in infos:
        _check_entry_name(info.filename)
        _check_not_symlink(info)
        total_uncompressed += info.file_size
        if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
            raise ZipValidationError(f"Archive decompresses to more than {MAX_TOTAL_UNCOMPRESSED} bytes.")
        _check_compression_ratio(info)


def _check_entry_name(name):
    if not name:
        raise ZipValidationError("Archive contains an entry with an empty name.")
    if "\x00" in name:
        raise ZipValidationError("Archive contains an entry name with a NUL byte.")
    # Reject absolute paths (POSIX and Windows) and drive letters.
    if name.startswith(("/", "\\")) or (len(name) >= 2 and name[1] == ":"):
        raise ZipValidationError(f"Absolute path in archive entry: {name!r}.")
    # Reject traversal in any segment once we normalise separators.
    normalised = name.replace("\\", "/")
    parts = normalised.split("/")
    if any(part == ".." for part in parts):
        raise ZipValidationError(f"Path traversal in archive entry: {name!r}.")
    # Belt-and-braces: after posix normpath, the result must not escape.
    resolved = posixpath.normpath(normalised)
    if resolved.startswith("../") or resolved == "..":
        raise ZipValidationError(f"Path traversal in archive entry: {name!r}.")


def _check_not_symlink(info):
    # Zip stores Unix mode in the top 16 bits of external_attr.
    unix_mode = info.external_attr >> 16
    if unix_mode and stat.S_ISLNK(unix_mode):
        raise ZipValidationError(f"Archive contains a symlink entry: {info.filename!r}.")


def _check_compression_ratio(info):
    if info.compress_size < MIN_COMPRESSED_FOR_RATIO_CHECK:
        return
    if info.file_size == 0:
        return
    ratio = info.file_size / max(info.compress_size, 1)
    if ratio > MAX_COMPRESSION_RATIO:
        raise ZipValidationError(
            f"Entry {info.filename!r} has a suspicious compression ratio " f"({ratio:.0f}x); possible zip bomb."
        )


def is_zip_extension(filename):
    """Return True if the filename suggests a zip-based upload we should inspect."""
    if not filename:
        return False
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    return ext in {"zip", "kmz", "xlsx"}
