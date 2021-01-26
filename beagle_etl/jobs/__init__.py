TYPES = {
    "DELIVERY": "beagle_etl.jobs.lims_etl_jobs.fetch_new_requests_lims",
    "REQUEST": "beagle_etl.jobs.lims_etl_jobs.fetch_samples",
    "PARSE_NEW_REQUEST": "beagle_etl.jobs.lims_etl_jobs.parse_new_request_job", # Created from NATS Client - NATS
    "SAMPLE": "beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata",
    "PARSE_SAMPLE_JOB": "beagle_etl.jobs.lims_etl_jobs.parse_samples_job", # Create pooled normal and sample jobs - NATS
    "PARSE_SAMPLE_METADATA": "beagle_etl.jobs.lims_etl_jobs.parse_sample_metadata", # Parse sample metadata - NATS
    "POOLED_NORMAL": "beagle_etl.jobs.lims_etl_jobs.create_pooled_normal", # NATS
    "REQUEST_CALLBACK": "beagle_etl.jobs.lims_etl_jobs.request_callback", # NATS
    "CALCULATE_CHECKSUMS": "beagle_etl.jobs.helper_jobs.calculate_file_checksum", # NATS
    "CALCULATE_CHECKSUM": "beagle_etl.jobs.lims_etl_jobs.calculate_checksum" # NATS
}
