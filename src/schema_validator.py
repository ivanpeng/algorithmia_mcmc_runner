import json
import jsonschema


class SchemaValidator:

    def __init__(self, schema_obj, schema=None):
        """
        :param schema_obj: a python object, which will be validated by jsonschema, amongst other things
        """
        self.schema_obj = schema_obj
        if schema is None:
            with open('src/schema.json', 'r') as f:
                schema = json.load(f)
        self.schema = schema

    def validate(self):
        return jsonschema.validate(self.schema_obj, self.schema)
