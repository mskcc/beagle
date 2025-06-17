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
        defs = nextflow_schema["definitions"]
        for key, val in defs.items():
            props = defs[key]["properties"]
            properties.update(props)
            for key, items in props.items():
                schema_path = os.path.join(location, f"assets/schema_{key}.json")
                if os.path.exists(schema_path):
                    schemes[key] = schema_path
        # Check for sample-sheet CLI inputs
        inputs = [
            {"id": key, "schema": {"type": val.get("format")}}
            for key, val in properties.items()
            if key not in schemes.keys()
        ]
        # Check Assets for sample sheet schemas
        for schema, file in schemes.items():
            with open(file, "r") as f:
                nextflow_schema = json.load(f)
                samplesheet_props = nextflow_schema["items"]["properties"]
                fields = [{"id": key, "type": val.get("format")} for key, val in samplesheet_props.items()]
                header = "\t".join([f["id"] for f in fields]) + "\n"
                body_start = f"{{{{#{schema}}}}}\n"
                body_end = f"\n{{{{/{schema}}}}}"
                body = "\t".join([f'{{{{{f["id"]}}}}}' for f in fields])
                template = header + body_start + body + body_end
                samplesheet_input = {"id": schema, "schema": {"items": {"fields": fields}}, "template": template}
                inputs.append(samplesheet_input)
        return inputs
