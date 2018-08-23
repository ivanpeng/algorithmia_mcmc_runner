from src import MCMC_runner

def test_MCMC_runner():
    assert MCMC_runner.apply("Jane") == "hello Jane"
