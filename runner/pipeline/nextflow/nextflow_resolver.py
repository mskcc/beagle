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
        schemes = {}
        properties = {}
        defs = nextflow_schema.get("$defs")
        if not defs:
            defs = nextflow_schema.get("definitions")
        # loop over definition properties
        for key, val in defs.items():
            props = defs[key]["properties"]
            properties.update(props)
            for key, items in props.items():
                # see if property has a schema
                schema = props[key].get("schema")
                mimetype = props[key].get("mimetype")
                #TODO this should probably be it's own function with a mapping of mimetype to delimiter
                if mimetype:
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
                if schema:
                    schema_path = os.path.join(location, schema)
                    if os.path.exists(schema_path):
                        schemes[key] = schema_path
        # properties without schemas are regular inputs
        inputs = [
            {"id": key, "schema": {"type": val.get("format")}}
            for key, val in properties.items()
            if key not in schemes.keys()
        ]
        # add schema template to inputs
        for schema, file in schemes.items():
            with open(file, "r") as f:
                nextflow_schema = json.load(f)
                samplesheet_props = nextflow_schema["items"]["properties"]
                fields = [{"id": key, "type": val.get("format")} for key, val in samplesheet_props.items()]
                header = delimiter.join([f["id"] for f in fields]) + "\n"
                body_start = f"{{{{#{schema}}}}}\n"
                body_end = f"\n{{{{/{schema}}}}}"
                body = delimiter.join([f'{{{{{f["id"]}}}}}' for f in fields])
                template = header + body_start + body + body_end
                samplesheet_input = {"id": schema, "schema": {"items": {"fields": fields}}, "template": template, "extension": extension}
                inputs.append(samplesheet_input)
        return inputs
