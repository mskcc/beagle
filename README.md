# beagle

Beagle is backend service for managing files, pipelines and runs.

![alt text](docs/pics/voyager.png "Diagram of Voyager project")

## beagle responsibilities 

- Users
  - Authentication using MSKCC LDAP
  - Every user will have same permissions
- Files
  - List files in Beagle DB
  - Search files (filename, metadata, file-type, file-group)
  - Create File in Beagle DB
- FileMetadata
  - Metadata is associated with file.
  - Metadata versioning. Changes are tracked, and can be reverted.
  - Metadata validation using JsonSchema.
- Pipelines
  - Using pipelines hosted on github
  - Creating RUNs from pipelines
- Run
  - Creating run (choosing pipeline, choosing inputs)
  - Submitting job to rabix executor
  - Receiving updates about job status from rabix
  - List outputs generated from run
- LIMS integration
  - Periodically fetch new samples from LIMS and create File objects in Beagle DB
  - Try to pair fails, and create runs
  - Notify if there are some errors with files or file metadata

## setup

- Requirements
  - PostgreSQL==11
  - python 3
  
- Instructions
  - virtualenv beagle
  - pip install -r requirements.txt
  - export BEAGLE_DB_NAME=<beagle_db_name>
  - export BEAGLE_DB_USERNAME=<beagle_db_username>
  - export BEAGLE_DB_PASSWORD=<beagle_db_password>
  - export BEAGLE_AUTH_LDAP_SERVER_URI=<ldap_server_uri>
  - export BEAGLE_RABIX_PATH=<rabix_cli_path>
  - export BEAGLE_RABIX_URL=<rabix_url>
  - python manage.py migrate
  - python manage.py runserver
