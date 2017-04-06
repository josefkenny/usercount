Mastodon User Count Bot
=======================

A bot which posts user statistics to [Mastodon](https://github.com/tootsuite/mastodon).

### Dependencies

-   **Python 2**
-   [gnuplot](http://www.gnuplot.info/) version 5 or greater
-   [Mastodon.py](https://github.com/halcy/Mastodon.py): `pip install Mastodon.py`
-   Everything else at the top of `usercount.py`!

### Usage:

1. Edit `config.txt` to specify the hostname of the Mastodon instance you would like to get data from.
2. Create a file called `secrets.txt` in the folder `secrets/`, as follows:

```
uc_client_id: <your client ID>
uc_client_secret: <your client secret>
uc_access_token: <your access token>
```

3. Use your favourite scheduling method to set `./usercount.py` to run regularly.

Call the script with the `--no-upload` argument if you don't want to upload anything.

Note: The script will fail to output a graph until you've collected data points that are actually different!
