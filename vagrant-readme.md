# Run With Vagrant

Make sure disksize plugin is installed:

```
vagrant plugin install vagrant-disksize

vagrant up
```

## How to run

``` bash
vagrant ssh

cd /vagrant

source pyenv/bin/activate

flask setup

flask download_data

flask import_data

flask test_data

flask aggregate_results
```

## Run webservice with vagrant

webservice (flask uses port 5000 by default, this is opened on the vagrant box):

``` bash
flask run --host 0.0.0.0
```
