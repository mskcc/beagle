# Helper Scripts

## Dumping Database Fixtures

In order to dump JSON copies of database fixtures, you should first have loaded a copy of a production database backup into your Beagle PostgreSQL database instance.

The included `dump_db_fixtures.py` script can be used to some types of fixtures. See `dump_db_fixtures.py -h` for the most up to date details.

### Dump Requests

A request can be dumped with `dump_db_fixtures.py request <request_id>`. This will output a JSON for the File entries associated with the request, and a JSON for the FileMetadata entries. Use the `--santize` flag to replace personal information in the fixtures (e.g. people's names and email addresses) with fake ones. Currently, `--sanitize`

Example:

```
$ ./dump_db_fixtures.py request 09603_I --sanitize

$ ls
09603_I.file.json
09603_I.filemetadata.json
```

- NOTE: `dump_db_fixtures.py` should be run from your Beagle dev environment since it requires Python 3 + Django. If you installed with the `Makefile` in the `beagle` root directory, from there you can just use `make bash` to load your dev instance environment to run the script with.

## Sanitize Fixtures

Fixtures for use in the repo should be further sanitized to remove sample ID's and replace CMO ID's.

Some easy helper scripts have been included for this purpose.

Use the script `get_fields_to_sanitize.sh` to print out a list of all recognized CMO ID's and sample ID's in the JSON you generated with `dump_db_fixtures.py`

```
$ ./get_fields_to_sanitize.sh 09603_I.filemetadata.json
# a list of id's
```

Use the list of ID's that are printed out to create a `patterns.tsv` file in this same directory. This will be used for the `sanitize.sh` script later. The `patterns.tsv` file should be formatted like this:

```
old_pattern1	new_pattern1
old_pattern2	new_pattern2
```

A quick & easy way to do this is to utilize both Excel and a raw text editor (`nano`, Atom, Sublime, etc.). You can copy the terminal output from `get_fields_to_sanitize.sh` into Excel, then in the adjacent column fill in dummy identifiers such as `Sample1`, `Sample2`, etc.. For CMO ID's, you can generate fake ones with the included `generate_cmo_id.py` script. Once you have two columns, simple highlight them in Excel (just the two columns, not the entire sheet) and paste them into `nano`/Atom/Sublime/etc. and they should be entered as tab delimited text which you can save with the filename of `patterns.tsv`

- TODO: write a script to do this instead

Once `patterns.tsv` is present, you can run the `sanitize.sh` script on your JSON to replace all the old patterns with new ones.


```
./sanitize.sh 09603_I.filemetadata.json
```

For good measure, double check the contents of the JSON to verify that it looks correct before commiting it. The JSON should be moved to the appropriate `fixtures` directory. 
