import json
import jsonschema
from jsonschema import ValidationError


class SchemaValidator:

    def __init__(self, schema_obj, schema=None):
        """
        :param schema_obj: a python object, which will be validated by jsonschema, amongst other things
        """
        self.schema_obj = schema_obj
        if schema is None:
            with open('schema.json', 'r') as f:
                schema = json.load(f)
        self.schema = schema

    def validate(self):
        return jsonschema.validate(self.schema_obj, self.schema)

    def _validate_dependencies(self):
        supported_distribution_types = {"normal", "exponential", "poisson", "bernoulli"}
        # First validate if all field names are unique
        field_names = [x["name"] for x in self.schema_obj["schema"]["fields"]]
        for field_name in field_names:
            if " " in field_name:
                raise ValidationError("Field names for variables must not contain spaces: %s" % field_name)
        # Validate field names for uniqueness
        if len(field_names) != len(set(field_names)):
            raise ValidationError("Field names for variables are not unique: %s" %field_names)
        field_name_set = set(field_names)
        for formula in self.schema_obj["schema"]["formulae"]:
            for prior in formula["priors"]:
                if prior["name"] not in field_name_set:
                    raise ValidationError("Prior name does not match field name: %s" % prior["name"])
                else:
                    # Need to remove it to prevent it from being called again.
                    field_name_set.remove(prior["name"])
                # Now validate type
                if prior["type"] not in supported_distribution_types:
                    raise ValidationError("Prior distribution type can only be one of %s" % supported_distribution_types)
            # Validate fields in deterministic
            # Let's support super simple expressions for now. I would imagine we will need a tokenizer eventually
            # https://stackoverflow.com/questions/43389684/how-can-i-split-a-string-of-a-mathematical-expressions-in-python
            equation_arr = formula["deterministic"]["formula"].replace(" ", "").replace("+", " ").replace("-", " ").replace("*", " ").replace("/", " ").split(" ")
            for e in equation_arr:
                try:
                    float(e)
                except ValueError:
                    # It isn't a number here, so it should be a variable name. Check if it's in field_names
                    if e not in field_names:
                        raise ValidationError("Variable name %s in deterministic equation doesn't exist as field" % e)
        return None
