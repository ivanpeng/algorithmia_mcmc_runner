import Algorithmia
import json

import pandas
import pymc3 as pm
import matplotlib.pyplot as plt

from schema_validator import SchemaValidator

"""
This python script will submit a PyMC3 MCMC job to Algorithmia and return the output.
"""


def _assign_mcmc_defaults(config):
    step_map = {"METROPOLIS": pm.Metropolis}
    return config["schema"]["mcmc_parameters"]["iterations"], step_map[config["schema"]["mcmc_parameters"]["step"]]


def _generate_deterministic(prior_dict, equation_str):
    # Simple Iter 1: eval. I am evil
    # TODO: Need to add ast traversal to actually make it work without evil eval
    # TODO: Keys cannot be subsets of each other atm. ie. if variables x and xy exist, we screwed.
    # Replace the string variable names with a dict lookup, and then eval that
    # Example: eq_str = x + y + 1.2*z, prior_dict = {x: pm.Normal("x", mu=0.4, sd=1), y: pm.Exponential("y", lam=3)}
    # Return should be eval('prior_dict["x"] + prior_dict["y"] + 1.2*prior_dict["z"]')
    keys = prior_dict.keys()
    for key in keys:
        equation_str = equation_str.replace(key, "prior_dict['" + key + "']")
    print(equation_str)
    return eval(equation_str)


# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages
def apply(input):
    # We will take a data input which is a json file with schema and data.
    # First parse the schema, then call runner on data with appropriate commands.

    client = Algorithmia.client()

    if "user_file" in input and client.file(input["user_file"]).exists():
        user_file = input["user_file"]
        text = client.file(user_file).getString()
        data = json.loads(text)
    else:
        data = input
    # Now validate data
    with open("schema.json", "r") as f:
        schema = json.load(f)
    validator = SchemaValidator(data, schema)
    validator.validate()
    # If we reached here, it means we're valid
    # Begin setting the parameters for MCMC!
    (iterations, step_type) = _assign_mcmc_defaults(data)
    observed_dict = {}
    field_names = [x["name"] for x in data["schema"]["fields"]]
    for field_name in field_names:
        observed_dict[field_name] = [x[field_name] for x in data["data"]]

    supported_dists = {"normal": pm.Normal, "exponential": pm.Exponential, "poisson": pm.Poisson,
                       "bernoulli": pm.Bernoulli, "gamma": pm.Gamma}
    for formula in data["schema"]["formulae"]:
        with pm.Model():
            prior_dict = {}
            for prior in formula["priors"]:
                additional_params = dict(prior).copy()
                additional_params.pop("name")
                additional_params.pop("type")
                prior_dict[prior["name"]] = supported_dists[prior["type"]](prior["name"], **additional_params)
                # Only taking observed as Poisson distributions atm
                if prior["name"] == "pts":
                    observed_dict[prior["name"]] = pm.Normal(prior["name"] + "_obs",
                                                             mu=prior_dict[prior["name"]],
                                                             sd=0.04,
                                                             observed=[x[prior["name"]] for x in data["data"]])
                else:
                    observed_dict[prior["name"]] = pm.Poisson(prior["name"] + "_obs",
                                                              mu=prior_dict[prior["name"]],
                                                              observed=[x[prior["name"]] for x in data["data"]])

            # Figure out deterministic now
            # Determinstic vs projected variables
            deterministic_eq = _generate_deterministic(prior_dict, formula["deterministic"]["formula"])
            deterministic = pm.Deterministic(formula["deterministic"]["name"], deterministic_eq)

            # Now run simulation
            start = pm.find_MAP()
            step = pm.NUTS()
            trace = pm.sample(iterations, start=start, step=step)
    pandas.set_option("display.max_columns", 20)
    # pandas.set_option('display.expand_frame_repr', False)
    print(pm.summary(trace))
    burn_in = int(iterations / 5)
    burned_trace = trace[burn_in:]

    pm.plot_posterior(burned_trace)
    plt.show()
    return pm.summary(trace)


if __name__ == '__main__':
    with open("schema-template.json", "r") as f:
        data = json.load(f)
    apply(data)

    # TODO: swap MCMC engine for pyro; just for shits and giggles.
