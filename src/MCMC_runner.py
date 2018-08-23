import Algorithmia

"""
This python script will submit a PyMC3 MCMC job to Algorithmia and return the output. This assumes the schema is
already correct. It will simply connect to the algorithm set up in Algorithmia and run the commands.
"""

# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages
def apply(input):

    # We will take a data input which is a json file with schema and data.
    # First parse the schema, then call runner on data with appropriate commands.

    return "hello {}".format(input)
