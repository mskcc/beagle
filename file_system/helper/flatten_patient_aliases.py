def update_patient_aliases(metadata):

    if not metadata:
        return False

    patient_aliases = metadata.get("patientAliases")
    if not patient_aliases:
        return False

    new_patient_aliases = {
        f"patientAliases_{item['namespace']}": item["value"]
        for item in patient_aliases
        if "namespace" in item and "value" in item
    }

    if not new_patient_aliases:
        return False

    metadata.update(new_patient_aliases)
    return True
