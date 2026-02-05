import os
import tempfile
import zipfile
import uuid
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from geonode.upload import project_dir
from geonode.upload.api.exceptions import InvalidInputFileException
from geonode.upload.handlers.xlsx.handler import XLSXFileHandler


class TestXLSXHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = XLSXFileHandler()

        # Consistent with CSV handler's fixture path
        cls.valid_xlsx = f"{project_dir}/tests/fixture/valid_excel.xlsx"
        cls.valid_xls = f"{project_dir}/tests/fixture/valid_excel.xls"
        cls.empty_rows_xlsx = f"{project_dir}/tests/fixture/valid_with_empty_rows.xlsx"
        cls.leading_empty_xlsx = f"{project_dir}/tests/fixture/valid_leading_empty_rows.xlsx"
        cls.missing_lat_xlsx = f"{project_dir}/tests/fixture/missing_lat.xlsx"
        cls.wrong_data_xlsx = f"{project_dir}/tests/fixture/wrong_data.xlsx"

        cls.user, _ = get_user_model().objects.get_or_create(username="admin")

    def setUp(self):
        # Force the handler to be enabled for testing
        XLSXFileHandler.XLSX_UPLOAD_ENABLED = True

    @patch("geonode.upload.handlers.common.vector.BaseVectorFileHandler.can_handle")
    def test_can_handle_xlsx_and_xls(self, mock_base_can_handle):
        """Check if the handler identifies both extensions."""
        mock_base_can_handle.return_value = True

        self.assertTrue(self.handler.can_handle({"base_file": self.valid_xlsx}))
        self.assertTrue(self.handler.can_handle({"base_file": self.valid_xls}))

        # Also verify it returns False when the file is wrong
        self.assertFalse(self.handler.can_handle({"base_file": "random.txt"}))

    @patch("geonode.upload.orchestrator.orchestrator.get_execution_object")
    @patch("geonode.upload.orchestrator.orchestrator.update_execution_request_obj")
    def test_pre_processing_success_with_valid_files(self, mock_update, mock_get_exec):
        test_files = [self.valid_xlsx, self.valid_xls, self.empty_rows_xlsx, self.leading_empty_xlsx]

        for file_path in test_files:
            exec_id = str(uuid.uuid4())
            files = {"base_file": file_path}

            with patch(
                "geonode.upload.handlers.csv.handler.CSVFileHandler.pre_processing",
                return_value=({"files": files, "temporary_files": {}}, exec_id),
            ):

                data, _ = self.handler.pre_processing(files, exec_id)

                output_csv = data["files"]["base_file"]
                self.assertTrue(output_csv.endswith(".csv"))
                self.assertTrue(os.path.exists(output_csv))

                # Cleanup
                if os.path.exists(output_csv):
                    os.remove(output_csv)

    @patch("geonode.upload.orchestrator.orchestrator.get_execution_object")
    def test_pre_processing_fails_on_missing_lat(self, mock_get_exec):
        """Should fail when header fingerprinting doesn't find Latitude."""
        exec_id = str(uuid.uuid4())
        files = {"base_file": self.missing_lat_xlsx}

        with patch(
            "geonode.upload.handlers.csv.handler.CSVFileHandler.pre_processing",
            return_value=({"files": files}, exec_id),
        ):
            with self.assertRaises(InvalidInputFileException) as context:
                self.handler.pre_processing(files, exec_id)

            self.assertIn("geometry headers", str(context.exception))

    @patch("geonode.upload.orchestrator.orchestrator.get_execution_object")
    def test_pre_processing_fails_on_wrong_data(self, mock_get_exec):
        """Should fail on row 1 of the data due to 'nan' and extreme magnitude."""
        exec_id = str(uuid.uuid4())
        files = {"base_file": self.wrong_data_xlsx}

        with patch(
            "geonode.upload.handlers.csv.handler.CSVFileHandler.pre_processing",
            return_value=({"files": files}, exec_id),
        ):
            with self.assertRaises(InvalidInputFileException) as context:
                self.handler.pre_processing(files, exec_id)

            # The error should specifically mention the coordinate error and the row
            self.assertIn("Coordinate error at row 2", str(context.exception))

    def test_data_sense_check_logic(self):
        """Directly test the coordinate validation math."""
        # Valid
        self.assertTrue(self.handler._data_sense_check(37.8, -122.4))
        # NaN
        self.assertFalse(self.handler._data_sense_check("nan", 40.0))
        # Infinite
        self.assertFalse(self.handler._data_sense_check(float("inf"), 40.0))
        # Extreme Magnitude
        self.assertFalse(self.handler._data_sense_check(40000001, 10.0))
        # Excel Date (as datetime object)
        from datetime import datetime

        self.assertFalse(self.handler._data_sense_check(datetime.now(), 40.0))

    def test_security_billion_laughs_protection(self):
        """
        Security Test: Verifies protection against XML Entity Expansion (Billion Laughs).
        Ensures the parser handles malicious DTD entities without crashing.
        """
        # Create the malicious payload in memory
        xml_payload = """<?xml version="1.0"?>
        <!DOCTYPE lolz [
        <!ENTITY lol "lol">
        <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
        <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
        <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
        ]>
        <workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
            <sheets><sheet name="&lol3;" sheetId="1" r:id="rId1"/></sheet></sheets>
        </workbook>"""

        # Use a temporary file so we don't pollute the project's fixture folder
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf:
            with zipfile.ZipFile(tf, "w") as zf:
                zf.writestr("xl/workbook.xml", xml_payload)
                zf.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="xml" ContentType="application/xml"/></Types>'
            )
            malicious_path = tf.name

        exec_id = str(uuid.uuid4())
        files = {"base_file": malicious_path}

        try:
            # Patch the super().pre_processing to return our temp file
            with patch(
                "geonode.upload.handlers.csv.handler.CSVFileHandler.pre_processing",
                return_value=({"files": files, "temporary_files": {}}, exec_id),
            ):

                # The test passes if it raises the exception OR if it handles it safely
                # without timing out (hanging).
                with self.assertRaises(InvalidInputFileException) as context:
                    self.handler.pre_processing(files, exec_id)

                self.assertIn("Failed to securely parse Excel", str(context.exception))
        finally:
            if os.path.exists(malicious_path):
                os.remove(malicious_path)
