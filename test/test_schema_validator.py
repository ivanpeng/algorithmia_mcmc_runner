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
        self.assertIsNone(validator._validate_dependencies())

    def test_full_schema_with_duplicate_field_names_fails(self):
        with open("src/schema-template.json", "r") as f:
            obj = json.load(f)
        obj["schema"]["fields"].append({
            "name": "returns_stock_1",
            "type": "float"
        })
        validator = SchemaValidator(obj)
        self.assertRaises(ValidationError, validator._validate_dependencies)

    def test_full_schema_with_field_with_space_fails(self):
        with open("src/schema-template.json", "r") as f:
            obj = json.load(f)
        obj["schema"]["fields"].append({
            "name": "a field name with spaces",
            "type": "float"
        })
        validator = SchemaValidator(obj)
        self.assertRaises(ValidationError, validator._validate_dependencies)

    def test_full_schema_with_nonexistent_prior_fails(self):
        with open("src/schema-template.json", "r") as f:
            obj = json.load(f)
        obj["schema"]["formulae"][0]["priors"].append({
            "name": "a_field_which_does_not_exist",
            "type": "normal",
            "mu": 3,
            "sd": 0.4
        })
        validator = SchemaValidator(obj)
        self.assertRaises(ValidationError, validator._validate_dependencies)

    def test_full_schema_with_duplicate_prior_fails(self):
        with open("src/schema-template.json", "r") as f:
            obj = json.load(f)
        obj["schema"]["formulae"][0]["priors"].append({
            "name": "returns_stock_1",
            "type": "normal",
            "mu": 3,
            "sd": 0.4
        })
        validator = SchemaValidator(obj)
        self.assertRaises(ValidationError, validator._validate_dependencies)

    def test_full_schema_with_nonexistent_field_in_prior_fails(self):
        with open("src/schema-template.json", "r") as f:
            obj = json.load(f)
        obj["schema"]["formulae"][0]["priors"].append({
            "name": "a_field_which_does_not_exist",
            "type": "normal",
            "mu": 3,
            "sd": 0.4
        })
        validator = SchemaValidator(obj)
        self.assertRaises(ValidationError, validator._validate_dependencies)

    def test_full_schema_with_unsupported_dist_type_fails(self):
        with open("src/schema-template.json", "r") as f:
            obj = json.load(f)
        obj["schema"]["formulae"][0]["priors"][0]["type"] = "pareto"
        validator = SchemaValidator(obj)
        self.assertRaises(ValidationError, validator._validate_dependencies)

    def test_full_schema_with_nonexistent_field_in_deterministic_eq_fails(self):
        with open("src/schema-template.json", "r") as f:
            obj = json.load(f)
        obj["schema"]["formulae"][0]["deterministic"]["formula"] = "1.2 * returns_stock_1 + returns_bond_1 - " \
                                                                   "a_nonexistent_prior "
        validator = SchemaValidator(obj)
        self.assertRaises(ValidationError, validator._validate_dependencies)