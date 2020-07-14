TYPES = {
    "DELIVERY": "beagle_etl.jobs.lims_etl_jobs.fetch_new_requests_lims",
    "REQUEST": "beagle_etl.jobs.lims_etl_jobs.fetch_samples",
    "SAMPLE": "beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata",
    "POOLED_NORMAL": "beagle_etl.jobs.lims_etl_jobs.create_pooled_normal",
    "REQUEST_CALLBACK": "beagle_etl.jobs.lims_etl_jobs.request_callback",
    "CALCULATE_CHECKSUMS": "beagle_etl.jobs.helper_jobs.calculate_file_checksum",
    "CALCULATE_CHECKSUM": "beagle_etl.jobs.lims_etl_jobs.calculate_checksum"
}
