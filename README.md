## Introduction ##
This is a plugin to run a serverless instance of MCMC on Algorithmia. It will accept a json schema, which will declare the data schema, along with what are the observed variables, vs. the deterministic ones. Based on the equation input, it will call PyMC3's MCMC algortithm to simulate distribution of data (read more here: ). The output will be a graph, and the trace which can be utilized to generate information about the distributions.

## Getting Started ##

Let's get started with a simple example. Consider a mutual fund, consistent of M stocks and N bonds. The stocks and bonds have been very well studied, and the stock returns can be modeled as a normal distribution with parameters mu_i, and sd_i (where i denotes stock i, 1 to M), while bond returns are modeled as an exponential distribution with parameter lambda_j (where j denotes bond j, 1 to N). We want to find out the mutual fund's overall return and the volatility of that return. To solve this, we call upon Bayes' rule to solve for our posterior given our priors, but Bayes' rule stipulates that we need to know the entire distribution to be able to solve the posterior. Given that there is no analytical solution to the entire distribution, we can utilize MCMC to approximate a solution to do so. We will be executing this very example to solve that.

Let's make our example a little more concrete. Imagine this mutual fund is consistent of 2 stocks and 2 bonds. We don't know the exact parameters of the each financial securities, but we do have their observed data, and we have their distribution behaviour. Given that this is Bayesian statistics, we give our prior estimates and let Bayes rule do the rest. Let's declare our model first:

```
Stock_1 ~ Normal(3, 0.4)

Stock_2 ~ Normal(4, 0.5)

Bond_1 ~ Exponential(2.5)

Bond_2 ~ Exponential(4)
```

Keep in mind that these are all estimates; we don't actually know the true value of this! The observed data is in stock_example.json. Meanwhile, our deterministic value for our mutual fund is:

```
MF = Stock_1 + Stock_2 + Bond_1 + Bond_2
```

We are assuming equal weights and that they all are the same value, but that can easily be changed. For example, if the mutual fund comprised of twice as much of stock 1 over everything else, the deterministic equation would be: 

```
MF = 2 * Stock_1 + Stock_2 + Bond_1 + Bond_2
```

Now let's codify this into python code to run with MCMC. Let's get started on the schema. Create a new file called mutual_fund_example.json, and copy the contents of template-schema.json into it. You will see the schema example set there, along with the test data. Run that with a simple 

```bash
python3 
```


## Schema Validation ##

