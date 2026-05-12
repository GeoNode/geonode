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

"""unit tests for geonode.upload.zip_validation"""

import io
import stat
import zipfile

from django.test import SimpleTestCase

from geonode.upload.zip_validation import (
    MAX_ENTRIES,
    ZipValidationError,
    is_zip_extension,
    validate_safe_zip,
)


def _make_zip(entries):
    """entries: iterable of (arcname, bytes, [ZipInfo overrides dict])."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in entries:
            if len(entry) == 3:
                arcname, data, overrides = entry
            else:
                arcname, data = entry
                overrides = None
            info = zipfile.ZipInfo(arcname)
            info.compress_type = zipfile.ZIP_DEFLATED
            if overrides:
                for key, value in overrides.items():
                    setattr(info, key, value)
            zf.writestr(info, data)
    buf.seek(0)
    return buf


class ValidateSafeZipTests(SimpleTestCase):
    def test_accepts_clean_archive(self):
        buf = _make_zip([("tileset.json", b'{"asset": {"version": "1.0"}}'), ("content/0.b3dm", b"x" * 128)])
        validate_safe_zip(buf)  # should not raise

    def test_rejects_absolute_path_entry(self):
        buf = _make_zip([("/etc/passwd", b"root:x:0:0")])
        with self.assertRaises(ZipValidationError) as ctx:
            validate_safe_zip(buf)
        self.assertIn("Absolute path", str(ctx.exception))

    def test_rejects_windows_absolute_path(self):
        buf = _make_zip([("C:/evil.txt", b"payload")])
        with self.assertRaises(ZipValidationError) as ctx:
            validate_safe_zip(buf)
        self.assertIn("Absolute path", str(ctx.exception))

    def test_rejects_path_traversal(self):
        buf = _make_zip([("../../etc/passwd", b"payload")])
        with self.assertRaises(ZipValidationError) as ctx:
            validate_safe_zip(buf)
        self.assertIn("traversal", str(ctx.exception))

    def test_rejects_traversal_in_middle_segment(self):
        buf = _make_zip([("a/../../b.txt", b"payload")])
        with self.assertRaises(ZipValidationError) as ctx:
            validate_safe_zip(buf)
        self.assertIn("traversal", str(ctx.exception))

    def test_rejects_nul_byte_in_name(self):
        # Python's zipfile silently strips NUL bytes when writing, so we patch
        # the ZipInfo's filename after the archive is built -- this mirrors a
        # hand-crafted malicious archive.
        buf = _make_zip([("foo.txt", b"payload")])
        zf = zipfile.ZipFile(buf)
        infos = zf.infolist()
        infos[0].filename = "foo\x00.txt"
        with self.assertRaises(ZipValidationError) as ctx:
            # Re-invoke the internal name check directly since ZipFile writes
            # have already happened.
            from geonode.upload.zip_validation import _check_entry_name

            _check_entry_name(infos[0].filename)
        self.assertIn("NUL byte", str(ctx.exception))

    def test_rejects_symlink_entry(self):
        # external_attr top 16 bits carry the Unix mode; S_IFLNK == 0o120000.
        symlink_mode = stat.S_IFLNK | 0o777
        buf = _make_zip([("link", b"target", {"external_attr": symlink_mode << 16})])
        with self.assertRaises(ZipValidationError) as ctx:
            validate_safe_zip(buf)
        self.assertIn("symlink", str(ctx.exception))

    def test_rejects_too_many_entries(self):
        entries = [(f"f{i}.txt", b"x") for i in range(MAX_ENTRIES + 1)]
        buf = _make_zip(entries)
        with self.assertRaises(ZipValidationError) as ctx:
            validate_safe_zip(buf)
        self.assertIn("entries", str(ctx.exception))

    def test_rejects_zip_bomb_ratio(self):
        # A single highly-compressible entry: 5 MiB of zeros typically crunches
        # below 10 KiB, well past the 100x ratio cap.
        payload = b"\x00" * (5 * 1024 * 1024)
        buf = _make_zip([("bomb.bin", payload)])
        with self.assertRaises(ZipValidationError) as ctx:
            validate_safe_zip(buf)
        self.assertIn("compression ratio", str(ctx.exception))

    def test_rejects_not_a_zip(self):
        with self.assertRaises(ZipValidationError) as ctx:
            validate_safe_zip(io.BytesIO(b"not a zip file"))
        self.assertIn("valid zip", str(ctx.exception))


class IsZipExtensionTests(SimpleTestCase):
    def test_accepts_known_zip_extensions(self):
        self.assertTrue(is_zip_extension("foo.zip"))
        self.assertTrue(is_zip_extension("foo.KMZ"))
        self.assertTrue(is_zip_extension("report.xlsx"))

    def test_rejects_other_extensions(self):
        self.assertFalse(is_zip_extension("foo.shp"))
        self.assertFalse(is_zip_extension("foo.gpkg"))
        self.assertFalse(is_zip_extension(""))
        self.assertFalse(is_zip_extension(None))
