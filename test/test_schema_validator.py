import unittest
import json

from jsonschema import ValidationError

from src.schema_validator import SchemaValidator

class TestSchemaValidator(unittest.TestCase):

    def test_simple_schema_validation(self):
        schema = json.loads('{"type" : "object", "properties" : {"price" : {"type" : "number"},"name" : {"type" : "string"}}}')
        obj = {"name" : "Eggs", "price" : 34.99}
        validator = SchemaValidator(obj, schema)
        self.assertIsNone(validator.validate())

    def test_simple_schema_validation_fail(self):
        schema = json.loads('{"type" : "object", "properties" : {"price" : {"type" : "number"},"name" : {"type" : "string"}}}')
        obj = {"name" : "Eggs", "price" : "A string which should fail it"}
        validator = SchemaValidator(obj, schema)
        self.assertRaises(ValidationError, validator.validate)

    def test_full_schema_validation(self):
        with open("src/schema-template.json", "r") as f:
            obj = json.load(f)
        validator = SchemaValidator(obj)
        self.assertIsNone(validator.validate())