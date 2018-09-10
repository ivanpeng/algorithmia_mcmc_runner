import uuid

import Algorithmia
import pandas as pd

import json
import pymc3 as pm

from pymc3.backends.tracetab import trace_to_dataframe

from .exception import AlgorithmError

"""
This python script will submit a PyMC3 MCMC job to Algorithmia and return the output. This assumes the schema is
already correct. It will simply connect to the algorithm set up in Algorithmia and run the commands.
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


def write_dataframe_to_json(df, compression=True):
    tempfile = "/tmp/" + str(uuid.uuid4()) + ".tmp"
    if compression == True:
        outstream = df.to_json(compression="gzip")
    else:
        outstream = df.to_json()
    with open(tempfile, 'w') as f:
        f.write(outstream)
    return tempfile


# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages
def apply(input):
    client = Algorithmia.client()
    if "target_output" not in input:
        raise AlgorithmError("Target file name must be specified")

    if "user_file" in input and client.file(input["user_file"]).exists():
        user_file = input["user_file"]
        text = client.file(user_file).getString()
        data = json.loads(text)
    elif "data" in input:
        # Data is sent in via post, in which case it's a vanilla object
        data = input["data"]
        # TODO: Okay, this is dumb, but we'll get this working
        text = json.dumps(data)
    else:
        raise AlgorithmError("Input data must be specified or file must be specified")

    trace = run_simulation(pd.read_json(text))
    # For now, save trace to algorithmia data file, and return results of summary
    # TODO: Make this configurable from input
    output_file_uri = "data://ivanpeng/basketball/" + input["target_output"]
    tempfile = write_dataframe_to_json(trace_to_dataframe(trace), compression=True)
    client.file(output_file_uri).putFile(tempfile)
    return pm.summary(trace)
