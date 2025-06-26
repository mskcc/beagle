import os
import json
from runner.pipeline.pipeline_resolver import PipelineResolver


class NextflowResolver(PipelineResolver):
    def __init__(self, github, entrypoint, version=None, nfcore_template=None):
        super().__init__(github, entrypoint, version)
        self.nfcore_template = nfcore_template

    def resolve(self):
        dir = self._dir_name()
        location = self._git_clone(dir)
        if self.nfcore_template:
            # Check main schema for CLI inputs
            with open(os.path.join(location, "nextflow_schema.json"), "r") as f:
                nextflow_schema = json.load(f)
                inputs = self.schemas2template(nextflow_schema, location)
                pipeline = {"inputs": inputs}
        else:
            with open(os.path.join(location, "inputs.template.json"), "r") as f:
                pipeline = json.load(f)
        self._cleanup(location)
        return pipeline

    def schemas2template(self, nextflow_schema, location):
        inputs = []
        defs = nextflow_schema.get("$defs")
        if not defs:
            defs = nextflow_schema.get("definitions")
        # loop over definition properties
        for key, val in defs.items():
            props = defs[key]["properties"]
            for key, items in props.items():
                # see if property has a schema
                schema = props[key].get("schema")
                mimetype = props[key].get("mimetype")
                # TODO this should probably be it's own function with a mapping of mimetype to delimiter
                if schema and mimetype:
                    if mimetype == "text/csv":
                        delimiter = ","
                        extension = ".csv"
                    elif mimetype == "text/tsv":
                        delimiter = "\t"
                        extension = ".tsv"
                    else:
                        print(f"Warning: Unsupported mimetype '{mimetype}', defaulting to tab delimiter.")
                        delimiter = "\t"
                        extension = ".tsv"
                    schema_path = os.path.join(location, schema)
                    if os.path.exists(schema_path):
                        with open(schema_path, "r") as f:
                            nextflow_schema = json.load(f)
                            samplesheet_props = nextflow_schema["items"]["properties"]
                            fields = [{"id": k, "type": v.get("format")} for k, v in samplesheet_props.items()]
                            header = delimiter.join([f["id"] for f in fields]) + "\n"
                            body_start = f"{{{{#{key}}}}}\n"
                            body_end = f"\n{{{{/{key}}}}}"
                            body = delimiter.join([f'{{{{{f["id"]}}}}}' for f in fields])
                            template = header + body_start + body + body_end
                            samplesheet_input = {
                                "id": key,
                                "schema": {"items": {"fields": fields}},
                                "template": template,
                                "extension": extension,
                            }
                            inputs.append(samplesheet_input)
                else:
                    inputs.append({"id": key, "schema": {"type": items.get("format")}})
        return inputs
