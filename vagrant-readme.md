# Setup

First, clone the repository including the submodules:

```
git clone --recursive --branch original-version https://github.com/pwyf/aid-transparency-tracker.git
cd aid-transparency-tracker
```

Make sure disksize plugin is installed and initialise the vagrant box:

``` bash
vagrant plugin install vagrant-disksize
vagrant up
```

## Running the tracker

If the previous steps completed successfully then follow the next steps to initialise the tracker with the latest data from IATI:

``` bash
vagrant ssh
cd /vagrant
source pyenv/bin/activate
flask setup   # This setup will require you to enter a username and password which will be used to access the tracker through the UI
flask download_data
flask import_data
flask test_data
flask aggregate_results
flask setup_sampling
```

## Start the local server

Run the flask server (flask uses port 5000 by default):

``` bash
flask run --host 0.0.0.0
```

You should now be able to access the tracker in your browser (localhost:5000 or 0.0.0.0:5000)
