import base64
import binascii
import html

from django.conf import settings
from django.core.exceptions import RequestDataTooBig, TooManyFieldsSent
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadhandler import FileUploadHandler
from django.http import QueryDict
from django.http.multipartparser import FIELD, FILE, ChunkIter, LazyStream, Parser, exhaust
from django.utils.datastructures import MultiValueDict
from django.utils.encoding import force_str

from geonode.upload.models import UploadSizeLimit


class SizeRestrictedFileUploadHandler(FileUploadHandler):
    """
    Upload handler exhaust the stream to avoit overload the memory when the file is bigger than the limit set.
    The upload will be blocked afterwards by the Upload Form
    """

    elegible_url_names = settings.SIZE_RESTRICTED_FILE_UPLOAD_ELEGIBLE_URL_NAMES

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        """
        We use the content_length to signal whether or not this handler should be used.
        """
        # Check the content-length header and url_name to see if we should
        self.is_view_elegible_for_size_restriction = (
            self.request.resolver_match and self.request.resolver_match.url_name in self.elegible_url_names
        )
        self.max_size_allowed = 0
        self.activated = False

        # If the post is too large, we create a empty UploadedFile, otherwise another handler will take care or it.
        if self.is_view_elegible_for_size_restriction:
            file_type = 'dataset_upload_size' if 'uploads/upload' in input_data.path else 'document_upload_size'
            self.max_size_allowed = self._get_max_size(file_type)
            self.activated = content_length > self.max_size_allowed
            if self.activated:
                return self._handle_raw_input_without_file_stream(input_data, META, content_length, boundary, encoding)

    def _handle_raw_input_without_file_stream(self, input_data, META, raw_content_length, boundary, encoding=None):
        """
        Replaces django.http.multipartparser.MultiPartParser.parse
        A rfc2388 multipart/form-data parser but replacing the file stream to the creation of empty files.
        Returns a tuple of ``(MultiValueDict(POST), MultiValueDict(FILES))``.
        """
        # Create the data structures to be used later.
        _post = QueryDict(mutable=True)
        _files = MultiValueDict()

        # For compatibility with low-level network APIs (with 32-bit integers),
        # the chunk size should be < 2^31, but still divisible by 4.
        _chunk_size = min([2 ** 31 - 4, self.chunk_size])

        # Instantiate the parser and stream:
        stream = LazyStream(ChunkIter(input_data, _chunk_size))

        # Whether or not to signal a file-completion at the beginning of the loop.
        old_field_name = None

        # Number of bytes that have been read.
        num_bytes_read = 0
        # To count the number of keys in the request.
        num_post_keys = 0
        # To limit the amount of data read from the request.
        read_size = None

        for item_type, meta_data, field_stream in Parser(stream, boundary):
            if old_field_name:
                # We run this at the beginning of the next loop
                # since we cannot be sure a file is complete until
                # we hit the next boundary/part of the multipart content.
                file_obj = self.file_complete(raw_content_length)
                if file_obj:
                    # If it returns a file object, then set the files dict.
                    _files.appendlist(force_str(old_field_name, encoding, errors="replace"), file_obj)
                old_field_name = None

            try:
                disposition = meta_data["content-disposition"][1]
                field_name = disposition["name"].strip()
            except (KeyError, IndexError, AttributeError):
                continue

            transfer_encoding = meta_data.get("content-transfer-encoding")
            if transfer_encoding is not None:
                transfer_encoding = transfer_encoding[0].strip()
            field_name = force_str(field_name, encoding, errors="replace")

            if item_type == FIELD:
                # NOTE: Parse fields as usual, same as ``MultiPartParser.parse``
                # Avoid storing more than DATA_UPLOAD_MAX_NUMBER_FIELDS.
                num_post_keys += 1
                if (
                    settings.DATA_UPLOAD_MAX_NUMBER_FIELDS is not None
                    and settings.DATA_UPLOAD_MAX_NUMBER_FIELDS < num_post_keys
                ):
                    raise TooManyFieldsSent(
                        "The number of GET/POST parameters exceeded " "settings.DATA_UPLOAD_MAX_NUMBER_FIELDS."
                    )

                # Avoid reading more than DATA_UPLOAD_MAX_MEMORY_SIZE.
                if settings.DATA_UPLOAD_MAX_MEMORY_SIZE is not None:
                    read_size = settings.DATA_UPLOAD_MAX_MEMORY_SIZE - num_bytes_read

                # This is a post field, we can just set it in the post
                if transfer_encoding == "base64":
                    raw_data = field_stream.read(size=read_size)
                    num_bytes_read += len(raw_data)
                    try:
                        data = base64.b64decode(raw_data)
                    except binascii.Error:
                        data = raw_data
                else:
                    data = field_stream.read(size=read_size)
                    num_bytes_read += len(data)

                # Add two here to make the check consistent with the
                # x-www-form-urlencoded check that includes '&='.
                num_bytes_read += len(field_name) + 2
                if (
                    settings.DATA_UPLOAD_MAX_MEMORY_SIZE is not None
                    and num_bytes_read > settings.DATA_UPLOAD_MAX_MEMORY_SIZE
                ):
                    raise RequestDataTooBig("Request body exceeded settings.DATA_UPLOAD_MAX_MEMORY_SIZE.")

                _post.appendlist(field_name, force_str(data, encoding, errors="replace"))
            elif item_type == FILE:
                # NOTE: Parse files WITHOUT a stream.
                # This is a file, use the handler...
                file_name = disposition.get("filename")
                if file_name:
                    file_name = force_str(file_name, encoding, errors="replace")
                    file_name = self.sanitize_file_name(file_name)
                if not file_name:
                    continue

                content_type, content_type_extra = meta_data.get("content-type", ("", {}))
                content_type = content_type.strip()
                charset = content_type_extra.get("charset")
                content_length = None

                self.new_file(field_name, file_name, content_type, content_length, charset, content_type_extra)

                # Handle file upload completions on next iteration.
                old_field_name = field_name
            else:
                # If this is neither a FIELD or a FILE, just exhaust the stream.
                exhaust(stream)

        # Make sure that the request data is all fed
        exhaust(input_data)

        _post._mutable = False
        return _post, _files

    def sanitize_file_name(self, file_name):
        """
        Same as django.http.multipartparser.MultiPartParser.sanitize_file_name
        so it's not needed to instantiate a MultiPartParser object just to
        sanitize the filename of an upload.
        """
        file_name = html.unescape(file_name)
        file_name = file_name.rsplit("/")[-1]
        file_name = file_name.rsplit("\\")[-1]

        if file_name in {"", ".", ".."}:
            return None
        return file_name

    def _get_max_size(self, file_type):
        try:
            max_size_db_obj = UploadSizeLimit.objects.get(slug=file_type)
        except UploadSizeLimit.DoesNotExist:
            max_size_db_obj = UploadSizeLimit.objects.create_default_limit_with_slug(slug=file_type)
        return (max_size_db_obj.max_size * 2) + 2097152

    def receive_data_chunk(self, raw_data, start):
        """
        Receive data from the streamed upload parser. ``start`` is the position in the file of the chunk.
        """
        return raw_data

    def file_complete(self, file_size):
        """
        Signal that a file has completed.
        NOTE: When activated, file size DOES NOT corresponds to the actual size.
        NOTE: When activated, file size IS NOT accumulated by all the chunks.
        In this case, it represents the total content_length of the request.
        """
        if not self.activated:
            return

        # Create a concrete `UploadedFile` with empty content and `file_size` size
        uploaded_file = SimpleUploadedFile(
            name=self.file_name,
            content=b"",  # Empty Content
            content_type=self.content_type,
        )
        uploaded_file.field_name = self.field_name
        uploaded_file.size = file_size  # Set Size
        uploaded_file.charset = self.charset
        uploaded_file.content_type_extra = self.content_type_extra

        return uploaded_file
