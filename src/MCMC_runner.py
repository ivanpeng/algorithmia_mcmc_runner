import Algorithmia
import pandas as pd

import pymc3 as pm
import json

from functools import reduce
from pymc3.backends.tracetab import trace_to_dataframe

from .exception import AlgorithmError

"""
The algorithm is responsible for running MCMC sampling simulations for fantasy sports stats. It is based off of a
serverless application, Algorithmia to run. The process is kicked off with a post command to the algorithmia-hosted
program, with inputs as a file location or a json for input. MCMC is sampled, and the sampled trace is converted to a
dataframe and pushed to s3 (in compressed snappy parquet format), with intentions of pushing to Google BigQuery.
"""


def run_simulation(df):
    iterations = 10000
    burn_in = int(iterations / 5)

    with pm.Model():
        pt_mu = pm.Normal("pt_mu", mu=30, sd=8)
        reb_mu = pm.Gamma("reb_mu", alpha=6, beta=1)
        ast_mu = pm.Gamma("ast_mu", alpha=10, beta=1)
        stl_mu = pm.Gamma("stl_mu", alpha=1, beta=2)
        blk_mu = pm.Gamma("blk_mu", alpha=1, beta=1)
        tov_mu = pm.Gamma("tov_mu", alpha=2, beta=2)

        pt_sd = pm.Gamma("pt_sd", alpha=1, beta=1)

        pt_observed = pm.Normal("pts_obs", mu=pt_mu, sd=pt_sd, observed=df['pts'].values)
        reb_observed = pm.Poisson("reb_obs", mu=reb_mu, observed=(df['drb'] + df['orb']).values)
        ast_observed = pm.Poisson("ast_obs", mu=ast_mu, observed=df['ast'].values)
        stl_observed = pm.Poisson("stl_obs", mu=stl_mu, observed=df['stl'].values)
        blk_observed = pm.Poisson("blk_obs", mu=blk_mu, observed=df['blk'].values)
        tov_observed = pm.Poisson("tov_obs", mu=tov_mu, observed=df['tov'].values)

        fp_mu_eq = pm.Normal("pts_projected", mu=pt_mu, sd=pt_sd) + \
                   1.2 * pm.Poisson("reb_projected", mu=reb_mu) + \
                   1.5 * pm.Poisson("ast_projected", mu=ast_mu) + \
                   3 * pm.Poisson("stl_projected", mu=stl_mu) + \
                   3 * pm.Poisson("blk_projected", mu=blk_mu) - \
                   pm.Poisson("tov_projected", mu=tov_mu)

        fp_mu = pm.Deterministic("fp_projected", fp_mu_eq)

        start = pm.find_MAP()
        step = pm.NUTS()
        trace = pm.sample(iterations, start=start, step=step)

    burned_trace = trace[burn_in:]
    # TODO: when we hook up google bigquery, we are going to write to two tables: a summary table, and a trace table
    # summary_df = pm.summary(burned_trace)
    return burned_trace


def check_element_in_set(elem, key_set):
    return reduce((lambda x,y: x and y), [x in elem for x in key_set])


def validate_data(json_data):
    # Need to assert that the fields in data are adequate:
    # 1. json_data is an array
    # 2. has a set of {'pts', 'orb', 'drb', 'ast', 'stl', 'blk', 'tov'}
    # 3. Those values are floats/integers
    key_set = {'pts', 'orb', 'drb', 'ast', 'stl', 'blk', 'tov'}
    if not isinstance(json_data, (list,)):
        return False
    for elem in json_data:
        if not check_element_in_set(elem, key_set):
            return False
    return True


# TODO: TEST, or at least make more modular for testing
def parse_dataframe(input, client):
    if "target_output" not in input:
        raise AlgorithmError("Target file name must be specified")
    if "user_file" in input and client.file(input["user_file"]).exists():
        user_file = input["user_file"]
        text = client.file(user_file).getString()
        data = json.loads(text)
    elif "data" in input:
        # Data is sent in via post, in which case it's a vanilla object
        data = input["data"]
    else:
        raise AlgorithmError("Input data must be specified or file must be specified")
    if not validate_data(data):
        raise AlgorithmError("Data has not been validated")
    df = pd.DataFrame.from_dict(data)
    return df


def write_output(trace, uri, filepath, client):
    trace_dataframe = trace_to_dataframe(trace)
    trace_dataframe.to_parquet(filepath, engine="pyarrow", compression="snappy")
    client.file(uri).putFile(filepath)


# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages
def apply(input):
    client = Algorithmia.client()
    df = parse_dataframe(input, client)
    trace = run_simulation(df)
    # For now, save trace to algorithmia data file, and return results of summary
    output_file_uri = "s3+fantasygm://fantasygm-trace-out/v1/" + input["target_output"]
    # TODO: need a list of varnames for converting the multitrace to dataframe
    write_output(trace, output_file_uri, input["target_output"], client)
    return pm.summary(trace).to_json()
