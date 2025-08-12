import os


def spoof_barcode(file_path):
    """
    Spoof barcode by removing R1/R2 or .bam from end of filename, reverse the string.
    Works even with compound extensions like .fastq.gz.

    Barcode is used only for submitting to the cluster; makes sure paired fastqs get
    sent together during job distribution
    """
    # Get just the base name
    filename = os.path.basename(file_path)

    # Reverse full filename
    reversed_name = filename[::-1]

    # Remove reversed extensions
    for ext in ["bam", "gz", "fastq", "bz2", "tar"]:
        rev_ext = ext[::-1] + "."  # e.g., 'gz.' to match '.gz'
        if reversed_name.startswith(rev_ext):
            reversed_name = reversed_name[len(rev_ext) :]

    # Remove R1/R2 in reversed form
    reversed_name = reversed_name.replace("1R_", "").replace("2R_", "")

    # Reverse back to get spoofed barcode
    spoofed_barcode = reversed_name[::-1]
    return spoofed_barcode
