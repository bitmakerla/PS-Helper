import csv
import re
import smart_open
import json
from pprint import pformat
from cerberus import Validator


class AutoInputMixin:
    """
    Mixin for handling input data in spiders.

    Supported input sources:
      - ``-a input='{"key": "value"}'`` : JSON string
      - ``-a input_file=path/to/file.json`` : JSON file
      - ``-a input_sheet=<GoogleSheetURL>`` : Google Sheet CSV export

    Validates input using ``input_schema`` (Cerberus).
    """

    # Input Cerberus schema
    input_schema = None

    # settings to allow additional data and third boolean True/False/None
    validator = Validator(allow_unknown=True, ignore_none_values=True)

    # Used to ignore all non-prefixed values
    input_prefix = ""

    def __init__(self, *args, **kwargs):
        """Parse and assign the spider's input."""
        super().__init__(*args, **kwargs)
        self._check_and_assign(**kwargs)

    def _check_and_assign(self, **kwargs):
        """Set the input argument dict as a set of spider's attributes."""
        self.input = self._read_from_input_file() or self._read_from_input() or self._read_from_google_sheet() or {
            **kwargs}
        fields_to_assign = self._validate_fields(self.input)

        # To non-prefixed values.
        for key in filter(None, self.input_prefix.split(".")):
            fields_to_assign = fields_to_assign.get(key, {})
        if isinstance(fields_to_assign, list):
            self.input_data = fields_to_assign
        else:
            self.__dict__.update(fields_to_assign)

    def _read_from_input_file(self):
        """Read input json from the ``input_file`` argument if it was set."""
        if hasattr(self, "input_file") and self.input_file:
            with open(self.input_file) as json_file:
                return json.load(json_file)
        return None

    def _read_from_input(self):
        """Read input json from the ``input`` argument if it was set."""
        if hasattr(self, "input") and self.input:
            return json.loads(self.input)
        return None

    def _read_from_google_sheet(self):
        if hasattr(self, "input_sheet") and self.input_sheet:
            drive_csv = "https://docs.google.com/spreadsheets/d/{id}/export?format=csv"
            result = re.search(r'/d/([a-zA-Z0-9-_]+)', self.input_sheet)
            drive_id = result.group(1)

            with smart_open.open(drive_csv.format(id=drive_id), 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Assume the first row is headers
                data_list = [dict(zip(headers, row)) for row in reader]
                print(data_list)

            return data_list
        return None

    def _validate_fields(self, input_values):
        """Validate the input using the ``input_schema`` attribute if it was set."""
        if not self.input_schema:
            return input_values

        if isinstance(input_values, list):
            validated_list = []
            for i, item in enumerate(input_values):
                if not self.validator.validate(item, self.input_schema):
                    msg = f"Failed input validation at index {i}:\n"
                    msg += f"input = {pformat(item)}\nerrors = {pformat(self.validator.errors)}"
                    raise ValueError(msg)
                validated_list.append(self.validator.document)
            return validated_list

        if not self.validator.validate(input_values, self.input_schema):
            msg = "Failed input validation:\ninput = %s\nerrors = %s"
            msg_args = pformat(input_values), pformat(self.validator.errors)
            raise ValueError(msg % msg_args)

        return self.validator.document
