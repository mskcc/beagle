# beagle

Backend service for managing files, pipelines and runs.

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


