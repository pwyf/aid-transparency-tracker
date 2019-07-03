# Run With Vagrant

Make sure disksize plugin is installed:

```
vagrant plugin install vagrant-disksize

vagrant up
```

## How to run

``` bash
cd /vagrant

source pyenv/bin/activate

flask download_data

flask import_data

flask test_data

flask aggregate_results
```

## Run webservice with vagrant

webservice:

``` bash
flask run --host 0.0.0.0 --port 8080
```
