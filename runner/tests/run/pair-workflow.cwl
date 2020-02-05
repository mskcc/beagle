{
  "cwlVersion" : "v1.0",
  "inputs" : [ {
    "id" : "db_files",
    "type" : {
      "fields" : {
        "bait_intervals" : "File",
        "conpair_markers" : "string",
        "conpair_markers_bed" : "string",
        "custom_enst" : "string",
        "facets_snps" : "File",
        "fp_genotypes" : "File",
        "fp_intervals" : "File",
        "hotspot_list" : "string",
        "hotspot_list_maf" : "File",
        "hotspot_vcf" : "string",
        "refseq" : "File",
        "target_intervals" : "File",
        "vep_data" : "string",
        "vep_path" : "string"
      },
      "type" : "record"
    }
  }, {
    "id" : "ref_fasta",
    "type" : "File",
    "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
  }, {
    "id" : "mouse_fasta",
    "type" : "File",
    "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
  }, {
    "id" : "hapmap",
    "type" : "File",
    "secondaryFiles" : [ ".idx" ]
  }, {
    "id" : "dbsnp",
    "type" : "File",
    "secondaryFiles" : [ ".idx" ]
  }, {
    "id" : "indels_1000g",
    "type" : "File",
    "secondaryFiles" : [ ".idx" ]
  }, {
    "id" : "snps_1000g",
    "type" : "File",
    "secondaryFiles" : [ ".idx" ]
  }, {
    "id" : "cosmic",
    "type" : "File",
    "secondaryFiles" : [ ".idx" ]
  }, {
    "id" : "exac_filter",
    "type" : "File",
    "secondaryFiles" : [ ".tbi" ]
  }, {
    "id" : "curated_bams",
    "type" : {
      "items" : "File",
      "type" : "array"
    },
    "secondaryFiles" : [ "^.bai" ]
  }, {
    "id" : "runparams",
    "type" : {
      "fields" : {
        "abra_ram_min" : "int",
        "abra_scratch" : "string",
        "complex_nn" : "float",
        "complex_tn" : "float",
        "covariates" : "string[]",
        "delly_type" : "string[]",
        "emit_original_quals" : "boolean",
        "facets_cval" : "int",
        "facets_pcval" : "int",
        "gatk_jar_path" : "string",
        "genome" : "string",
        "intervals" : "string[]",
        "mutect_dcov" : "int",
        "mutect_rf" : "string[]",
        "num_cpu_threads_per_data_thread" : "int",
        "num_threads" : "int",
        "opt_dup_pix_dist" : "string",
        "project_prefix" : "string",
        "scripts_bin" : "string",
        "tmp_dir" : "string"
      },
      "type" : "record"
    }
  }, {
    "id" : "pair",
    "type" : {
      "items" : {
        "fields" : {
          "CN" : "string",
          "ID" : "string",
          "LB" : "string",
          "PL" : "string",
          "PU" : "string[]",
          "R1" : "File[]",
          "R2" : "File[]",
          "RG_ID" : "string[]",
          "adapter" : "string",
          "adapter2" : "string",
          "bam" : "File[]",
          "bwa_output" : "string",
          "zR1" : "File[]",
          "zR2" : "File[]"
        },
        "type" : "record"
      },
      "type" : "array"
    }
  } ],
  "outputs" : [ {
    "id" : "bams",
    "type" : "File[]",
    "outputSource" : "alignment/bams",
    "secondaryFiles" : [ "^.bai" ]
  }, {
    "id" : "clstats1",
    "type" : {
      "items" : {
        "items" : "File",
        "type" : "array"
      },
      "type" : "array"
    },
    "outputSource" : "alignment/clstats1"
  }, {
    "id" : "clstats2",
    "type" : {
      "items" : {
        "items" : "File",
        "type" : "array"
      },
      "type" : "array"
    },
    "outputSource" : "alignment/clstats2"
  }, {
    "id" : "md_metrics",
    "type" : "File[]",
    "outputSource" : "alignment/md_metrics"
  }, {
    "id" : "as_metrics",
    "type" : "File[]",
    "outputSource" : "alignment/as_metrics"
  }, {
    "id" : "hs_metrics",
    "type" : "File[]",
    "outputSource" : "alignment/hs_metrics"
  }, {
    "id" : "insert_metrics",
    "type" : "File[]",
    "outputSource" : "alignment/insert_metrics"
  }, {
    "id" : "insert_pdf",
    "type" : "File[]",
    "outputSource" : "alignment/insert_pdf"
  }, {
    "id" : "per_target_coverage",
    "type" : "File[]",
    "outputSource" : "alignment/per_target_coverage"
  }, {
    "id" : "qual_metrics",
    "type" : "File[]",
    "outputSource" : "alignment/qual_metrics"
  }, {
    "id" : "qual_pdf",
    "type" : "File[]",
    "outputSource" : "alignment/qual_pdf"
  }, {
    "id" : "doc_basecounts",
    "type" : "File[]",
    "outputSource" : "alignment/doc_basecounts"
  }, {
    "id" : "gcbias_pdf",
    "type" : "File[]",
    "outputSource" : "alignment/gcbias_pdf"
  }, {
    "id" : "gcbias_metrics",
    "type" : "File[]",
    "outputSource" : "alignment/gcbias_metrics"
  }, {
    "id" : "gcbias_summary",
    "type" : "File[]",
    "outputSource" : "alignment/gcbias_summary"
  }, {
    "id" : "conpair_pileups",
    "type" : "File[]",
    "outputSource" : "alignment/conpair_pileup"
  }, {
    "id" : "mutect_vcf",
    "type" : "File",
    "outputSource" : "variant_calling/mutect_vcf"
  }, {
    "id" : "mutect_callstats",
    "type" : "File",
    "outputSource" : "variant_calling/mutect_callstats"
  }, {
    "id" : "vardict_vcf",
    "type" : "File",
    "outputSource" : "variant_calling/vardict_vcf"
  }, {
    "id" : "combine_vcf",
    "type" : "File",
    "outputSource" : "variant_calling/combine_vcf",
    "secondaryFiles" : [ ".tbi" ]
  }, {
    "id" : "annotate_vcf",
    "type" : "File",
    "outputSource" : "variant_calling/annotate_vcf"
  }, {
    "id" : "vardict_norm_vcf",
    "type" : "File",
    "outputSource" : "variant_calling/vardict_norm_vcf",
    "secondaryFiles" : [ ".tbi" ]
  }, {
    "id" : "mutect_norm_vcf",
    "type" : "File",
    "outputSource" : "variant_calling/mutect_norm_vcf",
    "secondaryFiles" : [ ".tbi" ]
  }, {
    "id" : "facets_png",
    "type" : "File[]",
    "outputSource" : "variant_calling/facets_png"
  }, {
    "id" : "facets_txt_hisens",
    "type" : "File",
    "outputSource" : "variant_calling/facets_txt_hisens"
  }, {
    "id" : "facets_txt_purity",
    "type" : "File",
    "outputSource" : "variant_calling/facets_txt_purity"
  }, {
    "id" : "facets_out",
    "type" : "File[]",
    "outputSource" : "variant_calling/facets_out"
  }, {
    "id" : "facets_rdata",
    "type" : "File[]",
    "outputSource" : "variant_calling/facets_rdata"
  }, {
    "id" : "facets_seg",
    "type" : "File[]",
    "outputSource" : "variant_calling/facets_seg"
  }, {
    "id" : "facets_counts",
    "type" : "File",
    "outputSource" : "variant_calling/facets_counts"
  }, {
    "id" : "maf",
    "type" : "File",
    "outputSource" : "maf_processing/maf"
  } ],
  "hints" : [ ],
  "requirements" : [ {
    "class" : "MultipleInputFeatureRequirement"
  }, {
    "class" : "ScatterFeatureRequirement"
  }, {
    "class" : "StepInputExpressionRequirement"
  }, {
    "class" : "SubworkflowFeatureRequirement"
  }, {
    "class" : "InlineJavascriptRequirement"
  } ],
  "successCodes" : [ ],
  "steps" : [ {
    "id" : "alignment",
    "run" : {
      "cwlVersion" : "v1.0",
      "inputs" : [ {
        "id" : "pair",
        "type" : {
          "items" : {
            "fields" : {
              "CN" : "string",
              "ID" : "string",
              "LB" : "string",
              "PL" : "string",
              "PU" : "string[]",
              "R1" : "File[]",
              "R2" : "File[]",
              "RG_ID" : "string[]",
              "adapter" : "string",
              "adapter2" : "string",
              "bam" : "File[]",
              "bwa_output" : "string",
              "zR1" : "File[]",
              "zR2" : "File[]"
            },
            "type" : "record"
          },
          "type" : "array"
        }
      }, {
        "id" : "genome",
        "type" : "string"
      }, {
        "id" : "intervals",
        "type" : "string[]"
      }, {
        "id" : "opt_dup_pix_dist",
        "type" : "string"
      }, {
        "id" : "hapmap",
        "type" : "File",
        "secondaryFiles" : [ ".idx" ]
      }, {
        "id" : "dbsnp",
        "type" : "File",
        "secondaryFiles" : [ ".idx" ]
      }, {
        "id" : "indels_1000g",
        "type" : "File",
        "secondaryFiles" : [ ".idx" ]
      }, {
        "id" : "snps_1000g",
        "type" : "File",
        "secondaryFiles" : [ ".idx" ]
      }, {
        "id" : "covariates",
        "type" : "string[]"
      }, {
        "id" : "abra_ram_min",
        "type" : "int"
      }, {
        "id" : "gatk_jar_path",
        "type" : "string"
      }, {
        "id" : "bait_intervals",
        "type" : "File"
      }, {
        "id" : "target_intervals",
        "type" : "File"
      }, {
        "id" : "fp_intervals",
        "type" : "File"
      }, {
        "id" : "ref_fasta",
        "type" : "File",
        "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
      }, {
        "id" : "mouse_fasta",
        "type" : "File",
        "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
      }, {
        "id" : "conpair_markers_bed",
        "type" : "string"
      } ],
      "outputs" : [ {
        "id" : "bams",
        "type" : "File[]",
        "outputSource" : "realignment/outbams",
        "secondaryFiles" : [ "^.bai" ]
      }, {
        "id" : "clstats1",
        "type" : {
          "items" : {
            "items" : "File",
            "type" : "array"
          },
          "type" : "array"
        },
        "outputSource" : "sample_alignment/clstats1"
      }, {
        "id" : "clstats2",
        "type" : {
          "items" : {
            "items" : "File",
            "type" : "array"
          },
          "type" : "array"
        },
        "outputSource" : "sample_alignment/clstats2"
      }, {
        "id" : "md_metrics",
        "type" : "File[]",
        "outputSource" : "sample_alignment/md_metrics"
      }, {
        "id" : "as_metrics",
        "type" : "File[]",
        "outputSource" : "sample_alignment/as_metrics"
      }, {
        "id" : "hs_metrics",
        "type" : "File[]",
        "outputSource" : "sample_alignment/hs_metrics"
      }, {
        "id" : "insert_metrics",
        "type" : "File[]",
        "outputSource" : "sample_alignment/insert_metrics"
      }, {
        "id" : "insert_pdf",
        "type" : "File[]",
        "outputSource" : "sample_alignment/insert_pdf"
      }, {
        "id" : "per_target_coverage",
        "type" : "File[]",
        "outputSource" : "sample_alignment/per_target_coverage"
      }, {
        "id" : "doc_basecounts",
        "type" : "File[]",
        "outputSource" : "sample_alignment/doc_basecounts"
      }, {
        "id" : "gcbias_pdf",
        "type" : "File[]",
        "outputSource" : "sample_alignment/gcbias_pdf"
      }, {
        "id" : "gcbias_metrics",
        "type" : "File[]",
        "outputSource" : "sample_alignment/gcbias_metrics"
      }, {
        "id" : "gcbias_summary",
        "type" : "File[]",
        "outputSource" : "sample_alignment/gcbias_summary"
      }, {
        "id" : "conpair_pileup",
        "type" : "File[]",
        "outputSource" : "sample_alignment/conpair_pileup"
      }, {
        "id" : "covint_list",
        "type" : "File",
        "outputSource" : "realignment/covint_list"
      }, {
        "id" : "bed",
        "type" : "File",
        "outputSource" : "realignment/covint_bed"
      }, {
        "id" : "qual_metrics",
        "type" : "File[]",
        "outputSource" : "realignment/qual_metrics"
      }, {
        "id" : "qual_pdf",
        "type" : "File[]",
        "outputSource" : "realignment/qual_pdf"
      } ],
      "hints" : [ ],
      "requirements" : [ {
        "class" : "MultipleInputFeatureRequirement"
      }, {
        "class" : "ScatterFeatureRequirement"
      }, {
        "class" : "SubworkflowFeatureRequirement"
      }, {
        "class" : "InlineJavascriptRequirement"
      } ],
      "successCodes" : [ ],
      "steps" : [ {
        "id" : "sample_alignment",
        "run" : {
          "cwlVersion" : "v1.0",
          "inputs" : [ {
            "id" : "sample",
            "type" : {
              "fields" : {
                "CN" : "string",
                "ID" : "string",
                "LB" : "string",
                "PL" : "string",
                "PU" : "string[]",
                "R1" : "File[]",
                "R2" : "File[]",
                "RG_ID" : "string[]",
                "adapter" : "string",
                "adapter2" : "string",
                "bam" : "File[]",
                "bwa_output" : "string",
                "zR1" : "File[]",
                "zR2" : "File[]"
              },
              "type" : "record"
            }
          }, {
            "id" : "ref_fasta",
            "type" : "File",
            "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
          }, {
            "id" : "mouse_fasta",
            "type" : "File",
            "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
          }, {
            "id" : "genome",
            "type" : "string"
          }, {
            "id" : "opt_dup_pix_dist",
            "type" : "string"
          }, {
            "id" : "bait_intervals",
            "type" : "File"
          }, {
            "id" : "target_intervals",
            "type" : "File"
          }, {
            "id" : "fp_intervals",
            "type" : "File"
          }, {
            "id" : "conpair_markers_bed",
            "type" : "string"
          }, {
            "id" : "gatk_jar_path",
            "type" : "string"
          } ],
          "outputs" : [ {
            "id" : "clstats1",
            "type" : "File[]",
            "outputSource" : "align/clstats1"
          }, {
            "id" : "clstats2",
            "type" : "File[]",
            "outputSource" : "align/clstats2"
          }, {
            "id" : "bam",
            "type" : "File",
            "outputSource" : "mark_duplicates/bam"
          }, {
            "id" : "md_metrics",
            "type" : "File",
            "outputSource" : "mark_duplicates/mdmetrics"
          }, {
            "id" : "as_metrics",
            "type" : "File",
            "outputSource" : "gather_metrics/as_metrics"
          }, {
            "id" : "hs_metrics",
            "type" : "File",
            "outputSource" : "gather_metrics/hs_metrics"
          }, {
            "id" : "insert_metrics",
            "type" : "File",
            "outputSource" : "gather_metrics/insert_metrics"
          }, {
            "id" : "insert_pdf",
            "type" : "File",
            "outputSource" : "gather_metrics/insert_pdf"
          }, {
            "id" : "per_target_coverage",
            "type" : "File",
            "outputSource" : "gather_metrics/per_target_coverage"
          }, {
            "id" : "doc_basecounts",
            "type" : "File",
            "outputSource" : "gather_metrics/doc_basecounts"
          }, {
            "id" : "gcbias_pdf",
            "type" : "File",
            "outputSource" : "gather_metrics/gcbias_pdf"
          }, {
            "id" : "gcbias_metrics",
            "type" : "File",
            "outputSource" : "gather_metrics/gcbias_metrics"
          }, {
            "id" : "gcbias_summary",
            "type" : "File",
            "outputSource" : "gather_metrics/gcbias_summary"
          }, {
            "id" : "conpair_pileup",
            "type" : "File",
            "outputSource" : "gather_metrics/conpair_pileup"
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "MultipleInputFeatureRequirement"
          }, {
            "class" : "ScatterFeatureRequirement"
          }, {
            "class" : "SubworkflowFeatureRequirement"
          }, {
            "class" : "InlineJavascriptRequirement"
          }, {
            "class" : "StepInputExpressionRequirement"
          } ],
          "successCodes" : [ ],
          "steps" : [ {
            "id" : "get_sample_info",
            "run" : {
              "inputs" : [ {
                "id" : "sample",
                "type" : {
                  "fields" : {
                    "CN" : "string",
                    "ID" : "string",
                    "LB" : "string",
                    "PL" : "string",
                    "PU" : "string[]",
                    "R1" : "File[]",
                    "R2" : "File[]",
                    "RG_ID" : "string[]",
                    "adapter" : "string",
                    "adapter2" : "string",
                    "bam" : "File[]",
                    "bwa_output" : "string",
                    "zR1" : "File[]",
                    "zR2" : "File[]"
                  },
                  "type" : "record"
                }
              } ],
              "outputs" : [ {
                "id" : "CN",
                "type" : "string"
              }, {
                "id" : "LB",
                "type" : "string"
              }, {
                "id" : "ID",
                "type" : "string"
              }, {
                "id" : "PL",
                "type" : "string"
              }, {
                "id" : "PU",
                "type" : "string[]"
              }, {
                "id" : "zPU",
                "type" : {
                  "items" : {
                    "items" : "string",
                    "type" : "array"
                  },
                  "type" : "array"
                }
              }, {
                "id" : "R1",
                "type" : "File[]"
              }, {
                "id" : "R2",
                "type" : "File[]"
              }, {
                "id" : "zR1",
                "type" : "File[]"
              }, {
                "id" : "zR2",
                "type" : "File[]"
              }, {
                "id" : "bam",
                "type" : "File[]"
              }, {
                "id" : "RG_ID",
                "type" : "string[]"
              }, {
                "id" : "adapter",
                "type" : "string"
              }, {
                "id" : "adapter2",
                "type" : "string"
              }, {
                "id" : "bwa_output",
                "type" : "string"
              } ],
              "hints" : [ ],
              "requirements" : [ ],
              "successCodes" : [ ],
              "expression" : "${ var sample_object = {}; for(var key in inputs.sample){ sample_object[key] = inputs.sample[key] } sample_object['zPU'] = []; if(sample_object['zR1'].length != 0 && sample_object['zR2'].length != 0 ){ sample_object['zPU'] = [sample_object['PU']]; } return sample_object; }",
              "id" : "get_sample_info",
              "class" : "ExpressionTool"
            },
            "in" : [ {
              "id" : "sample",
              "source" : "sample"
            } ],
            "out" : [ {
              "id" : "CN"
            }, {
              "id" : "LB"
            }, {
              "id" : "ID"
            }, {
              "id" : "PL"
            }, {
              "id" : "PU"
            }, {
              "id" : "zPU"
            }, {
              "id" : "R1"
            }, {
              "id" : "R2"
            }, {
              "id" : "zR1"
            }, {
              "id" : "zR2"
            }, {
              "id" : "bam"
            }, {
              "id" : "RG_ID"
            }, {
              "id" : "adapter"
            }, {
              "id" : "adapter2"
            }, {
              "id" : "bwa_output"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "resolve_pdx",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "r1",
                "type" : "File[]"
              }, {
                "id" : "r2",
                "type" : "File[]"
              }, {
                "id" : "sample_id",
                "type" : "string"
              }, {
                "id" : "lane_id",
                "type" : "string[]"
              }, {
                "id" : "mouse_reference",
                "type" : "File",
                "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai" ]
              }, {
                "id" : "human_reference",
                "type" : "File",
                "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai" ]
              } ],
              "outputs" : [ {
                "id" : "disambiguate_bam",
                "type" : "File",
                "outputSource" : "run_disambiguate/disambiguate_a_bam"
              }, {
                "id" : "summary",
                "type" : "File",
                "outputSource" : "run_disambiguate/summary"
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "StepInputExpressionRequirement"
              }, {
                "class" : "MultipleInputFeatureRequirement"
              }, {
                "class" : "ScatterFeatureRequirement"
              }, {
                "class" : "SubworkflowFeatureRequirement"
              }, {
                "class" : "InlineJavascriptRequirement"
              } ],
              "successCodes" : [ ],
              "steps" : [ {
                "id" : "align_to_human",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "reference_sequence",
                    "type" : "File",
                    "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai" ]
                  }, {
                    "id" : "r1",
                    "type" : "File[]"
                  }, {
                    "id" : "r2",
                    "type" : "File[]"
                  }, {
                    "id" : "sample_id",
                    "type" : "string"
                  }, {
                    "id" : "lane_id",
                    "type" : "string[]"
                  } ],
                  "outputs" : [ {
                    "id" : "sample_id_output",
                    "type" : [ "string", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "outputSource" : [ "bwa_sort/sample_id_output" ]
                  }, {
                    "id" : "output_md_metrics",
                    "type" : "File",
                    "outputSource" : [ "gatk_markduplicatesgatk/output_md_metrics" ]
                  }, {
                    "id" : "output_merge_sort_bam",
                    "type" : "File",
                    "outputSource" : [ "samtools_merge/output_file" ]
                  }, {
                    "id" : "output_md_bam",
                    "type" : "File",
                    "outputSource" : [ "gatk_markduplicatesgatk/output_md_bam" ]
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "SubworkflowFeatureRequirement"
                  }, {
                    "class" : "ScatterFeatureRequirement"
                  }, {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "StepInputExpressionRequirement"
                  } ],
                  "successCodes" : [ ],
                  "steps" : [ {
                    "id" : "samtools_merge",
                    "run" : {
                      "cwlVersion" : "v1.0",
                      "inputs" : [ {
                        "id" : "input_bams",
                        "type" : "File[]",
                        "inputBinding" : {
                          "position" : 2
                        },
                        "doc" : "Input array containing files to be merged"
                      } ],
                      "outputs" : [ {
                        "id" : "output_file",
                        "type" : "File",
                        "outputBinding" : {
                          "glob" : "*merged.bam"
                        }
                      } ],
                      "hints" : [ ],
                      "requirements" : [ {
                        "class" : "ResourceRequirement",
                        "ramMin" : 32000,
                        "coresMin" : 4
                      }, {
                        "class" : "DockerRequirement",
                        "dockerPull" : "mjblow/samtools-1.9:latest"
                      }, {
                        "class" : "InlineJavascriptRequirement"
                      } ],
                      "successCodes" : [ ],
                      "baseCommand" : [ "samtools", "merge" ],
                      "arguments" : [ {
                        "position" : 0,
                        "valueFrom" : "$(inputs.input_bams[0].basename.replace('bam', 'merged.bam'))"
                      }, {
                        "position" : 0,
                        "prefix" : "-test"
                      } ],
                      "dct:creator" : {
                        "foaf:mbox" : "mailto:bolipatc@mskcc.org",
                        "foaf:name" : "C. Allan Bolipata"
                      },
                      "dct:contributor" : {
                        "foaf:mbox" : "mailto:bolipatc@mskcc.org",
                        "foaf:name" : "C. Allan Bolipata"
                      },
                      "class" : "CommandLineTool"
                    },
                    "in" : [ {
                      "id" : "input_bams",
                      "source" : [ "bwa_sort/output_file" ]
                    } ],
                    "out" : [ {
                      "id" : "output_file"
                    } ],
                    "hints" : [ ],
                    "requirements" : [ ]
                  }, {
                    "id" : "bwa_sort",
                    "run" : {
                      "cwlVersion" : "v1.0",
                      "inputs" : [ {
                        "id" : "reference_sequence",
                        "type" : "File",
                        "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai" ]
                      }, {
                        "id" : "read_pair",
                        "type" : "File[]"
                      }, {
                        "id" : "sample_id",
                        "type" : "string"
                      }, {
                        "id" : "lane_id",
                        "type" : "string"
                      } ],
                      "outputs" : [ {
                        "id" : "output_file",
                        "type" : "File",
                        "outputSource" : [ "samtools_sort/output_file" ]
                      }, {
                        "id" : "sample_id_output",
                        "type" : "string",
                        "outputSource" : [ "sample_id" ]
                      }, {
                        "id" : "lane_id_output",
                        "type" : "string",
                        "outputSource" : [ "lane_id" ]
                      } ],
                      "hints" : [ ],
                      "requirements" : [ ],
                      "successCodes" : [ ],
                      "steps" : [ {
                        "id" : "bwa_mem",
                        "run" : {
                          "cwlVersion" : "v1.0",
                          "inputs" : [ {
                            "id" : "reads",
                            "type" : "File[]",
                            "inputBinding" : {
                              "position" : 3
                            }
                          }, {
                            "id" : "reference",
                            "type" : "File",
                            "inputBinding" : {
                              "position" : 2
                            },
                            "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai" ]
                          }, {
                            "id" : "sample_id",
                            "type" : "string"
                          }, {
                            "id" : "lane_id",
                            "type" : "string"
                          }, {
                            "id" : "A",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-A"
                            }
                          }, {
                            "id" : "B",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-B"
                            }
                          }, {
                            "id" : "C",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-C"
                            }
                          }, {
                            "id" : "E",
                            "type" : "int[]?",
                            "inputBinding" : {
                              "itemSeparator" : ",",
                              "position" : 0,
                              "prefix" : "-E"
                            }
                          }, {
                            "id" : "L",
                            "type" : "int[]?",
                            "inputBinding" : {
                              "itemSeparator" : ",",
                              "position" : 0,
                              "prefix" : "-L"
                            }
                          }, {
                            "id" : "M",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-M"
                            }
                          }, {
                            "id" : "O",
                            "type" : "int[]?",
                            "inputBinding" : {
                              "itemSeparator" : ",",
                              "position" : 0,
                              "prefix" : "-O"
                            }
                          }, {
                            "id" : "P",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-P"
                            }
                          }, {
                            "id" : "S",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-S"
                            }
                          }, {
                            "id" : "T",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-T"
                            }
                          }, {
                            "id" : "U",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-U"
                            }
                          }, {
                            "id" : "a",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-a"
                            }
                          }, {
                            "id" : "c",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-c"
                            }
                          }, {
                            "id" : "d",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-d"
                            }
                          }, {
                            "id" : "k",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-k"
                            }
                          }, {
                            "id" : "output",
                            "type" : "string?"
                          }, {
                            "id" : "p",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-p"
                            }
                          }, {
                            "id" : "r",
                            "type" : "float?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-r"
                            }
                          }, {
                            "id" : "v",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-v"
                            }
                          }, {
                            "id" : "w",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-w"
                            }
                          }, {
                            "id" : "y",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-y"
                            }
                          }, {
                            "id" : "D",
                            "type" : "float?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-D"
                            }
                          }, {
                            "id" : "W",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-W"
                            }
                          }, {
                            "id" : "m",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-m"
                            }
                          }, {
                            "id" : "e",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-e"
                            }
                          }, {
                            "id" : "x",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-x"
                            }
                          }, {
                            "id" : "H",
                            "type" : [ "File?", "string?" ],
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-H"
                            }
                          }, {
                            "id" : "j",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-j"
                            }
                          }, {
                            "id" : "h",
                            "type" : "int[]?",
                            "inputBinding" : {
                              "itemSeparator" : ",",
                              "position" : 0,
                              "prefix" : "-h"
                            }
                          }, {
                            "id" : "V",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-V"
                            }
                          }, {
                            "id" : "Y",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-Y"
                            }
                          }, {
                            "id" : "I",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-M"
                            }
                          } ],
                          "outputs" : [ {
                            "id" : "output_sam",
                            "type" : "File",
                            "outputBinding" : {
                              "glob" : "$(inputs.reads[0].basename.replace('fastq.gz', 'sam'))"
                            }
                          } ],
                          "hints" : [ ],
                          "requirements" : [ {
                            "class" : "ResourceRequirement",
                            "ramMin" : 32000,
                            "coresMin" : 4
                          }, {
                            "class" : "DockerRequirement",
                            "dockerPull" : "mskcc/bwa_mem:0.7.12"
                          }, {
                            "class" : "InlineJavascriptRequirement"
                          } ],
                          "successCodes" : [ ],
                          "stdout" : "$(inputs.reads[0].basename.replace('fastq.gz', 'sam'))",
                          "baseCommand" : [ "bwa", "mem" ],
                          "arguments" : [ {
                            "position" : 0,
                            "prefix" : "-R",
                            "valueFrom" : "@RG\\\\tID:$(inputs.lane_id)\\\\tSM:$(inputs.sample_id)\\\\tLB:$(inputs.sample_id)\\\\tPL:Illumina\\\\tPU:$(inputs.lane_id)"
                          }, {
                            "position" : 0,
                            "prefix" : "-t",
                            "valueFrom" : "$(runtime.cores)"
                          } ],
                          "class" : "CommandLineTool"
                        },
                        "in" : [ {
                          "id" : "reads",
                          "source" : [ "read_pair" ]
                        }, {
                          "id" : "reference",
                          "source" : "reference_sequence"
                        }, {
                          "id" : "sample_id",
                          "source" : "sample_id"
                        }, {
                          "id" : "lane_id",
                          "source" : "lane_id"
                        } ],
                        "out" : [ {
                          "id" : "output_sam"
                        } ],
                        "hints" : [ ],
                        "requirements" : [ ]
                      }, {
                        "id" : "samtools_sort",
                        "run" : {
                          "cwlVersion" : "v1.0",
                          "inputs" : [ {
                            "id" : "compression_level",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-l"
                            },
                            "doc" : "Set compression level, from 0 (uncompressed) to 9 (best)\n"
                          }, {
                            "id" : "input",
                            "type" : "File",
                            "inputBinding" : {
                              "position" : 1
                            },
                            "doc" : "Input bam file."
                          }, {
                            "id" : "memory",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-m"
                            },
                            "doc" : "Set maximum memory per thread; suffix K/M/G recognized [768M]\n"
                          }, {
                            "id" : "sort_by_name",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-n"
                            },
                            "doc" : "Sort by read names (i.e., the QNAME field) rather than by chromosomal coordinates."
                          }, {
                            "id" : "reference",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "--reference"
                            }
                          }, {
                            "id" : "output_format",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-O"
                            }
                          } ],
                          "outputs" : [ {
                            "id" : "output_file",
                            "type" : "File",
                            "outputBinding" : {
                              "glob" : "$(inputs.input.basename.replace('bam', 'sorted.bam'))"
                            }
                          } ],
                          "hints" : [ ],
                          "requirements" : [ {
                            "class" : "ResourceRequirement",
                            "ramMin" : 32000,
                            "coresMin" : 4
                          }, {
                            "class" : "DockerRequirement",
                            "dockerPull" : "quay.io/cancercollaboratory/dockstore-tool-samtools-sort:1.0"
                          }, {
                            "class" : "InlineJavascriptRequirement"
                          } ],
                          "successCodes" : [ ],
                          "baseCommand" : [ "samtools", "sort" ],
                          "arguments" : [ {
                            "position" : 0,
                            "prefix" : "-o",
                            "valueFrom" : "$(inputs.input.basename.replace('bam', 'sorted.bam'))"
                          }, {
                            "position" : 0,
                            "prefix" : "-@",
                            "valueFrom" : "$(runtime.cores)"
                          } ],
                          "dct:creator" : {
                            "@id" : "http://orcid.org/0000-0001-9102-5681",
                            "foaf:mbox" : "mailto:Andrey.Kartashov@cchmc.org",
                            "foaf:name" : "Andrey Kartashov"
                          },
                          "dct:contributor" : {
                            "foaf:mbox" : "mailto:ayang@oicr.on.ca",
                            "foaf:name" : "Andy Yang"
                          },
                          "doc" : "Sort alignments by leftmost coordinates, or by read name when -n is used. An appropriate @HD-SO sort order header tag will be added or an existing one updated if necessary.\n\nUsage: samtools sort [-l level] [-m maxMem] [-o out.bam] [-O format] [-n] -T out.prefix [-@ threads] [in.bam]\n\nOptions:\n-l INT\nSet the desired compression level for the final output file, ranging from 0 (uncompressed) or 1 (fastest but minimal compression) to 9 (best compression but slowest to write), similarly to gzip(1)'s compression level setting.\n\nIf -l is not used, the default compression level will apply.\n\n-m INT\nApproximately the maximum required memory per thread, specified either in bytes or with a K, M, or G suffix. [768 MiB]\n\n-n\nSort by read names (i.e., the QNAME field) rather than by chromosomal coordinates.\n\n-o FILE\nWrite the final sorted output to FILE, rather than to standard output.\n\n-O FORMAT\nWrite the final output as sam, bam, or cram.\n\nBy default, samtools tries to select a format based on the -o filename extension; if output is to standard output or no format can be deduced, -O must be used.\n\n-T PREFIX\nWrite temporary files to PREFIX.nnnn.bam. This option is required.\n\n-@ INT\nSet number of sorting and compression threads. By default, operation is single-threaded\n",
                          "dct:description" : "Developed at Cincinnati Children���s Hospital Medical Center for the CWL consortium http://commonwl.org/ Original URL: https://github.com/common-workflow-language/workflows",
                          "$namespaces" : null,
                          "class" : "CommandLineTool"
                        },
                        "in" : [ {
                          "id" : "input",
                          "source" : "sam_to_bam/output_bam"
                        } ],
                        "out" : [ {
                          "id" : "output_file"
                        } ],
                        "hints" : [ ],
                        "requirements" : [ ]
                      }, {
                        "id" : "sam_to_bam",
                        "run" : {
                          "cwlVersion" : "v1.0",
                          "inputs" : [ {
                            "id" : "bedoverlap",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-L"
                            },
                            "doc" : "only include reads overlapping this BED FILE [null]\n"
                          }, {
                            "id" : "cigar",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-m"
                            },
                            "doc" : "only include reads with number of CIGAR operations\nconsuming query sequence >= INT [0]\n"
                          }, {
                            "id" : "collapsecigar",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-B"
                            },
                            "doc" : "collapse the backward CIGAR operation\n"
                          }, {
                            "id" : "count",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-c"
                            },
                            "doc" : "print only the count of matching records\n"
                          }, {
                            "id" : "fastcompression",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-1"
                            },
                            "doc" : "use fast BAM compression (implies -b)\n"
                          }, {
                            "id" : "input",
                            "type" : "File",
                            "inputBinding" : {
                              "position" : 4
                            },
                            "doc" : "Input bam file.\n"
                          }, {
                            "id" : "isbam",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 2,
                              "prefix" : "-b"
                            },
                            "doc" : "output in BAM format\n"
                          }, {
                            "id" : "iscram",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 2,
                              "prefix" : "-C"
                            },
                            "doc" : "output in CRAM format\n"
                          }, {
                            "id" : "randomseed",
                            "type" : "float?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-s"
                            },
                            "doc" : "integer part sets seed of random number generator [0];\nrest sets fraction of templates to subsample [no subsampling]\n"
                          }, {
                            "id" : "readsingroup",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-r"
                            },
                            "doc" : "only include reads in read group STR [null]\n"
                          }, {
                            "id" : "readsingroupfile",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-R"
                            },
                            "doc" : "only include reads with read group listed in FILE [null]\n"
                          }, {
                            "id" : "readsinlibrary",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-l"
                            },
                            "doc" : "only include reads in library STR [null]\n"
                          }, {
                            "id" : "readsquality",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-q"
                            },
                            "doc" : "only include reads with mapping quality >= INT [0]\n"
                          }, {
                            "id" : "readswithbits",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-f"
                            },
                            "doc" : "only include reads with all bits set in INT set in FLAG [0]\n"
                          }, {
                            "id" : "readswithoutbits",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-F"
                            },
                            "doc" : "only include reads with none of the bits set in INT set in FLAG [0]\n"
                          }, {
                            "id" : "readtagtostrip",
                            "type" : "string[]?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-x"
                            },
                            "doc" : "read tag to strip (repeatable) [null]\n"
                          }, {
                            "id" : "referencefasta",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-T"
                            },
                            "doc" : "reference sequence FASTA FILE [null]\n"
                          }, {
                            "id" : "region",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 5
                            },
                            "doc" : "[region ...]\n"
                          }, {
                            "id" : "samheader",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-h"
                            },
                            "doc" : "include header in SAM output\n"
                          }, {
                            "id" : "threads",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-@"
                            },
                            "doc" : "number of BAM compression threads [0]\n"
                          }, {
                            "id" : "uncompressed",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-u"
                            },
                            "doc" : "uncompressed BAM output (implies -b)\n"
                          }, {
                            "id" : "samheaderonly",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-H"
                            }
                          }, {
                            "id" : "outputreadsnotselectedbyfilters",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-U"
                            }
                          }, {
                            "id" : "listingreferencenamesandlengths",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-t"
                            }
                          }, {
                            "id" : "readtagtostri",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-x"
                            }
                          }, {
                            "id" : "output_format",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-O"
                            }
                          } ],
                          "outputs" : [ {
                            "id" : "output_bam",
                            "type" : "File",
                            "outputBinding" : {
                              "glob" : "$(inputs.input.basename.replace('sam', 'bam'))"
                            }
                          } ],
                          "hints" : [ ],
                          "requirements" : [ {
                            "class" : "ResourceRequirement",
                            "ramMin" : 32000,
                            "coresMin" : 4
                          }, {
                            "class" : "DockerRequirement",
                            "dockerPull" : "quay.io/cancercollaboratory/dockstore-tool-samtools-view:1.0"
                          }, {
                            "class" : "InlineJavascriptRequirement"
                          } ],
                          "successCodes" : [ ],
                          "baseCommand" : [ "samtools", "view" ],
                          "arguments" : [ {
                            "position" : 0,
                            "prefix" : "-o",
                            "valueFrom" : "$(inputs.input.basename.replace('sam', 'bam'))"
                          }, {
                            "position" : 0,
                            "prefix" : "--threads",
                            "valueFrom" : "$(runtime.cores)"
                          } ],
                          "dct:creator" : {
                            "@id" : "http://orcid.org/0000-0001-9102-5681",
                            "foaf:mbox" : "mailto:Andrey.Kartashov@cchmc.org",
                            "foaf:name" : "Andrey Kartashov"
                          },
                          "dct:contributor" : {
                            "foaf:mbox" : "mailto:ayang@oicr.on.ca",
                            "foaf:name" : "Andy Yang"
                          },
                          "dct:description" : "Developed at Cincinnati Children���s Hospital Medical Center for the CWL consortium http://commonwl.org/ Original URL: https://github.com/common-workflow-language/workflows",
                          "doc" : "Prints alignments in the specified input alignment file.\n\nWith no options or regions specified, prints all alignments in the specified input alignment file (in SAM, BAM, or CRAM format) to standard output in SAM format (with no header).\n\nYou may specify one or more space-separated region specifications after the input filename to restrict output to only those alignments which overlap the specified region(s). Use of region specifications requires a coordinate-sorted and indexed input file (in BAM or CRAM format).\n\nThe -b, -C, -1, -u, -h, -H, and -c options change the output format from the default of headerless SAM, and the -o and -U options set the output file name(s).\n\nThe -t and -T options provide additional reference data. One of these two options is required when SAM input does not contain @SQ headers, and the -T option is required whenever writing CRAM output.\n\nThe -L, -r, -R, -q, -l, -m, -f, and -F options filter the alignments that will be included in the output to only those alignments that match certain criteria.\n\nThe -x, -B, and -s options modify the data which is contained in each alignment.\n\nFinally, the -@ option can be used to allocate additional threads to be used for compression, and the -? option requests a long help message.\n\nUsage: samtools view [options] in.bam|in.sam|in.cram [region...]\n\nRegions can be specified as: RNAME[:STARTPOS[-ENDPOS]] and all position coordinates are 1-based.\n\nImportant note: when multiple regions are given, some alignments may be output multiple times if they overlap more than one of the specified regions.\n\nExamples of region specifications:\n\n`chr1'\nOutput all alignments mapped to the reference sequence named `chr1' (i.e. @SQ SN:chr1) .\n\n`chr2:1000000'\nThe region on chr2 beginning at base position 1,000,000 and ending at the end of the chromosome.\n\n`chr3:1000-2000'\nThe 1001bp region on chr3 beginning at base position 1,000 and ending at base position 2,000 (including both end positions).\n\nOPTIONS:\n\n-b\nOutput in the BAM format.\n\n-C\nOutput in the CRAM format (requires -T).\n\n-1\nEnable fast BAM compression (implies -b).\n\n-u\nOutput uncompressed BAM. This option saves time spent on compression/decompression and is thus preferred when the output is piped to another samtools command.\n\n-h\nInclude the header in the output.\n\n-H\nOutput the header only.\n\n-c\nInstead of printing the alignments, only count them and print the total number. All filter options, such as -f, -F, and -q, are taken into account.\n\n-?\nOutput long help and exit immediately.\n\n-o FILE\nOutput to FILE [stdout].\n\n-U FILE\nWrite alignments that are not selected by the various filter options to FILE. When this option is used, all alignments (or all alignments intersecting the regions specified) are written to either the output file or this file, but never both.\n\n-t FILE\nA tab-delimited FILE. Each line must contain the reference name in the first column and the length of the reference in the second column, with one line for each distinct reference. Any additional fields beyond the second column are ignored. This file also defines the order of the reference sequences in sorting. If you run: `samtools faidx <ref.fa>', the resulting index file <ref.fa>.fai can be used as this FILE.\n\n-T FILE\nA FASTA format reference FILE, optionally compressed by bgzip and ideally indexed by samtools faidx. If an index is not present, one will be generated for you.\n\n-L FILE\nOnly output alignments overlapping the input BED FILE [null].\n\n-r STR\nOnly output alignments in read group STR [null].\n\n-R FILE\nOutput alignments in read groups listed in FILE [null].\n\n-q INT\nSkip alignments with MAPQ smaller than INT [0].\n\n-l STR\nOnly output alignments in library STR [null].\n\n-m INT\nOnly output alignments with number of CIGAR bases consuming query sequence ��� INT [0]\n\n-f INT\nOnly output alignments with all bits set in INT present in the FLAG field. INT can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/) or in octal by beginning with `0' (i.e. /^0[0-7]+/) [0].\n\n-F INT\nDo not output alignments with any bits set in INT present in the FLAG field. INT can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/) or in octal by beginning with `0' (i.e. /^0[0-7]+/) [0].\n\n-x STR\nRead tag to exclude from output (repeatable) [null]\n\n-B\nCollapse the backward CIGAR operation.\n\n-s FLOAT\nInteger part is used to seed the random number generator [0]. Part after the decimal point sets the fraction of templates/pairs to subsample [no subsampling].\n\n-@ INT\nNumber of BAM compression threads to use in addition to main thread [0].\n\n-S\nIgnored for compatibility with previous samtools versions. Previously this option was required if input was in SAM format, but now the correct format is automatically detected by examining the first few characters of input.\n",
                          "class" : "CommandLineTool"
                        },
                        "in" : [ {
                          "id" : "input",
                          "source" : "bwa_mem/output_sam"
                        } ],
                        "out" : [ {
                          "id" : "output_bam"
                        } ],
                        "hints" : [ ],
                        "requirements" : [ ]
                      } ],
                      "id" : "bwa_sort",
                      "label" : "bwa_sort",
                      "class" : "Workflow"
                    },
                    "scatter" : [ "r1", "r2", "lane_id" ],
                    "scatterMethod" : "dotproduct",
                    "in" : [ {
                      "id" : "r1",
                      "source" : "r1"
                    }, {
                      "id" : "r2",
                      "source" : "r2"
                    }, {
                      "id" : "reference_sequence",
                      "source" : "reference_sequence"
                    }, {
                      "id" : "read_pair",
                      "valueFrom" : "${ var data = []; data.push(inputs.r1); data.push(inputs.r2); return data; }"
                    }, {
                      "id" : "sample_id",
                      "source" : "sample_id"
                    }, {
                      "id" : "lane_id",
                      "source" : "lane_id"
                    } ],
                    "out" : [ {
                      "id" : "output_file"
                    }, {
                      "id" : "sample_id_output"
                    }, {
                      "id" : "lane_id_output"
                    } ],
                    "hints" : [ ],
                    "requirements" : [ ]
                  }, {
                    "id" : "gatk_markduplicatesgatk",
                    "run" : {
                      "cwlVersion" : "v1.0",
                      "inputs" : [ {
                        "id" : "input",
                        "type" : "File",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--INPUT"
                        },
                        "doc" : "Input BAM file"
                      }, {
                        "id" : "arguments_file",
                        "type" : "File?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--arguments_file"
                        }
                      }, {
                        "id" : "assume_sort_order",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--ASSUME_SORT_ORDER"
                        }
                      }, {
                        "id" : "assume_sorted",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--ASSUME_SORTED"
                        }
                      }, {
                        "id" : "barcode_tag",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--BARCODE_TAG"
                        }
                      }, {
                        "id" : "clear_dt",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--CLEAR_DT"
                        }
                      }, {
                        "id" : "comment",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--COMMENT"
                        }
                      }, {
                        "id" : "duplex_umi",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--DUPLEX_UMI"
                        }
                      }, {
                        "id" : "duplicate_scoring_strategy",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--DUPLICATE_SCORING_STRATEGY"
                        }
                      }, {
                        "id" : "max_file_hendles_for_read_ends_map",
                        "type" : "int?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--MAX_FILE_HANDLES_FOR_READ_ENDS_MAP"
                        }
                      }, {
                        "id" : "max_optical_duplicate_set_size",
                        "type" : "float?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--MAX_OPTICAL_DUPLICATE_SET_SIZE"
                        }
                      }, {
                        "id" : "max_sequences_for_disk_read_ends_map",
                        "type" : "int?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--MAX_SEQUENCES_FOR_DISK_READ_ENDS_MAP"
                        }
                      }, {
                        "id" : "molecular_identifier_tag",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--MOLECULAR_IDENTIFIER_TAG"
                        }
                      }, {
                        "id" : "optical_duplicate_pixel_distance",
                        "type" : "int?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--OPTICAL_DUPLICATE_PIXEL_DISTANCE"
                        }
                      }, {
                        "id" : "program_group_command_line",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--PROGRAM_GROUP_COMMAND_LINE"
                        }
                      }, {
                        "id" : "program_group_name",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--PROGRAM_GROUP_NAME"
                        }
                      }, {
                        "id" : "program_group_version",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--PROGRAM_GROUP_VERSION"
                        }
                      }, {
                        "id" : "program_record_id",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--PROGRAM_RECORD_ID"
                        }
                      }, {
                        "id" : "read_name_regex",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--READ_NAME_REGEX"
                        }
                      }, {
                        "id" : "read_one_barcode_tag",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--READ_ONE_BARCODE_TAG"
                        }
                      }, {
                        "id" : "read_two_barcode_tag",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--READ_TWO_BARCODE_TAG"
                        }
                      }, {
                        "id" : "remove_duplicates",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--REMOVE_DUPLICATES"
                        }
                      }, {
                        "id" : "remove_sequencing_duplicates",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--REMOVE_SEQUENCING_DUPLICATES"
                        }
                      }, {
                        "id" : "sorting_collection_size_ratio",
                        "type" : "float?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--SORTING_COLLECTION_SIZE_RATIO"
                        }
                      }, {
                        "id" : "tag_duplicate_set_members",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--TAG_DUPLICATE_SET_MEMBERS"
                        }
                      }, {
                        "id" : "tagging_policy",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--TAGGING_POLICY"
                        }
                      } ],
                      "outputs" : [ {
                        "id" : "output_md_bam",
                        "type" : "File",
                        "outputBinding" : {
                          "glob" : "$(inputs.input.basename.replace('md.bam', 'bam'))"
                        },
                        "secondaryFiles" : [ "^.bai" ],
                        "doc" : "Output marked duplicate bam"
                      }, {
                        "id" : "output_md_metrics",
                        "type" : "File",
                        "outputBinding" : {
                          "glob" : "$(inputs.input.basename.replace('bam', 'md.metrics'))"
                        },
                        "doc" : "Output marked duplicate metrics"
                      } ],
                      "hints" : [ ],
                      "requirements" : [ {
                        "class" : "ResourceRequirement",
                        "ramMin" : 42000,
                        "coresMin" : 1
                      }, {
                        "class" : "DockerRequirement",
                        "dockerPull" : "broadinstitute/gatk:4.1.0.0"
                      }, {
                        "class" : "InlineJavascriptRequirement"
                      } ],
                      "successCodes" : [ ],
                      "baseCommand" : [ "gatk", "MarkDuplicates" ],
                      "arguments" : [ {
                        "position" : 0,
                        "prefix" : "--OUTPUT",
                        "valueFrom" : "$(inputs.input.basename.replace('md.bam', 'bam'))"
                      }, {
                        "position" : 0,
                        "prefix" : "--METRICS_FILE",
                        "valueFrom" : "$(inputs.input.basename.replace('bam', 'md.metrics'))"
                      }, {
                        "position" : 0,
                        "prefix" : "--TMP_DIR",
                        "valueFrom" : "."
                      }, {
                        "position" : 0,
                        "prefix" : "--ASSUME_SORT_ORDER",
                        "valueFrom" : "coordinate"
                      }, {
                        "position" : 0
                      }, {
                        "position" : 0,
                        "prefix" : "--CREATE_INDEX",
                        "valueFrom" : "true"
                      }, {
                        "position" : 0,
                        "prefix" : "--MAX_RECORDS_IN_RAM",
                        "valueFrom" : "50000"
                      }, {
                        "position" : 0,
                        "prefix" : "--java-options",
                        "valueFrom" : "-Xms$(parseInt(runtime.ram)/1900)g -Xmx$(parseInt(runtime.ram)/950)g"
                      } ],
                      "id" : "gatk_markduplicatesgatk",
                      "label" : "GATK MarkDuplicates",
                      "class" : "CommandLineTool"
                    },
                    "in" : [ {
                      "id" : "input",
                      "source" : "samtools_merge/output_file"
                    } ],
                    "out" : [ {
                      "id" : "output_md_bam"
                    }, {
                      "id" : "output_md_metrics"
                    } ],
                    "hints" : [ ],
                    "requirements" : [ ]
                  } ],
                  "id" : "align_sample",
                  "label" : "align_sample",
                  "class" : "Workflow"
                },
                "in" : [ {
                  "id" : "prefix",
                  "source" : "sample_id"
                }, {
                  "id" : "reference_sequence",
                  "source" : "human_reference"
                }, {
                  "id" : "r1",
                  "source" : "r1"
                }, {
                  "id" : "r2",
                  "source" : "r2"
                }, {
                  "id" : "sample_id",
                  "valueFrom" : "${ return inputs.prefix + \"_human\"; }"
                }, {
                  "id" : "lane_id",
                  "source" : "lane_id"
                } ],
                "out" : [ {
                  "id" : "output_merge_sort_bam"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "align_to_mouse",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "reference_sequence",
                    "type" : "File",
                    "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai" ]
                  }, {
                    "id" : "r1",
                    "type" : "File[]"
                  }, {
                    "id" : "r2",
                    "type" : "File[]"
                  }, {
                    "id" : "sample_id",
                    "type" : "string"
                  }, {
                    "id" : "lane_id",
                    "type" : "string[]"
                  } ],
                  "outputs" : [ {
                    "id" : "sample_id_output",
                    "type" : [ "string", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "outputSource" : [ "bwa_sort/sample_id_output" ]
                  }, {
                    "id" : "output_md_metrics",
                    "type" : "File",
                    "outputSource" : [ "gatk_markduplicatesgatk/output_md_metrics" ]
                  }, {
                    "id" : "output_merge_sort_bam",
                    "type" : "File",
                    "outputSource" : [ "samtools_merge/output_file" ]
                  }, {
                    "id" : "output_md_bam",
                    "type" : "File",
                    "outputSource" : [ "gatk_markduplicatesgatk/output_md_bam" ]
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "SubworkflowFeatureRequirement"
                  }, {
                    "class" : "ScatterFeatureRequirement"
                  }, {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "StepInputExpressionRequirement"
                  } ],
                  "successCodes" : [ ],
                  "steps" : [ {
                    "id" : "samtools_merge",
                    "run" : {
                      "cwlVersion" : "v1.0",
                      "inputs" : [ {
                        "id" : "input_bams",
                        "type" : "File[]",
                        "inputBinding" : {
                          "position" : 2
                        },
                        "doc" : "Input array containing files to be merged"
                      } ],
                      "outputs" : [ {
                        "id" : "output_file",
                        "type" : "File",
                        "outputBinding" : {
                          "glob" : "*merged.bam"
                        }
                      } ],
                      "hints" : [ ],
                      "requirements" : [ {
                        "class" : "ResourceRequirement",
                        "ramMin" : 32000,
                        "coresMin" : 4
                      }, {
                        "class" : "DockerRequirement",
                        "dockerPull" : "mjblow/samtools-1.9:latest"
                      }, {
                        "class" : "InlineJavascriptRequirement"
                      } ],
                      "successCodes" : [ ],
                      "baseCommand" : [ "samtools", "merge" ],
                      "arguments" : [ {
                        "position" : 0,
                        "valueFrom" : "$(inputs.input_bams[0].basename.replace('bam', 'merged.bam'))"
                      }, {
                        "position" : 0,
                        "prefix" : "-test"
                      } ],
                      "dct:creator" : {
                        "foaf:mbox" : "mailto:bolipatc@mskcc.org",
                        "foaf:name" : "C. Allan Bolipata"
                      },
                      "dct:contributor" : {
                        "foaf:mbox" : "mailto:bolipatc@mskcc.org",
                        "foaf:name" : "C. Allan Bolipata"
                      },
                      "class" : "CommandLineTool"
                    },
                    "in" : [ {
                      "id" : "input_bams",
                      "source" : [ "bwa_sort/output_file" ]
                    } ],
                    "out" : [ {
                      "id" : "output_file"
                    } ],
                    "hints" : [ ],
                    "requirements" : [ ]
                  }, {
                    "id" : "bwa_sort",
                    "run" : {
                      "cwlVersion" : "v1.0",
                      "inputs" : [ {
                        "id" : "reference_sequence",
                        "type" : "File",
                        "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai" ]
                      }, {
                        "id" : "read_pair",
                        "type" : "File[]"
                      }, {
                        "id" : "sample_id",
                        "type" : "string"
                      }, {
                        "id" : "lane_id",
                        "type" : "string"
                      } ],
                      "outputs" : [ {
                        "id" : "output_file",
                        "type" : "File",
                        "outputSource" : [ "samtools_sort/output_file" ]
                      }, {
                        "id" : "sample_id_output",
                        "type" : "string",
                        "outputSource" : [ "sample_id" ]
                      }, {
                        "id" : "lane_id_output",
                        "type" : "string",
                        "outputSource" : [ "lane_id" ]
                      } ],
                      "hints" : [ ],
                      "requirements" : [ ],
                      "successCodes" : [ ],
                      "steps" : [ {
                        "id" : "bwa_mem",
                        "run" : {
                          "cwlVersion" : "v1.0",
                          "inputs" : [ {
                            "id" : "reads",
                            "type" : "File[]",
                            "inputBinding" : {
                              "position" : 3
                            }
                          }, {
                            "id" : "reference",
                            "type" : "File",
                            "inputBinding" : {
                              "position" : 2
                            },
                            "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai" ]
                          }, {
                            "id" : "sample_id",
                            "type" : "string"
                          }, {
                            "id" : "lane_id",
                            "type" : "string"
                          }, {
                            "id" : "A",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-A"
                            }
                          }, {
                            "id" : "B",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-B"
                            }
                          }, {
                            "id" : "C",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-C"
                            }
                          }, {
                            "id" : "E",
                            "type" : "int[]?",
                            "inputBinding" : {
                              "itemSeparator" : ",",
                              "position" : 0,
                              "prefix" : "-E"
                            }
                          }, {
                            "id" : "L",
                            "type" : "int[]?",
                            "inputBinding" : {
                              "itemSeparator" : ",",
                              "position" : 0,
                              "prefix" : "-L"
                            }
                          }, {
                            "id" : "M",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-M"
                            }
                          }, {
                            "id" : "O",
                            "type" : "int[]?",
                            "inputBinding" : {
                              "itemSeparator" : ",",
                              "position" : 0,
                              "prefix" : "-O"
                            }
                          }, {
                            "id" : "P",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-P"
                            }
                          }, {
                            "id" : "S",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-S"
                            }
                          }, {
                            "id" : "T",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-T"
                            }
                          }, {
                            "id" : "U",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-U"
                            }
                          }, {
                            "id" : "a",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-a"
                            }
                          }, {
                            "id" : "c",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-c"
                            }
                          }, {
                            "id" : "d",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-d"
                            }
                          }, {
                            "id" : "k",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-k"
                            }
                          }, {
                            "id" : "output",
                            "type" : "string?"
                          }, {
                            "id" : "p",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-p"
                            }
                          }, {
                            "id" : "r",
                            "type" : "float?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-r"
                            }
                          }, {
                            "id" : "v",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-v"
                            }
                          }, {
                            "id" : "w",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-w"
                            }
                          }, {
                            "id" : "y",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-y"
                            }
                          }, {
                            "id" : "D",
                            "type" : "float?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-D"
                            }
                          }, {
                            "id" : "W",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-W"
                            }
                          }, {
                            "id" : "m",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-m"
                            }
                          }, {
                            "id" : "e",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-e"
                            }
                          }, {
                            "id" : "x",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-x"
                            }
                          }, {
                            "id" : "H",
                            "type" : [ "File?", "string?" ],
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-H"
                            }
                          }, {
                            "id" : "j",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-j"
                            }
                          }, {
                            "id" : "h",
                            "type" : "int[]?",
                            "inputBinding" : {
                              "itemSeparator" : ",",
                              "position" : 0,
                              "prefix" : "-h"
                            }
                          }, {
                            "id" : "V",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-V"
                            }
                          }, {
                            "id" : "Y",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-Y"
                            }
                          }, {
                            "id" : "I",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-M"
                            }
                          } ],
                          "outputs" : [ {
                            "id" : "output_sam",
                            "type" : "File",
                            "outputBinding" : {
                              "glob" : "$(inputs.reads[0].basename.replace('fastq.gz', 'sam'))"
                            }
                          } ],
                          "hints" : [ ],
                          "requirements" : [ {
                            "class" : "ResourceRequirement",
                            "ramMin" : 32000,
                            "coresMin" : 4
                          }, {
                            "class" : "DockerRequirement",
                            "dockerPull" : "mskcc/bwa_mem:0.7.12"
                          }, {
                            "class" : "InlineJavascriptRequirement"
                          } ],
                          "successCodes" : [ ],
                          "stdout" : "$(inputs.reads[0].basename.replace('fastq.gz', 'sam'))",
                          "baseCommand" : [ "bwa", "mem" ],
                          "arguments" : [ {
                            "position" : 0,
                            "prefix" : "-R",
                            "valueFrom" : "@RG\\\\tID:$(inputs.lane_id)\\\\tSM:$(inputs.sample_id)\\\\tLB:$(inputs.sample_id)\\\\tPL:Illumina\\\\tPU:$(inputs.lane_id)"
                          }, {
                            "position" : 0,
                            "prefix" : "-t",
                            "valueFrom" : "$(runtime.cores)"
                          } ],
                          "class" : "CommandLineTool"
                        },
                        "in" : [ {
                          "id" : "reads",
                          "source" : [ "read_pair" ]
                        }, {
                          "id" : "reference",
                          "source" : "reference_sequence"
                        }, {
                          "id" : "sample_id",
                          "source" : "sample_id"
                        }, {
                          "id" : "lane_id",
                          "source" : "lane_id"
                        } ],
                        "out" : [ {
                          "id" : "output_sam"
                        } ],
                        "hints" : [ ],
                        "requirements" : [ ]
                      }, {
                        "id" : "samtools_sort",
                        "run" : {
                          "cwlVersion" : "v1.0",
                          "inputs" : [ {
                            "id" : "compression_level",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-l"
                            },
                            "doc" : "Set compression level, from 0 (uncompressed) to 9 (best)\n"
                          }, {
                            "id" : "input",
                            "type" : "File",
                            "inputBinding" : {
                              "position" : 1
                            },
                            "doc" : "Input bam file."
                          }, {
                            "id" : "memory",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-m"
                            },
                            "doc" : "Set maximum memory per thread; suffix K/M/G recognized [768M]\n"
                          }, {
                            "id" : "sort_by_name",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-n"
                            },
                            "doc" : "Sort by read names (i.e., the QNAME field) rather than by chromosomal coordinates."
                          }, {
                            "id" : "reference",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "--reference"
                            }
                          }, {
                            "id" : "output_format",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-O"
                            }
                          } ],
                          "outputs" : [ {
                            "id" : "output_file",
                            "type" : "File",
                            "outputBinding" : {
                              "glob" : "$(inputs.input.basename.replace('bam', 'sorted.bam'))"
                            }
                          } ],
                          "hints" : [ ],
                          "requirements" : [ {
                            "class" : "ResourceRequirement",
                            "ramMin" : 32000,
                            "coresMin" : 4
                          }, {
                            "class" : "DockerRequirement",
                            "dockerPull" : "quay.io/cancercollaboratory/dockstore-tool-samtools-sort:1.0"
                          }, {
                            "class" : "InlineJavascriptRequirement"
                          } ],
                          "successCodes" : [ ],
                          "baseCommand" : [ "samtools", "sort" ],
                          "arguments" : [ {
                            "position" : 0,
                            "prefix" : "-o",
                            "valueFrom" : "$(inputs.input.basename.replace('bam', 'sorted.bam'))"
                          }, {
                            "position" : 0,
                            "prefix" : "-@",
                            "valueFrom" : "$(runtime.cores)"
                          } ],
                          "dct:creator" : {
                            "@id" : "http://orcid.org/0000-0001-9102-5681",
                            "foaf:mbox" : "mailto:Andrey.Kartashov@cchmc.org",
                            "foaf:name" : "Andrey Kartashov"
                          },
                          "dct:contributor" : {
                            "foaf:mbox" : "mailto:ayang@oicr.on.ca",
                            "foaf:name" : "Andy Yang"
                          },
                          "doc" : "Sort alignments by leftmost coordinates, or by read name when -n is used. An appropriate @HD-SO sort order header tag will be added or an existing one updated if necessary.\n\nUsage: samtools sort [-l level] [-m maxMem] [-o out.bam] [-O format] [-n] -T out.prefix [-@ threads] [in.bam]\n\nOptions:\n-l INT\nSet the desired compression level for the final output file, ranging from 0 (uncompressed) or 1 (fastest but minimal compression) to 9 (best compression but slowest to write), similarly to gzip(1)'s compression level setting.\n\nIf -l is not used, the default compression level will apply.\n\n-m INT\nApproximately the maximum required memory per thread, specified either in bytes or with a K, M, or G suffix. [768 MiB]\n\n-n\nSort by read names (i.e., the QNAME field) rather than by chromosomal coordinates.\n\n-o FILE\nWrite the final sorted output to FILE, rather than to standard output.\n\n-O FORMAT\nWrite the final output as sam, bam, or cram.\n\nBy default, samtools tries to select a format based on the -o filename extension; if output is to standard output or no format can be deduced, -O must be used.\n\n-T PREFIX\nWrite temporary files to PREFIX.nnnn.bam. This option is required.\n\n-@ INT\nSet number of sorting and compression threads. By default, operation is single-threaded\n",
                          "dct:description" : "Developed at Cincinnati Children���s Hospital Medical Center for the CWL consortium http://commonwl.org/ Original URL: https://github.com/common-workflow-language/workflows",
                          "$namespaces" : null,
                          "class" : "CommandLineTool"
                        },
                        "in" : [ {
                          "id" : "input",
                          "source" : "sam_to_bam/output_bam"
                        } ],
                        "out" : [ {
                          "id" : "output_file"
                        } ],
                        "hints" : [ ],
                        "requirements" : [ ]
                      }, {
                        "id" : "sam_to_bam",
                        "run" : {
                          "cwlVersion" : "v1.0",
                          "inputs" : [ {
                            "id" : "bedoverlap",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-L"
                            },
                            "doc" : "only include reads overlapping this BED FILE [null]\n"
                          }, {
                            "id" : "cigar",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-m"
                            },
                            "doc" : "only include reads with number of CIGAR operations\nconsuming query sequence >= INT [0]\n"
                          }, {
                            "id" : "collapsecigar",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-B"
                            },
                            "doc" : "collapse the backward CIGAR operation\n"
                          }, {
                            "id" : "count",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-c"
                            },
                            "doc" : "print only the count of matching records\n"
                          }, {
                            "id" : "fastcompression",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-1"
                            },
                            "doc" : "use fast BAM compression (implies -b)\n"
                          }, {
                            "id" : "input",
                            "type" : "File",
                            "inputBinding" : {
                              "position" : 4
                            },
                            "doc" : "Input bam file.\n"
                          }, {
                            "id" : "isbam",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 2,
                              "prefix" : "-b"
                            },
                            "doc" : "output in BAM format\n"
                          }, {
                            "id" : "iscram",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 2,
                              "prefix" : "-C"
                            },
                            "doc" : "output in CRAM format\n"
                          }, {
                            "id" : "randomseed",
                            "type" : "float?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-s"
                            },
                            "doc" : "integer part sets seed of random number generator [0];\nrest sets fraction of templates to subsample [no subsampling]\n"
                          }, {
                            "id" : "readsingroup",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-r"
                            },
                            "doc" : "only include reads in read group STR [null]\n"
                          }, {
                            "id" : "readsingroupfile",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-R"
                            },
                            "doc" : "only include reads with read group listed in FILE [null]\n"
                          }, {
                            "id" : "readsinlibrary",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-l"
                            },
                            "doc" : "only include reads in library STR [null]\n"
                          }, {
                            "id" : "readsquality",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-q"
                            },
                            "doc" : "only include reads with mapping quality >= INT [0]\n"
                          }, {
                            "id" : "readswithbits",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-f"
                            },
                            "doc" : "only include reads with all bits set in INT set in FLAG [0]\n"
                          }, {
                            "id" : "readswithoutbits",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-F"
                            },
                            "doc" : "only include reads with none of the bits set in INT set in FLAG [0]\n"
                          }, {
                            "id" : "readtagtostrip",
                            "type" : "string[]?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-x"
                            },
                            "doc" : "read tag to strip (repeatable) [null]\n"
                          }, {
                            "id" : "referencefasta",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-T"
                            },
                            "doc" : "reference sequence FASTA FILE [null]\n"
                          }, {
                            "id" : "region",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 5
                            },
                            "doc" : "[region ...]\n"
                          }, {
                            "id" : "samheader",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-h"
                            },
                            "doc" : "include header in SAM output\n"
                          }, {
                            "id" : "threads",
                            "type" : "int?",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-@"
                            },
                            "doc" : "number of BAM compression threads [0]\n"
                          }, {
                            "id" : "uncompressed",
                            "default" : false,
                            "type" : "boolean",
                            "inputBinding" : {
                              "position" : 1,
                              "prefix" : "-u"
                            },
                            "doc" : "uncompressed BAM output (implies -b)\n"
                          }, {
                            "id" : "samheaderonly",
                            "type" : "boolean?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-H"
                            }
                          }, {
                            "id" : "outputreadsnotselectedbyfilters",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-U"
                            }
                          }, {
                            "id" : "listingreferencenamesandlengths",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-t"
                            }
                          }, {
                            "id" : "readtagtostri",
                            "type" : "File?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-x"
                            }
                          }, {
                            "id" : "output_format",
                            "type" : "string?",
                            "inputBinding" : {
                              "position" : 0,
                              "prefix" : "-O"
                            }
                          } ],
                          "outputs" : [ {
                            "id" : "output_bam",
                            "type" : "File",
                            "outputBinding" : {
                              "glob" : "$(inputs.input.basename.replace('sam', 'bam'))"
                            }
                          } ],
                          "hints" : [ ],
                          "requirements" : [ {
                            "class" : "ResourceRequirement",
                            "ramMin" : 32000,
                            "coresMin" : 4
                          }, {
                            "class" : "DockerRequirement",
                            "dockerPull" : "quay.io/cancercollaboratory/dockstore-tool-samtools-view:1.0"
                          }, {
                            "class" : "InlineJavascriptRequirement"
                          } ],
                          "successCodes" : [ ],
                          "baseCommand" : [ "samtools", "view" ],
                          "arguments" : [ {
                            "position" : 0,
                            "prefix" : "-o",
                            "valueFrom" : "$(inputs.input.basename.replace('sam', 'bam'))"
                          }, {
                            "position" : 0,
                            "prefix" : "--threads",
                            "valueFrom" : "$(runtime.cores)"
                          } ],
                          "dct:creator" : {
                            "@id" : "http://orcid.org/0000-0001-9102-5681",
                            "foaf:mbox" : "mailto:Andrey.Kartashov@cchmc.org",
                            "foaf:name" : "Andrey Kartashov"
                          },
                          "dct:contributor" : {
                            "foaf:mbox" : "mailto:ayang@oicr.on.ca",
                            "foaf:name" : "Andy Yang"
                          },
                          "dct:description" : "Developed at Cincinnati Children���s Hospital Medical Center for the CWL consortium http://commonwl.org/ Original URL: https://github.com/common-workflow-language/workflows",
                          "doc" : "Prints alignments in the specified input alignment file.\n\nWith no options or regions specified, prints all alignments in the specified input alignment file (in SAM, BAM, or CRAM format) to standard output in SAM format (with no header).\n\nYou may specify one or more space-separated region specifications after the input filename to restrict output to only those alignments which overlap the specified region(s). Use of region specifications requires a coordinate-sorted and indexed input file (in BAM or CRAM format).\n\nThe -b, -C, -1, -u, -h, -H, and -c options change the output format from the default of headerless SAM, and the -o and -U options set the output file name(s).\n\nThe -t and -T options provide additional reference data. One of these two options is required when SAM input does not contain @SQ headers, and the -T option is required whenever writing CRAM output.\n\nThe -L, -r, -R, -q, -l, -m, -f, and -F options filter the alignments that will be included in the output to only those alignments that match certain criteria.\n\nThe -x, -B, and -s options modify the data which is contained in each alignment.\n\nFinally, the -@ option can be used to allocate additional threads to be used for compression, and the -? option requests a long help message.\n\nUsage: samtools view [options] in.bam|in.sam|in.cram [region...]\n\nRegions can be specified as: RNAME[:STARTPOS[-ENDPOS]] and all position coordinates are 1-based.\n\nImportant note: when multiple regions are given, some alignments may be output multiple times if they overlap more than one of the specified regions.\n\nExamples of region specifications:\n\n`chr1'\nOutput all alignments mapped to the reference sequence named `chr1' (i.e. @SQ SN:chr1) .\n\n`chr2:1000000'\nThe region on chr2 beginning at base position 1,000,000 and ending at the end of the chromosome.\n\n`chr3:1000-2000'\nThe 1001bp region on chr3 beginning at base position 1,000 and ending at base position 2,000 (including both end positions).\n\nOPTIONS:\n\n-b\nOutput in the BAM format.\n\n-C\nOutput in the CRAM format (requires -T).\n\n-1\nEnable fast BAM compression (implies -b).\n\n-u\nOutput uncompressed BAM. This option saves time spent on compression/decompression and is thus preferred when the output is piped to another samtools command.\n\n-h\nInclude the header in the output.\n\n-H\nOutput the header only.\n\n-c\nInstead of printing the alignments, only count them and print the total number. All filter options, such as -f, -F, and -q, are taken into account.\n\n-?\nOutput long help and exit immediately.\n\n-o FILE\nOutput to FILE [stdout].\n\n-U FILE\nWrite alignments that are not selected by the various filter options to FILE. When this option is used, all alignments (or all alignments intersecting the regions specified) are written to either the output file or this file, but never both.\n\n-t FILE\nA tab-delimited FILE. Each line must contain the reference name in the first column and the length of the reference in the second column, with one line for each distinct reference. Any additional fields beyond the second column are ignored. This file also defines the order of the reference sequences in sorting. If you run: `samtools faidx <ref.fa>', the resulting index file <ref.fa>.fai can be used as this FILE.\n\n-T FILE\nA FASTA format reference FILE, optionally compressed by bgzip and ideally indexed by samtools faidx. If an index is not present, one will be generated for you.\n\n-L FILE\nOnly output alignments overlapping the input BED FILE [null].\n\n-r STR\nOnly output alignments in read group STR [null].\n\n-R FILE\nOutput alignments in read groups listed in FILE [null].\n\n-q INT\nSkip alignments with MAPQ smaller than INT [0].\n\n-l STR\nOnly output alignments in library STR [null].\n\n-m INT\nOnly output alignments with number of CIGAR bases consuming query sequence ��� INT [0]\n\n-f INT\nOnly output alignments with all bits set in INT present in the FLAG field. INT can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/) or in octal by beginning with `0' (i.e. /^0[0-7]+/) [0].\n\n-F INT\nDo not output alignments with any bits set in INT present in the FLAG field. INT can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/) or in octal by beginning with `0' (i.e. /^0[0-7]+/) [0].\n\n-x STR\nRead tag to exclude from output (repeatable) [null]\n\n-B\nCollapse the backward CIGAR operation.\n\n-s FLOAT\nInteger part is used to seed the random number generator [0]. Part after the decimal point sets the fraction of templates/pairs to subsample [no subsampling].\n\n-@ INT\nNumber of BAM compression threads to use in addition to main thread [0].\n\n-S\nIgnored for compatibility with previous samtools versions. Previously this option was required if input was in SAM format, but now the correct format is automatically detected by examining the first few characters of input.\n",
                          "class" : "CommandLineTool"
                        },
                        "in" : [ {
                          "id" : "input",
                          "source" : "bwa_mem/output_sam"
                        } ],
                        "out" : [ {
                          "id" : "output_bam"
                        } ],
                        "hints" : [ ],
                        "requirements" : [ ]
                      } ],
                      "id" : "bwa_sort",
                      "label" : "bwa_sort",
                      "class" : "Workflow"
                    },
                    "scatter" : [ "r1", "r2", "lane_id" ],
                    "scatterMethod" : "dotproduct",
                    "in" : [ {
                      "id" : "r1",
                      "source" : "r1"
                    }, {
                      "id" : "r2",
                      "source" : "r2"
                    }, {
                      "id" : "reference_sequence",
                      "source" : "reference_sequence"
                    }, {
                      "id" : "read_pair",
                      "valueFrom" : "${ var data = []; data.push(inputs.r1); data.push(inputs.r2); return data; }"
                    }, {
                      "id" : "sample_id",
                      "source" : "sample_id"
                    }, {
                      "id" : "lane_id",
                      "source" : "lane_id"
                    } ],
                    "out" : [ {
                      "id" : "output_file"
                    }, {
                      "id" : "sample_id_output"
                    }, {
                      "id" : "lane_id_output"
                    } ],
                    "hints" : [ ],
                    "requirements" : [ ]
                  }, {
                    "id" : "gatk_markduplicatesgatk",
                    "run" : {
                      "cwlVersion" : "v1.0",
                      "inputs" : [ {
                        "id" : "input",
                        "type" : "File",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--INPUT"
                        },
                        "doc" : "Input BAM file"
                      }, {
                        "id" : "arguments_file",
                        "type" : "File?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--arguments_file"
                        }
                      }, {
                        "id" : "assume_sort_order",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--ASSUME_SORT_ORDER"
                        }
                      }, {
                        "id" : "assume_sorted",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--ASSUME_SORTED"
                        }
                      }, {
                        "id" : "barcode_tag",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--BARCODE_TAG"
                        }
                      }, {
                        "id" : "clear_dt",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--CLEAR_DT"
                        }
                      }, {
                        "id" : "comment",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--COMMENT"
                        }
                      }, {
                        "id" : "duplex_umi",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--DUPLEX_UMI"
                        }
                      }, {
                        "id" : "duplicate_scoring_strategy",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--DUPLICATE_SCORING_STRATEGY"
                        }
                      }, {
                        "id" : "max_file_hendles_for_read_ends_map",
                        "type" : "int?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--MAX_FILE_HANDLES_FOR_READ_ENDS_MAP"
                        }
                      }, {
                        "id" : "max_optical_duplicate_set_size",
                        "type" : "float?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--MAX_OPTICAL_DUPLICATE_SET_SIZE"
                        }
                      }, {
                        "id" : "max_sequences_for_disk_read_ends_map",
                        "type" : "int?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--MAX_SEQUENCES_FOR_DISK_READ_ENDS_MAP"
                        }
                      }, {
                        "id" : "molecular_identifier_tag",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--MOLECULAR_IDENTIFIER_TAG"
                        }
                      }, {
                        "id" : "optical_duplicate_pixel_distance",
                        "type" : "int?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--OPTICAL_DUPLICATE_PIXEL_DISTANCE"
                        }
                      }, {
                        "id" : "program_group_command_line",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--PROGRAM_GROUP_COMMAND_LINE"
                        }
                      }, {
                        "id" : "program_group_name",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--PROGRAM_GROUP_NAME"
                        }
                      }, {
                        "id" : "program_group_version",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--PROGRAM_GROUP_VERSION"
                        }
                      }, {
                        "id" : "program_record_id",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--PROGRAM_RECORD_ID"
                        }
                      }, {
                        "id" : "read_name_regex",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--READ_NAME_REGEX"
                        }
                      }, {
                        "id" : "read_one_barcode_tag",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--READ_ONE_BARCODE_TAG"
                        }
                      }, {
                        "id" : "read_two_barcode_tag",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--READ_TWO_BARCODE_TAG"
                        }
                      }, {
                        "id" : "remove_duplicates",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--REMOVE_DUPLICATES"
                        }
                      }, {
                        "id" : "remove_sequencing_duplicates",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--REMOVE_SEQUENCING_DUPLICATES"
                        }
                      }, {
                        "id" : "sorting_collection_size_ratio",
                        "type" : "float?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--SORTING_COLLECTION_SIZE_RATIO"
                        }
                      }, {
                        "id" : "tag_duplicate_set_members",
                        "type" : "boolean?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--TAG_DUPLICATE_SET_MEMBERS"
                        }
                      }, {
                        "id" : "tagging_policy",
                        "type" : "string?",
                        "inputBinding" : {
                          "position" : 0,
                          "prefix" : "--TAGGING_POLICY"
                        }
                      } ],
                      "outputs" : [ {
                        "id" : "output_md_bam",
                        "type" : "File",
                        "outputBinding" : {
                          "glob" : "$(inputs.input.basename.replace('md.bam', 'bam'))"
                        },
                        "secondaryFiles" : [ "^.bai" ],
                        "doc" : "Output marked duplicate bam"
                      }, {
                        "id" : "output_md_metrics",
                        "type" : "File",
                        "outputBinding" : {
                          "glob" : "$(inputs.input.basename.replace('bam', 'md.metrics'))"
                        },
                        "doc" : "Output marked duplicate metrics"
                      } ],
                      "hints" : [ ],
                      "requirements" : [ {
                        "class" : "ResourceRequirement",
                        "ramMin" : 42000,
                        "coresMin" : 1
                      }, {
                        "class" : "DockerRequirement",
                        "dockerPull" : "broadinstitute/gatk:4.1.0.0"
                      }, {
                        "class" : "InlineJavascriptRequirement"
                      } ],
                      "successCodes" : [ ],
                      "baseCommand" : [ "gatk", "MarkDuplicates" ],
                      "arguments" : [ {
                        "position" : 0,
                        "prefix" : "--OUTPUT",
                        "valueFrom" : "$(inputs.input.basename.replace('md.bam', 'bam'))"
                      }, {
                        "position" : 0,
                        "prefix" : "--METRICS_FILE",
                        "valueFrom" : "$(inputs.input.basename.replace('bam', 'md.metrics'))"
                      }, {
                        "position" : 0,
                        "prefix" : "--TMP_DIR",
                        "valueFrom" : "."
                      }, {
                        "position" : 0,
                        "prefix" : "--ASSUME_SORT_ORDER",
                        "valueFrom" : "coordinate"
                      }, {
                        "position" : 0
                      }, {
                        "position" : 0,
                        "prefix" : "--CREATE_INDEX",
                        "valueFrom" : "true"
                      }, {
                        "position" : 0,
                        "prefix" : "--MAX_RECORDS_IN_RAM",
                        "valueFrom" : "50000"
                      }, {
                        "position" : 0,
                        "prefix" : "--java-options",
                        "valueFrom" : "-Xms$(parseInt(runtime.ram)/1900)g -Xmx$(parseInt(runtime.ram)/950)g"
                      } ],
                      "id" : "gatk_markduplicatesgatk",
                      "label" : "GATK MarkDuplicates",
                      "class" : "CommandLineTool"
                    },
                    "in" : [ {
                      "id" : "input",
                      "source" : "samtools_merge/output_file"
                    } ],
                    "out" : [ {
                      "id" : "output_md_bam"
                    }, {
                      "id" : "output_md_metrics"
                    } ],
                    "hints" : [ ],
                    "requirements" : [ ]
                  } ],
                  "id" : "align_sample",
                  "label" : "align_sample",
                  "class" : "Workflow"
                },
                "in" : [ {
                  "id" : "prefix",
                  "source" : "sample_id"
                }, {
                  "id" : "reference_sequence",
                  "source" : "mouse_reference"
                }, {
                  "id" : "r1",
                  "source" : "r1"
                }, {
                  "id" : "r2",
                  "source" : "r2"
                }, {
                  "id" : "sample_id",
                  "valueFrom" : "${ return inputs.prefix + \"_mouse\"; }"
                }, {
                  "id" : "lane_id",
                  "source" : "lane_id"
                } ],
                "out" : [ {
                  "id" : "output_merge_sort_bam"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "name_sort_human",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "compression_level",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-l"
                    },
                    "doc" : "Set compression level, from 0 (uncompressed) to 9 (best)\n"
                  }, {
                    "id" : "input",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 1
                    },
                    "doc" : "Input bam file."
                  }, {
                    "id" : "memory",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-m"
                    },
                    "doc" : "Set maximum memory per thread; suffix K/M/G recognized [768M]\n"
                  }, {
                    "id" : "sort_by_name",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-n"
                    },
                    "doc" : "Sort by read names (i.e., the QNAME field) rather than by chromosomal coordinates."
                  }, {
                    "id" : "reference",
                    "type" : "File?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "--reference"
                    }
                  }, {
                    "id" : "output_format",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-O"
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "output_file",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "$(inputs.input.basename.replace('bam', 'sorted.bam'))"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "ResourceRequirement",
                    "ramMin" : 32000,
                    "coresMin" : 4
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "quay.io/cancercollaboratory/dockstore-tool-samtools-sort:1.0"
                  }, {
                    "class" : "InlineJavascriptRequirement"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "samtools", "sort" ],
                  "arguments" : [ {
                    "position" : 0,
                    "prefix" : "-o",
                    "valueFrom" : "$(inputs.input.basename.replace('bam', 'sorted.bam'))"
                  }, {
                    "position" : 0,
                    "prefix" : "-@",
                    "valueFrom" : "$(runtime.cores)"
                  } ],
                  "dct:creator" : {
                    "@id" : "http://orcid.org/0000-0001-9102-5681",
                    "foaf:mbox" : "mailto:Andrey.Kartashov@cchmc.org",
                    "foaf:name" : "Andrey Kartashov"
                  },
                  "dct:contributor" : {
                    "foaf:mbox" : "mailto:ayang@oicr.on.ca",
                    "foaf:name" : "Andy Yang"
                  },
                  "doc" : "Sort alignments by leftmost coordinates, or by read name when -n is used. An appropriate @HD-SO sort order header tag will be added or an existing one updated if necessary.\n\nUsage: samtools sort [-l level] [-m maxMem] [-o out.bam] [-O format] [-n] -T out.prefix [-@ threads] [in.bam]\n\nOptions:\n-l INT\nSet the desired compression level for the final output file, ranging from 0 (uncompressed) or 1 (fastest but minimal compression) to 9 (best compression but slowest to write), similarly to gzip(1)'s compression level setting.\n\nIf -l is not used, the default compression level will apply.\n\n-m INT\nApproximately the maximum required memory per thread, specified either in bytes or with a K, M, or G suffix. [768 MiB]\n\n-n\nSort by read names (i.e., the QNAME field) rather than by chromosomal coordinates.\n\n-o FILE\nWrite the final sorted output to FILE, rather than to standard output.\n\n-O FORMAT\nWrite the final output as sam, bam, or cram.\n\nBy default, samtools tries to select a format based on the -o filename extension; if output is to standard output or no format can be deduced, -O must be used.\n\n-T PREFIX\nWrite temporary files to PREFIX.nnnn.bam. This option is required.\n\n-@ INT\nSet number of sorting and compression threads. By default, operation is single-threaded\n",
                  "dct:description" : "Developed at Cincinnati Children���s Hospital Medical Center for the CWL consortium http://commonwl.org/ Original URL: https://github.com/common-workflow-language/workflows",
                  "$namespaces" : null,
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "input",
                  "source" : "align_to_human/output_merge_sort_bam"
                }, {
                  "id" : "sort_by_name",
                  "valueFrom" : "${ return true; }"
                } ],
                "out" : [ {
                  "id" : "output_file"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "name_sort_mouse",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "compression_level",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-l"
                    },
                    "doc" : "Set compression level, from 0 (uncompressed) to 9 (best)\n"
                  }, {
                    "id" : "input",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 1
                    },
                    "doc" : "Input bam file."
                  }, {
                    "id" : "memory",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-m"
                    },
                    "doc" : "Set maximum memory per thread; suffix K/M/G recognized [768M]\n"
                  }, {
                    "id" : "sort_by_name",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-n"
                    },
                    "doc" : "Sort by read names (i.e., the QNAME field) rather than by chromosomal coordinates."
                  }, {
                    "id" : "reference",
                    "type" : "File?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "--reference"
                    }
                  }, {
                    "id" : "output_format",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-O"
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "output_file",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "$(inputs.input.basename.replace('bam', 'sorted.bam'))"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "ResourceRequirement",
                    "ramMin" : 32000,
                    "coresMin" : 4
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "quay.io/cancercollaboratory/dockstore-tool-samtools-sort:1.0"
                  }, {
                    "class" : "InlineJavascriptRequirement"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "samtools", "sort" ],
                  "arguments" : [ {
                    "position" : 0,
                    "prefix" : "-o",
                    "valueFrom" : "$(inputs.input.basename.replace('bam', 'sorted.bam'))"
                  }, {
                    "position" : 0,
                    "prefix" : "-@",
                    "valueFrom" : "$(runtime.cores)"
                  } ],
                  "dct:creator" : {
                    "@id" : "http://orcid.org/0000-0001-9102-5681",
                    "foaf:mbox" : "mailto:Andrey.Kartashov@cchmc.org",
                    "foaf:name" : "Andrey Kartashov"
                  },
                  "dct:contributor" : {
                    "foaf:mbox" : "mailto:ayang@oicr.on.ca",
                    "foaf:name" : "Andy Yang"
                  },
                  "doc" : "Sort alignments by leftmost coordinates, or by read name when -n is used. An appropriate @HD-SO sort order header tag will be added or an existing one updated if necessary.\n\nUsage: samtools sort [-l level] [-m maxMem] [-o out.bam] [-O format] [-n] -T out.prefix [-@ threads] [in.bam]\n\nOptions:\n-l INT\nSet the desired compression level for the final output file, ranging from 0 (uncompressed) or 1 (fastest but minimal compression) to 9 (best compression but slowest to write), similarly to gzip(1)'s compression level setting.\n\nIf -l is not used, the default compression level will apply.\n\n-m INT\nApproximately the maximum required memory per thread, specified either in bytes or with a K, M, or G suffix. [768 MiB]\n\n-n\nSort by read names (i.e., the QNAME field) rather than by chromosomal coordinates.\n\n-o FILE\nWrite the final sorted output to FILE, rather than to standard output.\n\n-O FORMAT\nWrite the final output as sam, bam, or cram.\n\nBy default, samtools tries to select a format based on the -o filename extension; if output is to standard output or no format can be deduced, -O must be used.\n\n-T PREFIX\nWrite temporary files to PREFIX.nnnn.bam. This option is required.\n\n-@ INT\nSet number of sorting and compression threads. By default, operation is single-threaded\n",
                  "dct:description" : "Developed at Cincinnati Children���s Hospital Medical Center for the CWL consortium http://commonwl.org/ Original URL: https://github.com/common-workflow-language/workflows",
                  "$namespaces" : null,
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "input",
                  "source" : "align_to_mouse/output_merge_sort_bam"
                }, {
                  "id" : "sort_by_name",
                  "valueFrom" : "${ return true; }"
                } ],
                "out" : [ {
                  "id" : "output_file"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "run_disambiguate",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "no_sort",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "--no-sort"
                    }
                  }, {
                    "id" : "prefix",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "--prefix"
                    }
                  }, {
                    "id" : "output_dir",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "--output-dir"
                    }
                  }, {
                    "id" : "aligner",
                    "default" : "bwa",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "--aligner"
                    }
                  }, {
                    "id" : "species_a_bam",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 1
                    }
                  }, {
                    "id" : "species_b_bam",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "disambiguate_a_bam",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n    return inputs.output_dir.concat('/*.disambiguatedSpeciesA.bam');\n}\n"
                    }
                  }, {
                    "id" : "disambiguate_b_bam",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n    return inputs.output_dir.concat('/*.disambiguatedSpeciesB.bam');\n}\n"
                    }
                  }, {
                    "id" : "summary",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n    return inputs.output_dir.concat('/*_summary.txt');\n}\n"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "ResourceRequirement",
                    "ramMin" : 32000,
                    "coresMin" : 4
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/disambiguate:1.0.0"
                  }, {
                    "class" : "InlineJavascriptRequirement"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "ngs_disambiguate" ],
                  "arguments" : [ ],
                  "doap:release" : [ {
                    "class" : "doap:Version",
                    "doap:name" : "disambiguate",
                    "doap:revision" : "1.0.0"
                  } ],
                  "dct:creator" : [ {
                    "class" : "foaf:Organization",
                    "foaf:member" : [ {
                      "class" : "foaf:Person",
                      "foaf:mbox" : "mailto:bolipatc@mskcc.org",
                      "foaf:name" : "C. Allan Bolipata"
                    } ],
                    "foaf:name" : "Memorial Sloan Kettering Cancer Center"
                  } ],
                  "dct:contributor" : [ {
                    "class" : "foaf:Organization",
                    "foaf:member" : [ {
                      "class" : "foaf:Person",
                      "foaf:mbox" : "mailto:bolipatc@mskcc.org",
                      "foaf:name" : "C. Allan Bolipata"
                    } ],
                    "foaf:name" : "Memorial Sloan Kettering Cancer Center"
                  } ],
                  "$namespaces" : {
                    "dct" : "http://purl.org/dc/terms/",
                    "doap" : "http://usefulinc.com/ns/doap#",
                    "foaf" : "http://xmlns.com/foaf/0.1/"
                  },
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "prefix",
                  "source" : "sample_id"
                }, {
                  "id" : "aligner",
                  "valueFrom" : "${ return \"bwa\"; }"
                }, {
                  "id" : "output_dir",
                  "valueFrom" : "${ return inputs.prefix + \"_disambiguated\"; }"
                }, {
                  "id" : "species_a_bam",
                  "source" : "name_sort_human/output_file"
                }, {
                  "id" : "species_b_bam",
                  "source" : "name_sort_mouse/output_file"
                } ],
                "out" : [ {
                  "id" : "disambiguate_a_bam"
                }, {
                  "id" : "disambiguate_b_bam"
                }, {
                  "id" : "summary"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              } ],
              "id" : "resolve-pdx",
              "class" : "Workflow"
            },
            "scatter" : [ "lane_id" ],
            "scatterMethod" : "dotproduct",
            "in" : [ {
              "id" : "human_reference",
              "source" : "ref_fasta"
            }, {
              "id" : "mouse_reference",
              "source" : "mouse_fasta"
            }, {
              "id" : "sample_id",
              "source" : "get_sample_info/ID"
            }, {
              "id" : "lane_id",
              "source" : "get_sample_info/zPU"
            }, {
              "id" : "r1",
              "source" : "get_sample_info/zR1"
            }, {
              "id" : "r2",
              "source" : "get_sample_info/zR2"
            } ],
            "out" : [ {
              "id" : "disambiguate_bam"
            }, {
              "id" : "summary"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "unpack_bam",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "input_bam",
                "type" : "File",
                "inputBinding" : {
                  "position" : 0,
                  "prefix" : "--input-bam"
                }
              }, {
                "id" : "sample_id",
                "type" : "string",
                "inputBinding" : {
                  "position" : 0,
                  "prefix" : "--sample-id"
                }
              }, {
                "id" : "picard_jar",
                "default" : "/opt/common/CentOS_6-dev/picard/v2.13/picard.jar",
                "type" : "string",
                "inputBinding" : {
                  "position" : 0,
                  "prefix" : "--picard-jar"
                }
              }, {
                "id" : "output_dir",
                "default" : "fastqs",
                "type" : "string",
                "inputBinding" : {
                  "position" : 0,
                  "prefix" : "--output-dir"
                }
              } ],
              "outputs" : [ {
                "id" : "rg_output",
                "type" : "Directory",
                "outputBinding" : {
                  "glob" : "${\n  return inputs.output_dir;\n }"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/unpack_bam:0.1.0"
              }, {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : 16000,
                "coresMin" : 2
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "perl", "/opt/unpack_bam.pl" ],
              "arguments" : [ {
                "position" : 0,
                "prefix" : "--tmp-dir",
                "shellQuote" : false,
                "valueFrom" : "$(runtime.tmpdir)"
              } ],
              "id" : "unpack-bam",
              "class" : "CommandLineTool"
            },
            "scatter" : [ "input_bam" ],
            "scatterMethod" : "dotproduct",
            "in" : [ {
              "id" : "input_bam",
              "linkMerge" : "merge_flattened",
              "source" : [ "resolve_pdx/disambiguate_bam", "get_sample_info/bam" ]
            }, {
              "id" : "sample_id",
              "source" : "get_sample_info/ID"
            } ],
            "out" : [ {
              "id" : "rg_output"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "flatten_dir",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "directory_list",
                "type" : {
                  "items" : "Directory",
                  "type" : "array"
                }
              } ],
              "outputs" : [ {
                "id" : "output_directory",
                "type" : "Directory"
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              } ],
              "successCodes" : [ ],
              "expression" : "${ if (inputs.directory_list.length != 0) { return {'output_directory':inputs.directory_list[0]}; } else { return { 'output_directory': {'class': 'Directory','basename': 'empty','listing': []} }}; }",
              "id" : "flatten-array-directory",
              "class" : "ExpressionTool"
            },
            "in" : [ {
              "id" : "directory_list",
              "source" : "unpack_bam/rg_output"
            } ],
            "out" : [ {
              "id" : "output_directory"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "consolidate_reads",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "reads_dir",
                "type" : "Directory"
              } ],
              "outputs" : [ {
                "id" : "r1",
                "type" : "File[]"
              }, {
                "id" : "r2",
                "type" : "File[]"
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              } ],
              "successCodes" : [ ],
              "expression" : "${\n  var r1_files = [];\n  var r2_files = [];\n\n  for (var i = 0; i < inputs.reads_dir.listing.length; i++) {\n    var current_file_obj = inputs.reads_dir.listing[i];\n    if (current_file_obj.class == \"Directory\"){\n      for (var j = 0; j < current_file_obj.listing.length; j++) {\n        var current_fastq = current_file_obj.listing[j];\n        if ( current_fastq.basename.includes(\"_R1_\")){\n          r1_files.push(current_fastq);\n        }\n        else if ( current_fastq.basename.includes(\"_R2_\")){\n          r2_files.push(current_fastq);\n        }\n      }\n    }\n  }\n\n  return {\n    'r1': r1_files,\n    'r2': r2_files\n  };\n}\n",
              "id" : "consolidate-reads",
              "class" : "ExpressionTool"
            },
            "in" : [ {
              "id" : "reads_dir",
              "source" : "flatten_dir/output_directory"
            } ],
            "out" : [ {
              "id" : "r1"
            }, {
              "id" : "r2"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "chunking",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "fastq1",
                "type" : "File",
                "inputBinding" : {
                  "prefix" : "--fastq1"
                },
                "doc" : "filename to split"
              }, {
                "id" : "fastq2",
                "type" : "File",
                "inputBinding" : {
                  "prefix" : "--fastq2"
                },
                "doc" : "filename2 to split"
              }, {
                "id" : "platform_unit",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "prefix" : "--platform-unit"
                },
                "doc" : "RG/PU ID"
              } ],
              "outputs" : [ {
                "id" : "chunks1",
                "type" : {
                  "items" : "File",
                  "type" : "array"
                },
                "outputBinding" : {
                  "glob" : "${\n  var pattern = inputs.platform_unit + \"-\" + inputs.fastq1.basename.split(\".\",1)[0].split('_').slice(1).join(\"-\") + \".chunk*\";\n  return pattern\n}\n"
                }
              }, {
                "id" : "chunks2",
                "type" : {
                  "items" : "File",
                  "type" : "array"
                },
                "outputBinding" : {
                  "glob" : "${\n  var pattern = inputs.platform_unit + \"-\" + inputs.fastq2.basename.split(\".\",1)[0].split('_').slice(1).join(\"-\") + \".chunk*\";\n  return pattern\n}\n"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : 24000,
                "coresMin" : 1
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-cmo-utils:1.9.15"
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "cmo_split_reads" ],
              "arguments" : [ ],
              "doc" : "split files into chunks based on filesize\n",
              "id" : "cmo-split-reads",
              "class" : "CommandLineTool"
            },
            "scatter" : [ "fastq1", "fastq2", "platform_unit" ],
            "scatterMethod" : "dotproduct",
            "in" : [ {
              "id" : "fastq1",
              "linkMerge" : "merge_flattened",
              "source" : [ "get_sample_info/R1", "consolidate_reads/r1" ]
            }, {
              "id" : "fastq2",
              "linkMerge" : "merge_flattened",
              "source" : [ "get_sample_info/R2", "consolidate_reads/r2" ]
            }, {
              "id" : "platform_unit",
              "source" : "get_sample_info/PU"
            } ],
            "out" : [ {
              "id" : "chunks1"
            }, {
              "id" : "chunks2"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "flatten",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "fastq1",
                "type" : [ "File", {
                  "items" : {
                    "items" : "File",
                    "type" : "array"
                  },
                  "type" : "array"
                } ]
              }, {
                "id" : "fastq2",
                "type" : [ "File", {
                  "items" : {
                    "items" : "File",
                    "type" : "array"
                  },
                  "type" : "array"
                } ]
              }, {
                "id" : "add_rg_ID",
                "type" : {
                  "items" : "string",
                  "type" : "array"
                }
              }, {
                "id" : "add_rg_PU",
                "type" : {
                  "items" : "string",
                  "type" : "array"
                }
              } ],
              "outputs" : [ {
                "id" : "chunks1",
                "type" : {
                  "items" : "File",
                  "type" : "array"
                }
              }, {
                "id" : "chunks2",
                "type" : {
                  "items" : "File",
                  "type" : "array"
                }
              }, {
                "id" : "rg_ID",
                "type" : {
                  "items" : "string",
                  "type" : "array"
                }
              }, {
                "id" : "rg_PU",
                "type" : {
                  "items" : "string",
                  "type" : "array"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              } ],
              "successCodes" : [ ],
              "expression" : "${ var fastq1 = []; var fastq2 =[]; var add_rg_ID = []; var add_rg_PU = []; for (var i = 0; i < inputs.fastq1.length; i++) { for (var j =0; j < inputs.fastq1[i].length; j++) { fastq1.push(inputs.fastq1[i][j]); fastq2.push(inputs.fastq2[i][j]); } } fastq1 = fastq1.sort(function(a,b) {  if (a['basename']< b['basename']) { return -1; } else if(a['basename'] > b['basename']) { return 1; } else { return 0; } }); fastq2 = fastq2.sort(function(a,b) { if (a['basename']< b['basename']) { return -1; } else if(a['basename'] > b['basename']) { return 1; } else { return 0; }}); for (var i =0; i < fastq1.length; i++) { for(var j=0; j < inputs.add_rg_PU.length; j++) { if (fastq1[i].basename.includes(inputs.add_rg_PU[j])) { add_rg_ID.push(inputs.add_rg_ID[j]); add_rg_PU.push(inputs.add_rg_PU[j]); } } } var returnobj = {}; returnobj['chunks1'] = fastq1; returnobj['chunks2'] = fastq2; returnobj['rg_ID']= add_rg_ID; returnobj['rg_PU']= add_rg_PU; return returnobj; }",
              "id" : "flatten-array-fastq",
              "class" : "ExpressionTool"
            },
            "in" : [ {
              "id" : "fastq1",
              "source" : "chunking/chunks1"
            }, {
              "id" : "fastq2",
              "source" : "chunking/chunks2"
            }, {
              "id" : "add_rg_ID",
              "source" : "get_sample_info/RG_ID"
            }, {
              "id" : "add_rg_PU",
              "source" : "get_sample_info/PU"
            } ],
            "out" : [ {
              "id" : "chunks1"
            }, {
              "id" : "chunks2"
            }, {
              "id" : "rg_ID"
            }, {
              "id" : "rg_PU"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "align",
            "run" : {
              "inputs" : [ {
                "id" : "ref_fasta",
                "type" : "File"
              }, {
                "id" : "chunkfastq1",
                "type" : "File"
              }, {
                "id" : "chunkfastq2",
                "type" : "File"
              }, {
                "id" : "adapter",
                "type" : "string"
              }, {
                "id" : "genome",
                "type" : "string"
              }, {
                "id" : "adapter2",
                "type" : "string"
              }, {
                "id" : "bwa_output",
                "type" : "string"
              }, {
                "id" : "add_rg_LB",
                "type" : "string"
              }, {
                "id" : "add_rg_PL",
                "type" : "string"
              }, {
                "id" : "add_rg_ID",
                "type" : "string"
              }, {
                "id" : "add_rg_PU",
                "type" : "string"
              }, {
                "id" : "add_rg_SM",
                "type" : "string"
              }, {
                "id" : "add_rg_CN",
                "type" : "string"
              } ],
              "outputs" : [ {
                "id" : "clstats1",
                "type" : "File",
                "outputSource" : "trim_galore/clstats1"
              }, {
                "id" : "clstats2",
                "type" : "File",
                "outputSource" : "trim_galore/clstats2"
              }, {
                "id" : "bam",
                "type" : "File",
                "outputSource" : "add_rg_id/bam"
              } ],
              "hints" : [ ],
              "requirements" : [ ],
              "successCodes" : [ ],
              "steps" : [ {
                "id" : "trim_galore",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "quality",
                    "default" : "1",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--quality"
                    },
                    "doc" : "Trim low-quality ends from reads in addition to adapter removal. For RRBS samples, quality trimming will be performed first, and adapter trimming is carried in a second round. Other files are quality and adapter trimmed in a single pass. The algorithm is the same as the one used by BWA (Subtract INT from all qualities; compute partial sums from all indices to the end of the sequence; cut sequence at the index at which the sum is minimal). Default Phred score - 20."
                  }, {
                    "id" : "phred33",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--phred33"
                    },
                    "doc" : "Instructs Cutadapt to use ASCII+33 quality scores as Phred scores (Sanger/Illumina 1.9+ encoding) for quality trimming. Default - ON."
                  }, {
                    "id" : "phred64",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--phred64"
                    },
                    "doc" : "Instructs Cutadapt to use ASCII+64 quality scores as Phred scores (Illumina 1.5 encoding) for quality trimming."
                  }, {
                    "id" : "fastqc",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--fastqc"
                    },
                    "doc" : "Run FastQC in the default mode on the FastQ file once trimming is complete.--fastqc_args \"<ARGS>\" Passes extra arguments to FastQC. If more than one argument is to be passed to FastQC they must be in the form \"arg1 arg2 etc.\". An example would be - --fastqc_args \"--nogroup --outdir /home/\". Passing extra arguments will automatically invoke FastQC, so --fastqc does not have to be specified separately."
                  }, {
                    "id" : "adapter",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--adapter"
                    },
                    "doc" : "Adapter sequence to be trimmed. If not specified explicitely, the first 13 bp of the Illumina adapter 'AGATCGGAAGAGC' will be used by default."
                  }, {
                    "id" : "adapter2",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--adapter2"
                    },
                    "doc" : "Optional adapter sequence to be trimmed off read 2 of paired-end files. This option requires '--paired' to be specified as well."
                  }, {
                    "id" : "stringency",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--stringency"
                    },
                    "doc" : "Overlap with adapter sequence required to trim a sequence. Defaults to a very stringent setting of '1', i.e. even a single bp of overlapping sequence will be trimmed of the 3' end of any read.-e <ERROR RATE> Maximum allowed error rate (no. of errors divided by the length of the matching region) (default - 0.1)"
                  }, {
                    "id" : "gzip",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--gzip"
                    },
                    "doc" : "Compress the output file with gzip. If the input files are gzip-compressed the output files will be automatically gzip compressed as well."
                  }, {
                    "id" : "length",
                    "default" : "25",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--length"
                    },
                    "doc" : "Discard reads that became shorter than length INT because of either quality or adapter trimming. A value of '0' effectively disables this behaviour. Default - 20 bp. For paired-end files, both reads of a read-pair need to be longer than <INT> bp to be printed out to validated paired-end files (see option --paired). If only one read became too short there is the possibility of keeping such unpaired single-end reads (see --retain_unpaired). Default pair-cutoff - 20 bp."
                  }, {
                    "id" : "output_dir",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--output_dir"
                    },
                    "doc" : "If specified all output will be written to this directory instead of the current directory."
                  }, {
                    "id" : "no_report_file",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--no_report_file"
                    },
                    "doc" : "If specified no report file will be generated."
                  }, {
                    "id" : "suppress_warn",
                    "default" : true,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--suppress_warn"
                    },
                    "doc" : "If specified any output to STDOUT or STDERR will be suppressed.RRBS-specific options (MspI digested material) -"
                  }, {
                    "id" : "rrbs",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--rrbs"
                    },
                    "doc" : "Specifies that the input file was an MspI digested RRBS sample (recognition site - CCGG). Sequences which were adapter-trimmed will have a further 2 bp removed from their 3' end. This is to avoid that the filled-in C close to the second MspI site in a sequence is used for methylation calls. Sequences which were merely trimmed because of poor quality will not be shortened further."
                  }, {
                    "id" : "non_directional",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--non_directional"
                    },
                    "doc" : "Selecting this option for non-directional RRBS libraries will screen quality-trimmed sequences for 'CAA' or 'CGA' at the start of the read and, if found, removes the first two basepairs. Like with the option '--rrbs' this avoids using cytosine positions that were filled-in during the end-repair step. '--non_directional' requires '--rrbs' to be specified as well."
                  }, {
                    "id" : "keep",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--keep"
                    },
                    "doc" : "Keep the quality trimmed intermediate file. Default - off, which means the temporary file is being deleted after adapter trimming. Only has an effect for RRBS samples since other FastQ files are not trimmed for poor qualities separately.Note for RRBS using MseI -If your DNA material was digested with MseI (recognition motif - TTAA) instead of MspI it is NOT necessaryto specify --rrbs or --non_directional since virtually all reads should start with the sequence'TAA', and this holds true for both directional and non-directional libraries. As the end-repair of 'TAA'restricted sites does not involve any cytosines it does not need to be treated especially. Instead, simplyrun Trim Galore! in the standard (i.e. non-RRBS) mode.Paired-end specific options -"
                  }, {
                    "id" : "paired",
                    "default" : true,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--paired"
                    },
                    "doc" : "This option performs length trimming of quality/adapter/RRBS trimmed reads for paired-end files. To pass the validation test, both sequences of a sequence pair are required to have a certain minimum length which is governed by the option --length (see above). If only one read passes this length threshold the other read can be rescued (see option --retain_unpaired). Using this option lets you discard too short read pairs without disturbing the sequence-by-sequence order of FastQ files which is required by many aligners. Trim Galore! expects paired-end files to be supplied in a pairwise fashion, e.g. file1_1.fq file1_2.fq SRR2_1.fq.gz SRR2_2.fq.gz ... ."
                  }, {
                    "id" : "trim1",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--trim1"
                    },
                    "doc" : "Trims 1 bp off every read from its 3' end. This may be needed for FastQ files that are to be aligned as paired-end data with Bowtie. This is because Bowtie (1) regards alignments like this - R1 ---------------------------> or this - -----------------------> R1 R2 <--------------------------- <----------------- R2 as invalid (whenever a start/end coordinate is contained within the other read)."
                  }, {
                    "id" : "retain_unpaired",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--retain_unpaired"
                    },
                    "doc" : "If only one of the two paired-end reads became too short, the longer read will be written to either '.unpaired_1.fq' or '.unpaired_2.fq' output files. The length cutoff for unpaired single-end reads is governed by the parameters -r1/--length_1 and -r2/--length_2. Default - OFF."
                  }, {
                    "id" : "length_1",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--length_1"
                    },
                    "doc" : "Unpaired single-end read length cutoff needed for read 1 to be written to '.unpaired_1.fq' output file. These reads may be mapped in single-end mode. Default - 35 bp."
                  }, {
                    "id" : "length_2",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--length_2"
                    },
                    "doc" : "Unpaired single-end read length cutoff needed for read 2 to be written to '.unpaired_2.fq' output file. These reads may be mapped in single-end mode. Default - 35 bp.Last modified on 18 Oct 2012."
                  }, {
                    "id" : "fastq1",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 1
                    }
                  }, {
                    "id" : "fastq2",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2
                    }
                  }, {
                    "id" : "stderr",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--stderr"
                    },
                    "doc" : "log stderr to file"
                  }, {
                    "id" : "stdout",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--stdout"
                    },
                    "doc" : "log stdout to file"
                  } ],
                  "outputs" : [ {
                    "id" : "clfastq1",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.paired && inputs.fastq1)\n    return getBaseName(inputs.fastq1).replace(\".fastq.gz\", \"_cl.fastq.gz\");\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "clfastq2",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.paired && inputs.fastq2)\n    return getBaseName(inputs.fastq2).replace(\".fastq.gz\", \"_cl.fastq.gz\");\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "clstats1",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.paired && inputs.fastq1)\n    return getBaseName(inputs.fastq1).replace(\".fastq.gz\", \"_cl.stats\");\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "clstats2",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.paired && inputs.fastq2)\n    return getBaseName(inputs.fastq2).replace(\".fastq.gz\", \"_cl.stats\");\n  return null;\n}"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement",
                    "expressionLib" : [ "var getBaseName = function(inputFile) { return inputFile.basename; };" ]
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 12000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-trimgalore:0.2.5.mod"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "/usr/bin/trim_galore" ],
                  "arguments" : [ ],
                  "doc" : "None\n",
                  "id" : "trimgalore",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "fastq1",
                  "source" : "chunkfastq1"
                }, {
                  "id" : "fastq2",
                  "source" : "chunkfastq2"
                }, {
                  "id" : "adapter",
                  "source" : "adapter"
                }, {
                  "id" : "adapter2",
                  "source" : "adapter2"
                } ],
                "out" : [ {
                  "id" : "clfastq1"
                }, {
                  "id" : "clfastq2"
                }, {
                  "id" : "clstats1"
                }, {
                  "id" : "clstats2"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "bwa",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "reference",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 1
                    },
                    "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
                  }, {
                    "id" : "fastq1",
                    "type" : [ "string", "File" ],
                    "inputBinding" : {
                      "position" : 2
                    }
                  }, {
                    "id" : "fastq2",
                    "type" : [ "string", "File" ],
                    "inputBinding" : {
                      "position" : 2
                    }
                  }, {
                    "id" : "output",
                    "type" : "string"
                  }, {
                    "id" : "E",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-E"
                    },
                    "doc" : "INT gap extension penalty; a gap of size k cost {-O} + {-E}*k [1]"
                  }, {
                    "id" : "d",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-d"
                    },
                    "doc" : "INT off-diagonal X-dropoff [100]"
                  }, {
                    "id" : "A",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-A"
                    },
                    "doc" : "INT score for a sequence match [1]"
                  }, {
                    "id" : "C",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-C"
                    },
                    "doc" : "append FASTA/FASTQ comment to SAM output"
                  }, {
                    "id" : "c",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-c"
                    },
                    "doc" : "INT skip seeds with more than INT occurrences [10000]"
                  }, {
                    "id" : "B",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-B"
                    },
                    "doc" : "INT penalty for a mismatch [4]"
                  }, {
                    "id" : "M",
                    "default" : true,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-M"
                    },
                    "doc" : "mark shorter split hits as secondary (for Picard/GATK compatibility)"
                  }, {
                    "id" : "L",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-L"
                    },
                    "doc" : "INT penalty for clipping [5]"
                  }, {
                    "id" : "O",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-O"
                    },
                    "doc" : "INT gap open penalty [6]"
                  }, {
                    "id" : "R",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-R"
                    },
                    "doc" : "STR read group header line such as '@RG\\tID -foo\\tSM -bar' [null]"
                  }, {
                    "id" : "k",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-k"
                    },
                    "doc" : "INT minimum seed length [19]"
                  }, {
                    "id" : "U",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-U"
                    },
                    "doc" : "INT penalty for an unpaired read pair [17]"
                  }, {
                    "id" : "t",
                    "default" : "6",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-t"
                    },
                    "doc" : "INT number of threads [1]"
                  }, {
                    "id" : "w",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-w"
                    },
                    "doc" : "INT band width for banded alignment [100]"
                  }, {
                    "id" : "v",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-v"
                    },
                    "doc" : "INT verbose level - 1=error, 2=warning, 3=message, 4+=debugging [3]"
                  }, {
                    "id" : "T",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-T"
                    },
                    "doc" : "INT minimum score to output [30]"
                  }, {
                    "id" : "P",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-P"
                    },
                    "doc" : "skip pairing; mate rescue performed unless -S also in use"
                  }, {
                    "id" : "S",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-S"
                    },
                    "doc" : "skip mate rescue"
                  }, {
                    "id" : "r",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-r"
                    },
                    "doc" : "FLOAT look for internal seeds inside a seed longer than {-k} * FLOAT [1.5]"
                  }, {
                    "id" : "a",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-a"
                    },
                    "doc" : "output all alignments for SE or unpaired PE"
                  }, {
                    "id" : "p",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-p"
                    },
                    "doc" : "first query file consists of interleaved paired-end sequences"
                  } ],
                  "outputs" : [ {
                    "id" : "sam",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.output)\n    return inputs.output;\n  return null;\n}"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 32000,
                    "coresMin" : 4
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/bwa_mem:0.7.12"
                  } ],
                  "successCodes" : [ ],
                  "stdout" : "$(inputs.output)",
                  "baseCommand" : [ "/usr/bin/bwa", "mem" ],
                  "arguments" : [ ],
                  "doc" : "run bwa mem\n",
                  "id" : "bwa-mem",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "reference",
                  "source" : "ref_fasta"
                }, {
                  "id" : "fastq1",
                  "source" : "trim_galore/clfastq1"
                }, {
                  "id" : "fastq2",
                  "source" : "trim_galore/clfastq2"
                }, {
                  "id" : "basebamname",
                  "source" : "bwa_output"
                }, {
                  "id" : "output",
                  "valueFrom" : "${ return inputs.basebamname.replace(\".bam\", \".\" + inputs.fastq1.basename.match(/chunk\\d\\d\\d/)[0] + \".sam\");}"
                }, {
                  "id" : "genome",
                  "source" : "genome"
                } ],
                "out" : [ {
                  "id" : "sam"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "sam_to_bam",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "bedoverlap",
                    "type" : "File?",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-L"
                    },
                    "doc" : "only include reads overlapping this BED FILE [null]\n"
                  }, {
                    "id" : "cigar",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-m"
                    },
                    "doc" : "only include reads with number of CIGAR operations\nconsuming query sequence >= INT [0]\n"
                  }, {
                    "id" : "collapsecigar",
                    "default" : false,
                    "type" : "boolean",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-B"
                    },
                    "doc" : "collapse the backward CIGAR operation\n"
                  }, {
                    "id" : "count",
                    "default" : false,
                    "type" : "boolean",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-c"
                    },
                    "doc" : "print only the count of matching records\n"
                  }, {
                    "id" : "fastcompression",
                    "default" : false,
                    "type" : "boolean",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-1"
                    },
                    "doc" : "use fast BAM compression (implies -b)\n"
                  }, {
                    "id" : "input",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 4
                    },
                    "doc" : "Input bam file.\n"
                  }, {
                    "id" : "isbam",
                    "default" : false,
                    "type" : "boolean",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "-b"
                    },
                    "doc" : "output in BAM format\n"
                  }, {
                    "id" : "iscram",
                    "default" : false,
                    "type" : "boolean",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "-C"
                    },
                    "doc" : "output in CRAM format\n"
                  }, {
                    "id" : "randomseed",
                    "type" : "float?",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-s"
                    },
                    "doc" : "integer part sets seed of random number generator [0];\nrest sets fraction of templates to subsample [no subsampling]\n"
                  }, {
                    "id" : "readsingroup",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-r"
                    },
                    "doc" : "only include reads in read group STR [null]\n"
                  }, {
                    "id" : "readsingroupfile",
                    "type" : "File?",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-R"
                    },
                    "doc" : "only include reads with read group listed in FILE [null]\n"
                  }, {
                    "id" : "readsinlibrary",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-l"
                    },
                    "doc" : "only include reads in library STR [null]\n"
                  }, {
                    "id" : "readsquality",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-q"
                    },
                    "doc" : "only include reads with mapping quality >= INT [0]\n"
                  }, {
                    "id" : "readswithbits",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-f"
                    },
                    "doc" : "only include reads with all bits set in INT set in FLAG [0]\n"
                  }, {
                    "id" : "readswithoutbits",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-F"
                    },
                    "doc" : "only include reads with none of the bits set in INT set in FLAG [0]\n"
                  }, {
                    "id" : "readtagtostrip",
                    "type" : "string[]?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-x"
                    },
                    "doc" : "read tag to strip (repeatable) [null]\n"
                  }, {
                    "id" : "referencefasta",
                    "type" : "File?",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-T"
                    },
                    "doc" : "reference sequence FASTA FILE [null]\n"
                  }, {
                    "id" : "region",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 5
                    },
                    "doc" : "[region ...]\n"
                  }, {
                    "id" : "samheader",
                    "default" : false,
                    "type" : "boolean",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-h"
                    },
                    "doc" : "include header in SAM output\n"
                  }, {
                    "id" : "threads",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-@"
                    },
                    "doc" : "number of BAM compression threads [0]\n"
                  }, {
                    "id" : "uncompressed",
                    "default" : false,
                    "type" : "boolean",
                    "inputBinding" : {
                      "position" : 1,
                      "prefix" : "-u"
                    },
                    "doc" : "uncompressed BAM output (implies -b)\n"
                  }, {
                    "id" : "samheaderonly",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-H"
                    }
                  }, {
                    "id" : "outputreadsnotselectedbyfilters",
                    "type" : "File?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-U"
                    }
                  }, {
                    "id" : "listingreferencenamesandlengths",
                    "type" : "File?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-t"
                    }
                  }, {
                    "id" : "readtagtostri",
                    "type" : "File?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-x"
                    }
                  }, {
                    "id" : "output_format",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-O"
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "output_bam",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "$(inputs.input.basename.replace('sam', 'bam'))"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "ResourceRequirement",
                    "ramMin" : 32000,
                    "coresMin" : 4
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-samtools:1.3.1"
                  }, {
                    "class" : "InlineJavascriptRequirement"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "/usr/bin/samtools", "view" ],
                  "arguments" : [ {
                    "position" : 0,
                    "prefix" : "-o",
                    "valueFrom" : "$(inputs.input.basename.replace('sam', 'bam'))"
                  }, {
                    "position" : 0,
                    "prefix" : "--threads",
                    "valueFrom" : "$(runtime.cores)"
                  } ],
                  "doc" : "Prints alignments in the specified input alignment file.\n\nWith no options or regions specified, prints all alignments in the specified input alignment file (in SAM, BAM, or CRAM format) to standard output in SAM format (with no header).\n\nYou may specify one or more space-separated region specifications after the input filename to restrict output to only those alignments which overlap the specified region(s). Use of region specifications requires a coordinate-sorted and indexed input file (in BAM or CRAM format).\n\nThe -b, -C, -1, -u, -h, -H, and -c options change the output format from the default of headerless SAM, and the -o and -U options set the output file name(s).\n\nThe -t and -T options provide additional reference data. One of these two options is required when SAM input does not contain @SQ headers, and the -T option is required whenever writing CRAM output.\n\nThe -L, -r, -R, -q, -l, -m, -f, and -F options filter the alignments that will be included in the output to only those alignments that match certain criteria.\n\nThe -x, -B, and -s options modify the data which is contained in each alignment.\n\nFinally, the -@ option can be used to allocate additional threads to be used for compression, and the -? option requests a long help message.\n\nUsage: samtools view [options] in.bam|in.sam|in.cram [region...]\n\nRegions can be specified as: RNAME[:STARTPOS[-ENDPOS]] and all position coordinates are 1-based.\n\nImportant note: when multiple regions are given, some alignments may be output multiple times if they overlap more than one of the specified regions.\n\nExamples of region specifications:\n\n`chr1'\nOutput all alignments mapped to the reference sequence named `chr1' (i.e. @SQ SN:chr1) .\n\n`chr2:1000000'\nThe region on chr2 beginning at base position 1,000,000 and ending at the end of the chromosome.\n\n`chr3:1000-2000'\nThe 1001bp region on chr3 beginning at base position 1,000 and ending at base position 2,000 (including both end positions).\n\nOPTIONS:\n\n-b\nOutput in the BAM format.\n\n-C\nOutput in the CRAM format (requires -T).\n\n-1\nEnable fast BAM compression (implies -b).\n\n-u\nOutput uncompressed BAM. This option saves time spent on compression/decompression and is thus preferred when the output is piped to another samtools command.\n\n-h\nInclude the header in the output.\n\n-H\nOutput the header only.\n\n-c\nInstead of printing the alignments, only count them and print the total number. All filter options, such as -f, -F, and -q, are taken into account.\n\n-?\nOutput long help and exit immediately.\n\n-o FILE\nOutput to FILE [stdout].\n\n-U FILE\nWrite alignments that are not selected by the various filter options to FILE. When this option is used, all alignments (or all alignments intersecting the regions specified) are written to either the output file or this file, but never both.\n\n-t FILE\nA tab-delimited FILE. Each line must contain the reference name in the first column and the length of the reference in the second column, with one line for each distinct reference. Any additional fields beyond the second column are ignored. This file also defines the order of the reference sequences in sorting. If you run: `samtools faidx <ref.fa>', the resulting index file <ref.fa>.fai can be used as this FILE.\n\n-T FILE\nA FASTA format reference FILE, optionally compressed by bgzip and ideally indexed by samtools faidx. If an index is not present, one will be generated for you.\n\n-L FILE\nOnly output alignments overlapping the input BED FILE [null].\n\n-r STR\nOnly output alignments in read group STR [null].\n\n-R FILE\nOutput alignments in read groups listed in FILE [null].\n\n-q INT\nSkip alignments with MAPQ smaller than INT [0].\n\n-l STR\nOnly output alignments in library STR [null].\n\n-m INT\nOnly output alignments with number of CIGAR bases consuming query sequence ��� INT [0]\n\n-f INT\nOnly output alignments with all bits set in INT present in the FLAG field. INT can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/) or in octal by beginning with `0' (i.e. /^0[0-7]+/) [0].\n\n-F INT\nDo not output alignments with any bits set in INT present in the FLAG field. INT can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/) or in octal by beginning with `0' (i.e. /^0[0-7]+/) [0].\n\n-x STR\nRead tag to exclude from output (repeatable) [null]\n\n-B\nCollapse the backward CIGAR operation.\n\n-s FLOAT\nInteger part is used to seed the random number generator [0]. Part after the decimal point sets the fraction of templates/pairs to subsample [no subsampling].\n\n-@ INT\nNumber of BAM compression threads to use in addition to main thread [0].\n\n-S\nIgnored for compatibility with previous samtools versions. Previously this option was required if input was in SAM format, but now the correct format is automatically detected by examining the first few characters of input.\n",
                  "id" : "samtools-view",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "input",
                  "source" : "bwa/sam"
                }, {
                  "id" : "isbam",
                  "valueFrom" : "${ return true; }"
                }, {
                  "id" : "samheader",
                  "valueFrom" : "${ return true; }"
                } ],
                "out" : [ {
                  "id" : "output_bam"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "add_rg_id",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "I",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "I=",
                      "separate" : false
                    }
                  }, {
                    "id" : "O",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "O=",
                      "separate" : false
                    },
                    "doc" : "Output file (BAM or SAM). Required."
                  }, {
                    "id" : "SO",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "SO=",
                      "separate" : false
                    },
                    "doc" : "Optional sort order to output in. If not supplied OUTPUT is in the same order as INPUT. Default value - null. Possible values - {unsorted, queryname, coordinate, duplicate, unknown}"
                  }, {
                    "id" : "ID",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "ID=",
                      "separate" : false
                    },
                    "doc" : "Read Group ID Default value - 1. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "LB",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "LB=",
                      "separate" : false
                    },
                    "doc" : "Read Group library Required."
                  }, {
                    "id" : "PL",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "PL=",
                      "separate" : false
                    },
                    "doc" : "Read Group platform (e.g. illumina, solid) Required."
                  }, {
                    "id" : "PU",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "PU=",
                      "separate" : false
                    },
                    "doc" : "Read Group platform unit (eg. run barcode) Required."
                  }, {
                    "id" : "SM",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "SM=",
                      "separate" : false
                    },
                    "doc" : "Read Group sample name Required."
                  }, {
                    "id" : "CN",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CN=",
                      "separate" : false
                    },
                    "doc" : "Read Group sequencing center name Default value - null."
                  }, {
                    "id" : "DS",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "DS=",
                      "separate" : false
                    },
                    "doc" : "Read Group description Default value - null."
                  }, {
                    "id" : "DT",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "DT=",
                      "separate" : false
                    },
                    "doc" : "Read Group run date Default value - null."
                  }, {
                    "id" : "KS",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "KS=",
                      "separate" : false
                    },
                    "doc" : "Read Group key sequence Default value - null."
                  }, {
                    "id" : "FO",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "FO=",
                      "separate" : false
                    },
                    "doc" : "Read Group flow order Default value - null."
                  }, {
                    "id" : "PI",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "PI=",
                      "separate" : false
                    },
                    "doc" : "Read Group predicted insert size Default value - null."
                  }, {
                    "id" : "PG",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "PG=",
                      "separate" : false
                    },
                    "doc" : "Read Group program group Default value - null."
                  }, {
                    "id" : "PM",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "PM=",
                      "separate" : false
                    },
                    "doc" : "Read Group platform model Default value - null."
                  }, {
                    "id" : "QUIET",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "QUIET=True"
                    }
                  }, {
                    "id" : "CREATE_MD5_FILE",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_MD5_FILE=True"
                    }
                  }, {
                    "id" : "CREATE_INDEX",
                    "default" : true,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_INDEX=True"
                    }
                  }, {
                    "id" : "VERBOSITY",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VERBOSITY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "VALIDATION_STRINGENCY",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VALIDATION_STRINGENCY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "COMPRESSION_LEVEL",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "COMPRESSION_LEVEL=",
                      "separate" : false
                    }
                  }, {
                    "id" : "MAX_RECORDS_IN_RAM",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MAX_RECORDS_IN_RAM=",
                      "separate" : false
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "bam",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.O)\n    return inputs.O;\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "bai",
                    "type" : "File?",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.O)\n    return inputs.O.replace(/^.*[\\\\\\/]/, '').replace(/\\.[^/.]+$/, '').replace(/\\.bam/,'') + \".bai\";\n  return null;\n}"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 25000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-picard:2.9"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "java" ],
                  "arguments" : [ {
                    "position" : 1,
                    "prefix" : "-jar",
                    "shellQuote" : false,
                    "valueFrom" : "/usr/bin/picard-tools/picard.jar"
                  }, {
                    "position" : 1,
                    "shellQuote" : false,
                    "valueFrom" : "AddOrReplaceReadGroups"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-XX:-UseGCOverheadLimit"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
                  }, {
                    "position" : 2,
                    "shellQuote" : false,
                    "valueFrom" : "TMP_DIR=$(runtime.tmpdir)"
                  } ],
                  "doc" : "None\n",
                  "id" : "picard-AddOrReplaceReadGroups",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "I",
                  "source" : "sam_to_bam/output_bam"
                }, {
                  "id" : "O",
                  "valueFrom" : "${ return inputs.I.basename.replace(\".bam\", \".rg.bam\") }"
                }, {
                  "id" : "LB",
                  "source" : "add_rg_LB"
                }, {
                  "id" : "PL",
                  "source" : "add_rg_PL"
                }, {
                  "id" : "ID",
                  "source" : "add_rg_ID"
                }, {
                  "id" : "PU",
                  "source" : "add_rg_PU"
                }, {
                  "id" : "SM",
                  "source" : "add_rg_SM"
                }, {
                  "id" : "CN",
                  "source" : "add_rg_CN"
                }, {
                  "default" : "coordinate",
                  "id" : "SO"
                } ],
                "out" : [ {
                  "id" : "bam"
                }, {
                  "id" : "bai"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              } ],
              "id" : "alignment_sample",
              "class" : "Workflow"
            },
            "scatter" : [ "chunkfastq1", "chunkfastq2", "add_rg_ID", "add_rg_PU" ],
            "scatterMethod" : "dotproduct",
            "in" : [ {
              "id" : "ref_fasta",
              "source" : "ref_fasta"
            }, {
              "id" : "chunkfastq1",
              "source" : "flatten/chunks1"
            }, {
              "id" : "chunkfastq2",
              "source" : "flatten/chunks2"
            }, {
              "id" : "adapter",
              "source" : "get_sample_info/adapter"
            }, {
              "id" : "adapter2",
              "source" : "get_sample_info/adapter2"
            }, {
              "id" : "genome",
              "source" : "genome"
            }, {
              "id" : "bwa_output",
              "source" : "get_sample_info/bwa_output"
            }, {
              "id" : "add_rg_LB",
              "source" : "get_sample_info/LB"
            }, {
              "id" : "add_rg_PL",
              "source" : "get_sample_info/PL"
            }, {
              "id" : "add_rg_ID",
              "source" : "flatten/rg_ID"
            }, {
              "id" : "add_rg_PU",
              "source" : "flatten/rg_PU"
            }, {
              "id" : "add_rg_SM",
              "source" : "get_sample_info/ID"
            }, {
              "id" : "add_rg_CN",
              "source" : "get_sample_info/CN"
            } ],
            "out" : [ {
              "id" : "clstats1"
            }, {
              "id" : "clstats2"
            }, {
              "id" : "bam"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "mark_duplicates",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "I",
                "type" : [ {
                  "inputBinding" : {
                    "prefix" : "I=",
                    "separate" : false
                  },
                  "items" : "File",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2
                }
              }, {
                "id" : "MAX_SEQS",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "MAX_SEQUENCES_FOR_DISK_READ_ENDS_MAP=",
                  "separate" : false
                },
                "doc" : "This option is obsolete. ReadEnds will always be spilled to disk. Default value - 50000. This option can be set to 'null' to clear the default value."
              }, {
                "id" : "MAX_FILE_HANDLES",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "MAX_FILE_HANDLES_FOR_READ_ENDS_MAP=",
                  "separate" : false
                },
                "doc" : "Maximum number of file handles to keep open when spilling read ends to disk. Set this number a little lower than the per-process maximum number of file that may be open. This number can be found by executing the 'ulimit -n' command on a Unix system. Default value - 8000. This option can be set to 'null' to clear the default value."
              }, {
                "id" : "SORTING_COLLECTION_SIZE_RATIO",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "SORTING_COLLECTION_SIZE_RATIO=",
                  "separate" : false
                },
                "doc" : "This number, plus the maximum RAM available to the JVM, determine the memory footprint used by some of the sorting collections. If you are running out of memory, try reducing this number. Default value - 0.25. This option can be set to 'null' to clear the default value."
              }, {
                "id" : "BARCODE_TAG",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "BARCODE_TAG=",
                  "separate" : false
                },
                "doc" : "Barcode SAM tag (ex. BC for 10X Genomics) Default value - null."
              }, {
                "id" : "READ_ONE_BARCODE_TAG",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "READ_ONE_BARCODE_TAG=",
                  "separate" : false
                },
                "doc" : "Read one barcode SAM tag (ex. BX for 10X Genomics) Default value - null."
              }, {
                "id" : "READ_TWO_BARCODE_TAG",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "READ_TWO_BARCODE_TAG=",
                  "separate" : false
                },
                "doc" : "Read two barcode SAM tag (ex. BX for 10X Genomics) Default value - null."
              }, {
                "id" : "TAG_DUPLICATE_SET_MEMBERS",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "TAG_DUPLICATE_SET_MEMBERS=",
                  "separate" : false
                },
                "doc" : "If a read appears in a duplicate set, add two tags. The first tag, DUPLICATE_SET_SIZE_TAG (DS), indicates the size of the duplicate set. The smallest possible DS value is 2 which occurs when two reads map to the same portion of the reference only one of which is marked as duplicate. The second tag, DUPLICATE_SET_INDEX_TAG (DI), represents a unique identifier for the duplicate set to which the record belongs. This identifier is the index-in-file of the representative read that was selected out of the duplicate set. Default value - false. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
              }, {
                "id" : "REMOVE_SEQUENCING_DUPLICATES",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "REMOVE_SEQUENCING_DUPLICATES=",
                  "separate" : false
                },
                "doc" : "If true remove 'optical' duplicates and other duplicates that appear to have arisen from the sequencing process instead of the library preparation process, even if REMOVE_DUPLICATES is false. If REMOVE_DUPLICATES is true, all duplicates are removed and this option is ignored. Default value - false. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
              }, {
                "id" : "TAGGING_POLICY",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "TAGGING_POLICY=",
                  "separate" : false
                },
                "doc" : "Determines how duplicate types are recorded in the DT optional attribute. Default value - DontTag. This option can be set to 'null' to clear the default value. Possible values - {DontTag, OpticalOnly, All}"
              }, {
                "id" : "CLEAR_DT",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "CLEAR_DT=",
                  "separate" : false
                },
                "doc" : "Clear DT tag from input SAM records. Should be set to false if input SAM doesn't have this tag. Default true Default value - true. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
              }, {
                "id" : "O",
                "type" : "string",
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "O=",
                  "separate" : false
                },
                "doc" : "The output file to write marked records to Required."
              }, {
                "id" : "M",
                "type" : "string",
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "METRICS_FILE=",
                  "separate" : false
                },
                "doc" : "File to write duplication metrics to Required."
              }, {
                "id" : "REMOVE_DUPLICATES",
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "REMOVE_DUPLICATES=True"
                },
                "doc" : "If true do not write duplicates to the output file instead of writing them with appropriate flags set. Default value - false. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
              }, {
                "id" : "ASO",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "ASSUME_SORT_ORDER=",
                  "separate" : false
                },
                "doc" : "If not null, assume that the input file has this order even if the header says otherwise. Default value - null. Possible values - {unsorted, queryname, coordinate, duplicate, unknown} Cannot be used in conjuction with option(s) ASSUME_SORTED (AS)"
              }, {
                "id" : "DS",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "DUPLICATE_SCORING_STRATEGY=",
                  "separate" : false
                },
                "doc" : "The scoring strategy for choosing the non-duplicate among candidates. Default value - SUM_OF_BASE_QUALITIES. This option can be set to 'null' to clear the default value. Possible values - {SUM_OF_BASE_QUALITIES, TOTAL_MAPPED_REFERENCE_LENGTH, RANDOM}"
              }, {
                "id" : "PG",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "PROGRAM_RECORD_ID=",
                  "separate" : false
                },
                "doc" : "The program record ID for the @PG record(s) created by this program. Set to null to disable PG record creation. This string may have a suffix appended to avoid collision with other program record IDs. Default value - MarkDuplicates. This option can be set to 'null' to clear the default value."
              }, {
                "id" : "PG_VERSION",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "PROGRAM_GROUP_VERSION=",
                  "separate" : false
                },
                "doc" : "Value of VN tag of PG record to be created. If not specified, the version will be detected automatically. Default value - null."
              }, {
                "id" : "PG_COMMAND",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "PROGRAM_GROUP_COMMAND_LINE=",
                  "separate" : false
                },
                "doc" : "Value of CL tag of PG record to be created. If not supplied the command line will be detected automatically. Default value - null."
              }, {
                "id" : "PG_NAME",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "PROGRAM_GROUP_NAME=",
                  "separate" : false
                },
                "doc" : "Value of PN tag of PG record to be created. Default value - MarkDuplicates. This option can be set to 'null' to clear the default value."
              }, {
                "id" : "CO",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "COMMENT=",
                  "separate" : false
                },
                "doc" : "Comment(s) to include in the output file's header. Default value - null. This option may be specified 0 or more times."
              }, {
                "id" : "READ_NAME_REGEX",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "READ_NAME_REGEX=",
                  "separate" : false
                },
                "doc" : "Regular expression that can be used to parse read names in the incoming SAM file. Read names are parsed to extract three variables - tile/region, x coordinate and y coordinate. These values are used to estimate the rate of optical duplication in order to give a more accurate estimated library size. Set this option to null to disable optical duplicate detection, e.g. for RNA-seq or other data where duplicate sets are extremely large and estimating library complexity is not an aim. Note that without optical duplicate counts, library size estimation will be inaccurate. The regular expression should contain three capture groups for the three variables, in order. It must match the entire read name. Note that if the default regex is specified, a regex match is not actually done, but instead the read name is split on colon character. For 5 element names, the 3rd, 4th and 5th elements are assumed to be tile, x and y values. For 7 element names (CASAVA 1.8), the 5th, 6th, and 7th elements are assumed to be tile, x and y values. Default value - <optimized capture of last three ' -' separated fields as numeric values>. This option can be set to 'null' to clear the default value."
              }, {
                "id" : "OPTICAL_DUPLICATE_PIXEL_DISTANCE",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "OPTICAL_DUPLICATE_PIXEL_DISTANCE=",
                  "separate" : false
                },
                "doc" : "The maximum offset between two duplicate clusters in order to consider them optical duplicates. The default is appropriate for unpatterned versions of the Illumina platform. For the patterned flowcell models, 2500 is moreappropriate. For other platforms and models, users should experiment to find what works best. Default value - 100. This option can be set to 'null' to clear the default value."
              }, {
                "id" : "MAX_OPTICAL_DUPLICATE_SET_SIZE",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "MAX_OPTICAL_DUPLICATE_SET_SIZE=",
                  "separate" : false
                },
                "doc" : "This number is the maximum size of a set of duplicate reads for which we will attempt to determine which are optical duplicates. Please be aware that if you raise this value too high and do encounter a very large set of duplicate reads, it will severely affect the runtime of this tool. To completely disable this check, set the value to -1. Default value - 300000. This option can be set to 'null' to clear the default value."
              }, {
                "id" : "AS",
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "ASSUME_SORTED=True",
                  "separate" : false
                },
                "doc" : "If true (default), then the sort order in the header file will be ignored. Default value - true. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
              }, {
                "id" : "STOP_AFTER",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "STOP_AFTER=",
                  "separate" : false
                },
                "doc" : "Stop after processing N reads, mainly for debugging. Default value - 0. This option can be set to 'null' to clear the default value."
              }, {
                "id" : "QUIET",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "QUIET=True"
                }
              }, {
                "id" : "CREATE_MD5_FILE",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "CREATE_MD5_FILE=True"
                }
              }, {
                "id" : "CREATE_INDEX",
                "default" : true,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "CREATE_INDEX=True"
                }
              }, {
                "id" : "VERBOSITY",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "VERBOSITY=",
                  "separate" : false
                }
              }, {
                "id" : "VALIDATION_STRINGENCY",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "VALIDATION_STRINGENCY=",
                  "separate" : false
                }
              }, {
                "id" : "COMPRESSION_LEVEL",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "COMPRESSION_LEVEL=",
                  "separate" : false
                }
              }, {
                "id" : "MAX_RECORDS_IN_RAM",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "MAX_RECORDS_IN_RAM=",
                  "separate" : false
                }
              } ],
              "outputs" : [ {
                "id" : "bam",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.O)\n    return inputs.O;\n  return null;\n}\n"
                },
                "secondaryFiles" : [ "^.bai" ]
              }, {
                "id" : "bai",
                "type" : "File?",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.O)\n    return inputs.O.replace(/^.*[\\\\\\/]/, '').replace(/\\.[^/.]+$/, '').replace(/\\.bam/,'') + \".bai\";\n  return null;\n}\n"
                }
              }, {
                "id" : "mdmetrics",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.M)\n    return inputs.M;\n  return null;\n}\n"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : 80000,
                "coresMin" : 1
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-picard:2.9"
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "java" ],
              "arguments" : [ {
                "position" : 1,
                "prefix" : "-jar",
                "shellQuote" : false,
                "valueFrom" : "/usr/bin/picard-tools/picard.jar"
              }, {
                "position" : 1,
                "shellQuote" : false,
                "valueFrom" : "MarkDuplicates"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-XX:-UseGCOverheadLimit"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
              }, {
                "position" : 2,
                "shellQuote" : false,
                "valueFrom" : "TMP_DIR=$(runtime.tmpdir)"
              } ],
              "doc" : "None\n",
              "id" : "picard-MarkDuplicates",
              "class" : "CommandLineTool"
            },
            "in" : [ {
              "id" : "OPTICAL_DUPLICATE_PIXEL_DISTANCE",
              "source" : "opt_dup_pix_dist"
            }, {
              "id" : "I",
              "source" : "align/bam"
            }, {
              "id" : "O",
              "valueFrom" : "${ return inputs.I[0].basename.replace(/\\.chunk\\d\\d\\d\\.rg\\.bam/, \".rg.md.bam\") }"
            }, {
              "id" : "M",
              "valueFrom" : "${ return inputs.I[0].basename.replace(/\\.chunk\\d\\d\\d\\.rg\\.bam/, \".rg.md_metrics\") }"
            } ],
            "out" : [ {
              "id" : "bam"
            }, {
              "id" : "bai"
            }, {
              "id" : "mdmetrics"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "gather_metrics",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "bam",
                "type" : "File"
              }, {
                "id" : "genome",
                "type" : "string"
              }, {
                "id" : "bait_intervals",
                "type" : "File"
              }, {
                "id" : "target_intervals",
                "type" : "File"
              }, {
                "id" : "fp_intervals",
                "type" : "File"
              }, {
                "id" : "gatk_jar_path",
                "type" : "string"
              }, {
                "id" : "conpair_markers_bed",
                "type" : "string"
              }, {
                "id" : "ref_fasta",
                "type" : "File",
                "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
              } ],
              "outputs" : [ {
                "id" : "gcbias_pdf",
                "type" : "File",
                "outputSource" : "gcbias_metrics/pdf"
              }, {
                "id" : "gcbias_metrics",
                "type" : "File",
                "outputSource" : "gcbias_metrics/out_file"
              }, {
                "id" : "gcbias_summary",
                "type" : "File",
                "outputSource" : "gcbias_metrics/summary"
              }, {
                "id" : "as_metrics",
                "type" : "File",
                "outputSource" : "as_metrics/out_file"
              }, {
                "id" : "hs_metrics",
                "type" : "File",
                "outputSource" : "hs_metrics/out_file"
              }, {
                "id" : "per_target_coverage",
                "type" : "File",
                "outputSource" : "hst_metrics/per_target_out"
              }, {
                "id" : "insert_metrics",
                "type" : "File",
                "outputSource" : "insert_metrics/is_file"
              }, {
                "id" : "insert_pdf",
                "type" : "File",
                "outputSource" : "insert_metrics/is_hist"
              }, {
                "id" : "doc_basecounts",
                "type" : "File",
                "outputSource" : "doc/out_file"
              }, {
                "id" : "conpair_pileup",
                "type" : "File",
                "outputSource" : "pileup/out_file"
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "MultipleInputFeatureRequirement"
              }, {
                "class" : "ScatterFeatureRequirement"
              }, {
                "class" : "SubworkflowFeatureRequirement"
              }, {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "StepInputExpressionRequirement"
              } ],
              "successCodes" : [ ],
              "steps" : [ {
                "id" : "as_metrics",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "I",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "I=",
                      "separate" : false
                    }
                  }, {
                    "id" : "MAX_INSERT_SIZE",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MAX_INSERT_SIZE=",
                      "separate" : false
                    },
                    "doc" : "Paired-end reads above this insert size will be considered chimeric along with inter-chromosomal pairs. Default value - 100000. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "EXPECTED_PAIR_ORIENTATIONS",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "EXPECTED_PAIR_ORIENTATIONS=",
                      "separate" : false
                    },
                    "doc" : "Paired-end reads that do not have this expected orientation will be considered chimeric. Default value - [FR]. This option can be set to 'null' to clear the default value. Possible values - {FR, RF, TANDEM} This option may be specified 0 or more times. This option can be set to 'null' to clear the default list."
                  }, {
                    "id" : "ADAPTER_SEQUENCE",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "ADAPTER_SEQUENCE=",
                      "separate" : false
                    },
                    "doc" : "List of adapter sequences to use when processing the alignment metrics. Default value - [AATGATACGGCGACCACCGAGATCTACACTCTTTCCCTACACGACGCTCTTCCGATCT, AGATCGGAAGAGCTCGTATGCCGTCTTCTGCTTG, AATGATACGGCGACCACCGAGATCTACACTCTTTCCCTACACGACGCTCTTCCGATCT, AGATCGGAAGAGCGGTTCAGCAGGAATGCCGAGACCGATCTCGTATGCCGTCTTCTGCTTG, AATGATACGGCGACCACCGAGATCTACACTCTTTCCCTACACGACGCTCTTCCGATCT, AGATCGGAAGAGCACACGTCTGAACTCCAGTCACNNNNNNNNATCTCGTATGCCGTCTTCTGCTTG]. This option can be set to 'null' to clear the default value. This option may be specified 0 or more times. This option can be set to 'null' to clear the default list."
                  }, {
                    "id" : "LEVEL",
                    "type" : [ "null", {
                      "inputBinding" : {
                        "prefix" : "LEVEL=",
                        "separate" : false
                      },
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2
                    }
                  }, {
                    "id" : "BS",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "IS_BISULFITE_SEQUENCED=",
                      "separate" : false
                    },
                    "doc" : "Whether the SAM or BAM file consists of bisulfite sequenced reads. Default value - false. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
                  }, {
                    "id" : "O",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "O=",
                      "separate" : false
                    },
                    "doc" : "File to write the output to. Required."
                  }, {
                    "id" : "AS",
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "ASSUME_SORTED=True"
                    },
                    "doc" : "If true (default), then the sort order in the header file will be ignored. Default value - true. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
                  }, {
                    "id" : "STOP_AFTER",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "STOP_AFTER=",
                      "separate" : false
                    },
                    "doc" : "Stop after processing N reads, mainly for debugging. Default value - 0. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "REFERENCE_SEQUENCE",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "REFERENCE_SEQUENCE=",
                      "separate" : false
                    }
                  }, {
                    "id" : "QUIET",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "QUIET=True"
                    }
                  }, {
                    "id" : "CREATE_MD5_FILE",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_MD5_FILE=True"
                    }
                  }, {
                    "id" : "CREATE_INDEX",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_INDEX=True"
                    }
                  }, {
                    "id" : "VERBOSITY",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VERBOSITY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "VALIDATION_STRINGENCY",
                    "default" : "SILENT",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VALIDATION_STRINGENCY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "COMPRESSION_LEVEL",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "COMPRESSION_LEVEL=",
                      "separate" : false
                    }
                  }, {
                    "id" : "MAX_RECORDS_IN_RAM",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MAX_RECORDS_IN_RAM=",
                      "separate" : false
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "out_file",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n    if (inputs.O)\n        return inputs.O;\n    return null;\n}\n"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 16000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-picard:2.9"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "java" ],
                  "arguments" : [ {
                    "position" : 1,
                    "prefix" : "-jar",
                    "shellQuote" : false,
                    "valueFrom" : "/usr/bin/picard-tools/picard.jar"
                  }, {
                    "position" : 1,
                    "shellQuote" : false,
                    "valueFrom" : "CollectAlignmentSummaryMetrics"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-XX:-UseGCOverheadLimit"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
                  }, {
                    "position" : 2,
                    "shellQuote" : false,
                    "valueFrom" : "TMP_DIR=$(runtime.tmpdir)"
                  } ],
                  "doc" : "None\n",
                  "id" : "picard-CollectAlignmentSummaryMetrics",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "I",
                  "source" : "bam"
                }, {
                  "id" : "REFERENCE_SEQUENCE",
                  "source" : "ref_fasta"
                }, {
                  "id" : "O",
                  "valueFrom" : "${ return inputs.I.basename.replace(\".bam\", \".asmetrics\")}"
                }, {
                  "id" : "LEVEL",
                  "valueFrom" : "${return [\"null\", \"SAMPLE\"]}"
                } ],
                "out" : [ {
                  "id" : "out_file"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "hs_metrics",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "I",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "I=",
                      "separate" : false
                    }
                  }, {
                    "id" : "BI",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "BAIT_INTERVALS=",
                      "separate" : false
                    },
                    "doc" : "An interval list file that contains the locations of the baits used. Default value - null. This option must be specified at least 1 times."
                  }, {
                    "id" : "N",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "BAIT_SET_NAME=",
                      "separate" : false
                    },
                    "doc" : "Bait set name. If not provided it is inferred from the filename of the bait intervals. Default value - null."
                  }, {
                    "id" : "TI",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "TARGET_INTERVALS=",
                      "separate" : false
                    },
                    "doc" : "An interval list file that contains the locations of the targets. Default value - null. This option must be specified at least 1 times."
                  }, {
                    "id" : "O",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "O=",
                      "separate" : false
                    },
                    "doc" : "The output file to write the metrics to. Required."
                  }, {
                    "id" : "LEVEL",
                    "type" : [ "null", {
                      "inputBinding" : {
                        "prefix" : "LEVEL=",
                        "separate" : false
                      },
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2
                    }
                  }, {
                    "id" : "PER_TARGET_COVERAGE",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "PER_TARGET_COVERAGE=",
                      "separate" : false
                    },
                    "doc" : "An optional file to output per target coverage information to. Default value - null."
                  }, {
                    "id" : "PER_BASE_COVERAGE",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "PER_BASE_COVERAGE=",
                      "separate" : false
                    },
                    "doc" : "An optional file to output per base coverage information to. The per-base file contains one line per target base and can grow very large. It is not recommended for use with large target sets. Default value - null."
                  }, {
                    "id" : "NEAR_DISTANCE",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "NEAR_DISTANCE=",
                      "separate" : false
                    },
                    "doc" : "The maximum distance between a read and the nearest probe/bait/amplicon for the read to be considered 'near probe' and included in percent selected. Default value - 250. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "MQ",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MINIMUM_MAPPING_QUALITY=",
                      "separate" : false
                    },
                    "doc" : "Minimum mapping quality for a read to contribute coverage. Default value - 20. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "Q",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MINIMUM_BASE_QUALITY=",
                      "separate" : false
                    },
                    "doc" : "Minimum base quality for a base to contribute coverage. Default value - 20. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "CLIP_OVERLAPPING_READS",
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CLIP_OVERLAPPING_READS=True"
                    },
                    "doc" : "if we are to clip overlapping reads, false otherwise. Default value - true. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
                  }, {
                    "id" : "COVMAX",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "COVERAGE_CAP=",
                      "separate" : false
                    },
                    "doc" : "Parameter to set a max coverage limit for Theoretical Sensitivity calculations. Default is 200. Default value - 200. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "SAMPLE_SIZE",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "SAMPLE_SIZE=",
                      "separate" : false
                    },
                    "doc" : "Sample Size used for Theoretical Het Sensitivity sampling. Default is 10000. Default value - 10000. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "QUIET",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "QUIET=True"
                    }
                  }, {
                    "id" : "CREATE_MD5_FILE",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_MD5_FILE=True"
                    }
                  }, {
                    "id" : "CREATE_INDEX",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_INDEX=True"
                    }
                  }, {
                    "id" : "VERBOSITY",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VERBOSITY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "VALIDATION_STRINGENCY",
                    "default" : "SILENT",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VALIDATION_STRINGENCY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "COMPRESSION_LEVEL",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "COMPRESSION_LEVEL=",
                      "separate" : false
                    }
                  }, {
                    "id" : "MAX_RECORDS_IN_RAM",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MAX_RECORDS_IN_RAM=",
                      "separate" : false
                    }
                  }, {
                    "id" : "REFERENCE_SEQUENCE",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "REFERENCE_SEQUENCE=",
                      "separate" : false
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "out_file",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.O)\n    return inputs.O;\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "per_target_out",
                    "type" : "File?",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.PER_TARGET_COVERAGE)\n    return inputs.PER_TARGET_COVERAGE;\n  return null;\n}\n"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 16000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-picard:2.9"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "java" ],
                  "arguments" : [ {
                    "position" : 1,
                    "prefix" : "-jar",
                    "shellQuote" : false,
                    "valueFrom" : "/usr/bin/picard-tools/picard.jar"
                  }, {
                    "position" : 1,
                    "shellQuote" : false,
                    "valueFrom" : "CollectHsMetrics"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955) - 1)G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-XX:-UseGCOverheadLimit"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
                  }, {
                    "position" : 2,
                    "shellQuote" : false,
                    "valueFrom" : "TMP_DIR=$(runtime.tmpdir)"
                  } ],
                  "doc" : "None\n",
                  "id" : "picard-CollectHsMetrics",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "BI",
                  "source" : "bait_intervals"
                }, {
                  "id" : "TI",
                  "source" : "target_intervals"
                }, {
                  "id" : "I",
                  "source" : "bam"
                }, {
                  "id" : "REFERENCE_SEQUENCE",
                  "source" : "ref_fasta"
                }, {
                  "id" : "O",
                  "valueFrom" : "${ return inputs.I.basename.replace(\".bam\", \".hsmetrics\")}"
                }, {
                  "id" : "LEVEL",
                  "valueFrom" : "${ return [\"null\", \"SAMPLE\"];}"
                } ],
                "out" : [ {
                  "id" : "out_file"
                }, {
                  "id" : "per_target_out"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "hst_metrics",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "I",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "I=",
                      "separate" : false
                    }
                  }, {
                    "id" : "BI",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "BAIT_INTERVALS=",
                      "separate" : false
                    },
                    "doc" : "An interval list file that contains the locations of the baits used. Default value - null. This option must be specified at least 1 times."
                  }, {
                    "id" : "N",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "BAIT_SET_NAME=",
                      "separate" : false
                    },
                    "doc" : "Bait set name. If not provided it is inferred from the filename of the bait intervals. Default value - null."
                  }, {
                    "id" : "TI",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "TARGET_INTERVALS=",
                      "separate" : false
                    },
                    "doc" : "An interval list file that contains the locations of the targets. Default value - null. This option must be specified at least 1 times."
                  }, {
                    "id" : "O",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "O=",
                      "separate" : false
                    },
                    "doc" : "The output file to write the metrics to. Required."
                  }, {
                    "id" : "LEVEL",
                    "type" : [ "null", {
                      "inputBinding" : {
                        "prefix" : "LEVEL=",
                        "separate" : false
                      },
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2
                    }
                  }, {
                    "id" : "PER_TARGET_COVERAGE",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "PER_TARGET_COVERAGE=",
                      "separate" : false
                    },
                    "doc" : "An optional file to output per target coverage information to. Default value - null."
                  }, {
                    "id" : "PER_BASE_COVERAGE",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "PER_BASE_COVERAGE=",
                      "separate" : false
                    },
                    "doc" : "An optional file to output per base coverage information to. The per-base file contains one line per target base and can grow very large. It is not recommended for use with large target sets. Default value - null."
                  }, {
                    "id" : "NEAR_DISTANCE",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "NEAR_DISTANCE=",
                      "separate" : false
                    },
                    "doc" : "The maximum distance between a read and the nearest probe/bait/amplicon for the read to be considered 'near probe' and included in percent selected. Default value - 250. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "MQ",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MINIMUM_MAPPING_QUALITY=",
                      "separate" : false
                    },
                    "doc" : "Minimum mapping quality for a read to contribute coverage. Default value - 20. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "Q",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MINIMUM_BASE_QUALITY=",
                      "separate" : false
                    },
                    "doc" : "Minimum base quality for a base to contribute coverage. Default value - 20. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "CLIP_OVERLAPPING_READS",
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CLIP_OVERLAPPING_READS=True"
                    },
                    "doc" : "if we are to clip overlapping reads, false otherwise. Default value - true. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
                  }, {
                    "id" : "COVMAX",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "COVERAGE_CAP=",
                      "separate" : false
                    },
                    "doc" : "Parameter to set a max coverage limit for Theoretical Sensitivity calculations. Default is 200. Default value - 200. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "SAMPLE_SIZE",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "SAMPLE_SIZE=",
                      "separate" : false
                    },
                    "doc" : "Sample Size used for Theoretical Het Sensitivity sampling. Default is 10000. Default value - 10000. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "QUIET",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "QUIET=True"
                    }
                  }, {
                    "id" : "CREATE_MD5_FILE",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_MD5_FILE=True"
                    }
                  }, {
                    "id" : "CREATE_INDEX",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_INDEX=True"
                    }
                  }, {
                    "id" : "VERBOSITY",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VERBOSITY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "VALIDATION_STRINGENCY",
                    "default" : "SILENT",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VALIDATION_STRINGENCY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "COMPRESSION_LEVEL",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "COMPRESSION_LEVEL=",
                      "separate" : false
                    }
                  }, {
                    "id" : "MAX_RECORDS_IN_RAM",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MAX_RECORDS_IN_RAM=",
                      "separate" : false
                    }
                  }, {
                    "id" : "REFERENCE_SEQUENCE",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "REFERENCE_SEQUENCE=",
                      "separate" : false
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "out_file",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.O)\n    return inputs.O;\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "per_target_out",
                    "type" : "File?",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.PER_TARGET_COVERAGE)\n    return inputs.PER_TARGET_COVERAGE;\n  return null;\n}\n"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 16000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-picard:2.9"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "java" ],
                  "arguments" : [ {
                    "position" : 1,
                    "prefix" : "-jar",
                    "shellQuote" : false,
                    "valueFrom" : "/usr/bin/picard-tools/picard.jar"
                  }, {
                    "position" : 1,
                    "shellQuote" : false,
                    "valueFrom" : "CollectHsMetrics"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955) - 1)G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-XX:-UseGCOverheadLimit"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
                  }, {
                    "position" : 2,
                    "shellQuote" : false,
                    "valueFrom" : "TMP_DIR=$(runtime.tmpdir)"
                  } ],
                  "doc" : "None\n",
                  "id" : "picard-CollectHsMetrics",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "BI",
                  "source" : "bait_intervals"
                }, {
                  "id" : "TI",
                  "source" : "target_intervals"
                }, {
                  "id" : "I",
                  "source" : "bam"
                }, {
                  "id" : "REFERENCE_SEQUENCE",
                  "source" : "ref_fasta"
                }, {
                  "id" : "O",
                  "valueFrom" : "${ return \"all_reads_hsmerics_dump.txt\"; }"
                }, {
                  "id" : "PER_TARGET_COVERAGE",
                  "valueFrom" : "${ return inputs.I.basename.replace(\".bam\", \".hstmetrics\")}"
                }, {
                  "id" : "LEVEL",
                  "valueFrom" : "${ return [\"ALL_READS\"];}"
                } ],
                "out" : [ {
                  "id" : "per_target_out"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "insert_metrics",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "I",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "I=",
                      "separate" : false
                    }
                  }, {
                    "id" : "H",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "HISTOGRAM_FILE=",
                      "separate" : false
                    },
                    "doc" : "File to write insert size Histogram chart to. Required."
                  }, {
                    "id" : "DEVIATIONS",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "DEVIATIONS=",
                      "separate" : false
                    },
                    "doc" : "Generate mean, sd and plots by trimming the data down to MEDIAN + DEVIATIONS*MEDIAN_ABSOLUTE_DEVIATION. This is done because insert size data typically includes enough anomalous values from chimeras and other artifacts to make the mean and sd grossly misleading regarding the real distribution. Default value - 10.0. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "W",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "HISTOGRAM_WIDTH=",
                      "separate" : false
                    },
                    "doc" : "Explicitly sets the Histogram width, overriding automatic truncation of Histogram tail. Also, when calculating mean and standard deviation, only bins <= Histogram_WIDTH will be included. Default value - null."
                  }, {
                    "id" : "M",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MINIMUM_PCT=",
                      "separate" : false
                    },
                    "doc" : "When generating the Histogram, discard any data categories (out of FR, TANDEM, RF) that have fewer than this percentage of overall reads. (Range - 0 to 1). Default value - 0.05. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "LEVEL",
                    "type" : [ "null", {
                      "inputBinding" : {
                        "prefix" : "LEVEL=",
                        "separate" : false
                      },
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2
                    }
                  }, {
                    "id" : "INCLUDE_DUPLICATES",
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "INCLUDE_DUPLICATES=True"
                    },
                    "doc" : "If true, also include reads marked as duplicates in the insert size histogram. Default value - false. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
                  }, {
                    "id" : "O",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "O=",
                      "separate" : false
                    },
                    "doc" : "File to write the output to. Required."
                  }, {
                    "id" : "AS",
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "ASSUME_SORTED=True",
                      "separate" : false
                    },
                    "doc" : "If true (default), then the sort order in the header file will be ignored. Default value - true. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
                  }, {
                    "id" : "STOP_AFTER",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "STOP_AFTER=",
                      "separate" : false
                    },
                    "doc" : "Stop after processing N reads, mainly for debugging. Default value - 0. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "QUIET",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "QUIET=True"
                    }
                  }, {
                    "id" : "CREATE_MD5_FILE",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_MD5_FILE=True"
                    }
                  }, {
                    "id" : "CREATE_INDEX",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_INDEX=True"
                    }
                  }, {
                    "id" : "VERBOSITY",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VERBOSITY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "VALIDATION_STRINGENCY",
                    "default" : "SILENT",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VALIDATION_STRINGENCY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "COMPRESSION_LEVEL",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "COMPRESSION_LEVEL=",
                      "separate" : false
                    }
                  }, {
                    "id" : "MAX_RECORDS_IN_RAM",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MAX_RECORDS_IN_RAM=",
                      "separate" : false
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "is_file",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.O)\n    return inputs.O;\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "is_hist",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.H)\n    return inputs.H;\n  return null;\n}\n"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 16000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-picard:2.9"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "java" ],
                  "arguments" : [ {
                    "position" : 1,
                    "prefix" : "-jar",
                    "shellQuote" : false,
                    "valueFrom" : "/usr/bin/picard-tools/picard.jar"
                  }, {
                    "position" : 1,
                    "shellQuote" : false,
                    "valueFrom" : "CollectInsertSizeMetrics"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-XX:-UseGCOverheadLimit"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
                  }, {
                    "position" : 2,
                    "shellQuote" : false,
                    "valueFrom" : "TMP_DIR=$(runtime.tmpdir)"
                  } ],
                  "doc" : "None\n",
                  "id" : "picard-CollectInsertSizeMetrics",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "I",
                  "source" : "bam"
                }, {
                  "id" : "H",
                  "valueFrom" : "${ return inputs.I.basename.replace(\".bam\", \".ismetrics.pdf\")}"
                }, {
                  "id" : "O",
                  "valueFrom" : "${ return inputs.I.basename.replace(\".bam\", \".ismetrics\")}"
                }, {
                  "id" : "LEVEL",
                  "valueFrom" : "${ return [\"null\", \"SAMPLE\"];}"
                } ],
                "out" : [ {
                  "id" : "is_file"
                }, {
                  "id" : "is_hist"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "gcbias_metrics",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "I",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "I=",
                      "separate" : false
                    }
                  }, {
                    "id" : "REFERENCE_SEQUENCE",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "REFERENCE_SEQUENCE=",
                      "separate" : false
                    }
                  }, {
                    "id" : "CHART",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CHART_OUTPUT=",
                      "separate" : false
                    },
                    "doc" : "The PDF file to render the chart to. Required."
                  }, {
                    "id" : "S",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "SUMMARY_OUTPUT=",
                      "separate" : false
                    },
                    "doc" : "The text file to write summary metrics to. Required."
                  }, {
                    "id" : "WINDOW_SIZE",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "SCAN_WINDOW_SIZE=",
                      "separate" : false
                    },
                    "doc" : "The size of the scanning windows on the reference genome that are used to bin reads. Default value - 100. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "MGF",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MINIMUM_GENOME_FRACTION=",
                      "separate" : false
                    },
                    "doc" : "For summary metrics, exclude GC windows that include less than this fraction of the genome. Default value - 1.0E-5. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "BS",
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "IS_BISULFITE_SEQUENCED=True"
                    },
                    "doc" : "Whether the SAM or BAM file consists of bisulfite sequenced reads. Default value - false. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
                  }, {
                    "id" : "ALSO_IGNORE_DUPLICATES",
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "ALSO_IGNORE_DUPLICATES=True"
                    },
                    "doc" : "to get additional results without duplicates. This option allows to gain two plots per level at the same time - one is the usual one and the other excludes duplicates. Default value - false. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
                  }, {
                    "id" : "O",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "O=",
                      "separate" : false
                    },
                    "doc" : "File to write the output to. Required."
                  }, {
                    "id" : "AS",
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "ASSUME_SORTED=True"
                    },
                    "doc" : "If true (default), then the sort order in the header file will be ignored. Default value - true. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
                  }, {
                    "id" : "STOP_AFTER",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "STOP_AFTER=",
                      "separate" : false
                    },
                    "doc" : "Stop after processing N reads, mainly for debugging. Default value - 0. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "QUIET",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "QUIET=True"
                    }
                  }, {
                    "id" : "CREATE_MD5_FILE",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_MD5_FILE=True"
                    }
                  }, {
                    "id" : "CREATE_INDEX",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_INDEX=True"
                    }
                  }, {
                    "id" : "VERBOSITY",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VERBOSITY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "VALIDATION_STRINGENCY",
                    "default" : "SILENT",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VALIDATION_STRINGENCY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "COMPRESSION_LEVEL",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "COMPRESSION_LEVEL=",
                      "separate" : false
                    }
                  }, {
                    "id" : "MAX_RECORDS_IN_RAM",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MAX_RECORDS_IN_RAM=",
                      "separate" : false
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "pdf",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.CHART)\n    return inputs.CHART;\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "out_file",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.O)\n    return inputs.O;\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "summary",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.S)\n    return inputs.S;\n  return null;\n}\n"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 16000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-picard:2.9"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "java" ],
                  "arguments" : [ {
                    "position" : 1,
                    "prefix" : "-jar",
                    "shellQuote" : false,
                    "valueFrom" : "/usr/bin/picard-tools/picard.jar"
                  }, {
                    "position" : 1,
                    "shellQuote" : false,
                    "valueFrom" : "CollectGcBiasMetrics"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-XX:-UseGCOverheadLimit"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
                  }, {
                    "position" : 2,
                    "shellQuote" : false,
                    "valueFrom" : "TMP_DIR=$(runtime.tmpdir)"
                  } ],
                  "doc" : "None\n",
                  "id" : "picard-CollectGcBiasMetrics",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "I",
                  "source" : "bam"
                }, {
                  "id" : "REFERENCE_SEQUENCE",
                  "source" : "ref_fasta"
                }, {
                  "id" : "O",
                  "valueFrom" : "${ return inputs.I.basename.replace(\".bam\", \".gcbiasmetrics\") }"
                }, {
                  "id" : "CHART",
                  "valueFrom" : "${ return inputs.I.basename.replace(\".bam\", \".gcbias.pdf\")}"
                }, {
                  "id" : "S",
                  "valueFrom" : "${ return inputs.I.basename.replace(\".bam\", \".gcbias.summary\")}"
                } ],
                "out" : [ {
                  "id" : "pdf"
                }, {
                  "id" : "out_file"
                }, {
                  "id" : "summary"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "doc",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "out",
                    "type" : [ "string", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--out"
                    },
                    "doc" : "An output file created by the walker. Will overwrite contents if file exists"
                  }, {
                    "id" : "minMappingQuality",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--minMappingQuality"
                    },
                    "doc" : "Minimum mapping quality of reads to count towards depth"
                  }, {
                    "id" : "maxMappingQuality",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--maxMappingQuality"
                    },
                    "doc" : "Maximum mapping quality of reads to count towards"
                  }, {
                    "id" : "minBaseQuality",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--minBaseQuality"
                    },
                    "doc" : "Minimum quality of bases to count towards depth"
                  }, {
                    "id" : "maxBaseQuality",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--maxBaseQuality"
                    },
                    "doc" : "Maximum quality of bases to count towards depth"
                  }, {
                    "id" : "countType",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--countType"
                    },
                    "doc" : "How should overlapping reads from the same"
                  }, {
                    "id" : "printBaseCounts",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--printBaseCounts"
                    },
                    "doc" : "Add base counts to per-locus output"
                  }, {
                    "id" : "omitLocusTable",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--omitLocusTable"
                    },
                    "doc" : "Do not calculate per-sample per-depth counts of loci"
                  }, {
                    "id" : "omitIntervalStatistics",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--omitIntervalStatistics"
                    },
                    "doc" : "Do not calculate per-interval statistics"
                  }, {
                    "id" : "omitDepthOutputAtEachBase",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--omitDepthOutputAtEachBase"
                    },
                    "doc" : "Do not output depth of coverage at each base"
                  }, {
                    "id" : "calculateCoverageOverGenes",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--calculateCoverageOverGenes"
                    },
                    "doc" : "Calculate coverage statistics over this list of genes"
                  }, {
                    "id" : "outputFormat",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--outputFormat"
                    },
                    "doc" : "The format of the output file"
                  }, {
                    "id" : "includeRefNSites",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--includeRefNSites"
                    },
                    "doc" : "Include sites where the reference is N"
                  }, {
                    "id" : "printBinEndpointsAndExit",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--printBinEndpointsAndExit"
                    },
                    "doc" : "Print the bin values and exit immediately"
                  }, {
                    "id" : "start",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--start"
                    },
                    "doc" : "Starting (left endpoint) for granular binning"
                  }, {
                    "id" : "stop",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--stop"
                    },
                    "doc" : "Ending (right endpoint) for granular binning"
                  }, {
                    "id" : "nBins",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--nBins"
                    },
                    "doc" : "Number of bins to use for granular binning"
                  }, {
                    "id" : "omitPerSampleStats",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--omitPerSampleStats"
                    },
                    "doc" : "Do not output the summary files per-sample"
                  }, {
                    "id" : "partitionType",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--partitionType"
                    },
                    "doc" : "Partition type for depth of coverage"
                  }, {
                    "id" : "includeDeletions",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--includeDeletions"
                    },
                    "doc" : "Include information on deletions"
                  }, {
                    "id" : "ignoreDeletionSites",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--ignoreDeletionSites"
                    },
                    "doc" : "Ignore sites consisting only of deletions"
                  }, {
                    "id" : "arg_file",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--arg_file"
                    },
                    "doc" : "Reads arguments from the specified file"
                  }, {
                    "id" : "input_file",
                    "type" : [ "File", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--input_file"
                    },
                    "doc" : "Input file containing sequence data (SAM or BAM)"
                  }, {
                    "id" : "read_buffer_size",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--read_buffer_size"
                    },
                    "doc" : "Number of reads per SAM file to buffer in memory"
                  }, {
                    "id" : "phone_home",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--phone_home"
                    },
                    "doc" : "Run reporting mode (NO_ET|AWS| STDOUT)"
                  }, {
                    "id" : "gatk_key",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--gatk_key"
                    },
                    "doc" : "GATK key file required to run with -et NO_ET"
                  }, {
                    "id" : "tag",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--tag"
                    },
                    "doc" : "Tag to identify this GATK run as part of a group of runs"
                  }, {
                    "id" : "read_filter",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--read_filter"
                    },
                    "doc" : "Filters to apply to reads before analysis"
                  }, {
                    "id" : "intervals",
                    "type" : [ "string", "File" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--intervals"
                    },
                    "doc" : "One or more genomic intervals over which to operate"
                  }, {
                    "id" : "excludeIntervals",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--excludeIntervals"
                    },
                    "doc" : "One or more genomic intervals to exclude from processing"
                  }, {
                    "id" : "interval_set_rule",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--interval_set_rule"
                    },
                    "doc" : "Set merging approach to use for combining interval inputs (UNION|INTERSECTION)"
                  }, {
                    "id" : "interval_merging",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--interval_merging"
                    },
                    "doc" : "Interval merging rule for abutting intervals (ALL| OVERLAPPING_ONLY)"
                  }, {
                    "id" : "interval_padding",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--interval_padding"
                    },
                    "doc" : "Amount of padding (in bp) to add to each interval"
                  }, {
                    "id" : "reference_sequence",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--reference_sequence"
                    },
                    "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
                  }, {
                    "id" : "nonDeterministicRandomSeed",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--nonDeterministicRandomSeed"
                    },
                    "doc" : "Use a non-deterministic random seed"
                  }, {
                    "id" : "maxRuntime",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--maxRuntime"
                    },
                    "doc" : "Stop execution cleanly as soon as maxRuntime has been reached"
                  }, {
                    "id" : "maxRuntimeUnits",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--maxRuntimeUnits"
                    },
                    "doc" : "Unit of time used by maxRuntime (NANOSECONDS|MICROSECONDS| MILLISECONDS|SECONDS|MINUTES| HOURS|DAYS)"
                  }, {
                    "id" : "downsampling_type",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--downsampling_type"
                    },
                    "doc" : "Type of read downsampling to employ at a given locus (NONE| ALL_READS|BY_SAMPLE)"
                  }, {
                    "id" : "downsample_to_fraction",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--downsample_to_fraction"
                    },
                    "doc" : "Fraction of reads to downsample to"
                  }, {
                    "id" : "downsample_to_coverage",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--downsample_to_coverage"
                    },
                    "doc" : "Target coverage threshold for downsampling to coverage"
                  }, {
                    "id" : "baq",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--baq"
                    },
                    "doc" : "Type of BAQ calculation to apply in the engine (OFF| CALCULATE_AS_NECESSARY| RECALCULATE)"
                  }, {
                    "id" : "baqGapOpenPenalty",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--baqGapOpenPenalty"
                    },
                    "doc" : "BAQ gap open penalty"
                  }, {
                    "id" : "refactor_NDN_cigar_string",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--refactor_NDN_cigar_string"
                    },
                    "doc" : "refactor cigar string with NDN elements to one element"
                  }, {
                    "id" : "fix_misencoded_quality_scores",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--fix_misencoded_quality_scores"
                    },
                    "doc" : "Fix mis-encoded base quality scores"
                  }, {
                    "id" : "allow_potentially_misencoded_quality_scores",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--allow_potentially_misencoded_quality_scores"
                    },
                    "doc" : "Ignore warnings about base quality score encoding"
                  }, {
                    "id" : "useOriginalQualities",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--useOriginalQualities"
                    },
                    "doc" : "Use the base quality scores from the OQ tag"
                  }, {
                    "id" : "defaultBaseQualities",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--defaultBaseQualities"
                    },
                    "doc" : "Assign a default base quality"
                  }, {
                    "id" : "performanceLog",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--performanceLog"
                    },
                    "doc" : "Write GATK runtime performance log to this file"
                  }, {
                    "id" : "BQSR",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--BQSR"
                    },
                    "doc" : "Input covariates table file for on-the-fly base quality score recalibration"
                  }, {
                    "id" : "disable_indel_quals",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--disable_indel_quals"
                    },
                    "doc" : "Disable printing of base insertion and deletion tags (with -BQSR)"
                  }, {
                    "id" : "emit_original_quals",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--emit_original_quals"
                    },
                    "doc" : "Emit the OQ tag with the original base qualities (with -BQSR)"
                  }, {
                    "id" : "preserve_qscores_less_than",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--preserve_qscores_less_than"
                    },
                    "doc" : "Don't recalibrate bases with quality scores less than this threshold (with -BQSR)"
                  }, {
                    "id" : "globalQScorePrior",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--globalQScorePrior"
                    },
                    "doc" : "Global Qscore Bayesian prior to use for BQSR"
                  }, {
                    "id" : "validation_strictness",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--validation_strictness"
                    },
                    "doc" : "How strict should we be with validation (STRICT|LENIENT| SILENT)"
                  }, {
                    "id" : "remove_program_records",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--remove_program_records"
                    },
                    "doc" : "Remove program records from the SAM header"
                  }, {
                    "id" : "keep_program_records",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--keep_program_records"
                    },
                    "doc" : "Keep program records in the SAM header"
                  }, {
                    "id" : "sample_rename_mapping_file",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--sample_rename_mapping_file"
                    },
                    "doc" : "Rename sample IDs on-the-fly at runtime using the provided mapping file"
                  }, {
                    "id" : "unsafe",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--unsafe"
                    },
                    "doc" : "Enable unsafe operations - nothing will be checked at runtime (ALLOW_N_CIGAR_READS| ALLOW_UNINDEXED_BAM| ALLOW_UNSET_BAM_SORT_ORDER| NO_READ_ORDER_VERIFICATION| ALLOW_SEQ_DICT_INCOMPATIBILITY| LENIENT_VCF_PROCESSING|ALL)"
                  }, {
                    "id" : "sites_only",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--sites_only"
                    },
                    "doc" : "Just output sites without genotypes (i.e. only the first 8 columns of the VCF)"
                  }, {
                    "id" : "never_trim_vcf_format_field",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--never_trim_vcf_format_field"
                    },
                    "doc" : "Always output all the records in VCF FORMAT fields, even if some are missing"
                  }, {
                    "id" : "bam_compression",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--bam_compression"
                    },
                    "doc" : "Compression level to use for writing BAM files (0 - 9, higher is more compressed)"
                  }, {
                    "id" : "simplifyBAM",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--simplifyBAM"
                    },
                    "doc" : "If provided, output BAM files will be simplified to include just key reads for downstream variation discovery analyses (removing duplicates, PF-, non-primary reads), as well stripping all extended tags from the kept reads except the read group identifier"
                  }, {
                    "id" : "disable_bam_indexing",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--disable_bam_indexing"
                    },
                    "doc" : "Turn off on-the-fly creation of"
                  }, {
                    "id" : "generate_md5",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--generate_md5"
                    },
                    "doc" : "Enable on-the-fly creation of"
                  }, {
                    "id" : "num_threads",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--num_threads"
                    },
                    "doc" : "Number of data threads to allocate to this analysis"
                  }, {
                    "id" : "num_cpu_threads_per_data_thread",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--num_cpu_threads_per_data_thread"
                    },
                    "doc" : "Number of CPU threads to allocate per data thread"
                  }, {
                    "id" : "monitorThreadEfficiency",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--monitorThreadEfficiency"
                    },
                    "doc" : "Enable threading efficiency monitoring"
                  }, {
                    "id" : "num_bam_file_handles",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--num_bam_file_handles"
                    },
                    "doc" : "Total number of BAM file handles to keep open simultaneously"
                  }, {
                    "id" : "read_group_black_list",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--read_group_black_list"
                    },
                    "doc" : "Exclude read groups based on tags"
                  }, {
                    "id" : "pedigree",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--pedigree"
                    },
                    "doc" : "Pedigree files for samples"
                  }, {
                    "id" : "pedigreeString",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--pedigreeString"
                    },
                    "doc" : "Pedigree string for samples"
                  }, {
                    "id" : "pedigreeValidationType",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--pedigreeValidationType"
                    },
                    "doc" : "Validation strictness for pedigree information (STRICT| SILENT)"
                  }, {
                    "id" : "variant_index_type",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--variant_index_type"
                    },
                    "doc" : "Type of IndexCreator to use for VCF/BCF indices (DYNAMIC_SEEK| DYNAMIC_SIZE|LINEAR|INTERVAL)"
                  }, {
                    "id" : "variant_index_parameter",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--variant_index_parameter"
                    },
                    "doc" : "Parameter to pass to the VCF/BCF IndexCreator"
                  }, {
                    "id" : "logging_level",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--logging_level"
                    },
                    "doc" : "Set the minimum level of logging"
                  }, {
                    "id" : "log_to_file",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--log_to_file"
                    },
                    "doc" : "Set the logging location"
                  }, {
                    "id" : "summaryCoverageThreshold",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--summaryCoverageThreshold"
                    },
                    "doc" : "Coverage threshold (in percent) for summarizing statistics"
                  }, {
                    "id" : "filter_reads_with_N_cigar",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--filter_reads_with_N_cigar"
                    },
                    "doc" : "filter out reads with CIGAR containing the N operator, instead of stop processing and report an error."
                  }, {
                    "id" : "filter_mismatching_base_and_quals",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--filter_mismatching_base_and_quals"
                    },
                    "doc" : "if a read has mismatching number of bases and base qualities, filter out the read instead of blowing up."
                  }, {
                    "id" : "filter_bases_not_stored",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--filter_bases_not_stored"
                    },
                    "doc" : "if a read has no stored bases (i.e. a '*'), filter out the read instead of blowing up."
                  } ],
                  "outputs" : [ {
                    "id" : "out_file",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.out)\n    return inputs.out;\n  return null;\n}\n"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 16000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-gatk:3.3-0"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "java" ],
                  "arguments" : [ {
                    "position" : 1,
                    "prefix" : "-jar",
                    "shellQuote" : false,
                    "valueFrom" : "/usr/bin/gatk.jar"
                  }, {
                    "position" : 1,
                    "prefix" : "-T",
                    "shellQuote" : false,
                    "valueFrom" : "DepthOfCoverage"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-XX:-UseGCOverheadLimit"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
                  } ],
                  "doc" : "None\n",
                  "id" : "gatk-DepthOfCoverage",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "input_file",
                  "source" : "bam"
                }, {
                  "id" : "intervals",
                  "source" : "fp_intervals"
                }, {
                  "id" : "reference_sequence",
                  "source" : "ref_fasta"
                }, {
                  "id" : "out",
                  "valueFrom" : "${ return inputs.input_file.basename.replace(\".bam\", \"_FP_base_counts.txt\") }"
                }, {
                  "id" : "omitLocustable",
                  "valueFrom" : "${ return true; }"
                }, {
                  "id" : "omitPerSampleStats",
                  "valueFrom" : "${ return true; }"
                }, {
                  "id" : "read_filter",
                  "valueFrom" : "${ return [\"BadCigar\"];}"
                }, {
                  "id" : "minMappingQuality",
                  "valueFrom" : "${ return \"10\"; }"
                }, {
                  "id" : "minBaseQuality",
                  "valueFrom" : "${ return \"3\"; }"
                }, {
                  "id" : "omitIntervals",
                  "valueFrom" : "${ return true; }"
                }, {
                  "id" : "printBaseCounts",
                  "valueFrom" : "${ return true; }"
                } ],
                "out" : [ {
                  "id" : "out_file"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "pileup",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "ref",
                    "type" : "File",
                    "inputBinding" : {
                      "prefix" : "--reference"
                    },
                    "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
                  }, {
                    "id" : "java_xmx",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "prefix" : "--xmx_java"
                    },
                    "doc" : "set up java -Xmx parameter"
                  }, {
                    "id" : "java_temp",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--temp_dir_java"
                    },
                    "doc" : "temporary directory to set -Djava.io.tmpdir"
                  }, {
                    "id" : "gatk",
                    "type" : [ [ "File", "string", "null" ] ],
                    "inputBinding" : {
                      "prefix" : "--gatk"
                    }
                  }, {
                    "id" : "markers_bed",
                    "type" : [ [ "File", "string" ] ],
                    "inputBinding" : {
                      "prefix" : "--markers"
                    }
                  }, {
                    "id" : "bam",
                    "type" : [ [ "File", "string" ] ],
                    "inputBinding" : {
                      "prefix" : "--bam"
                    },
                    "secondaryFiles" : [ "^.bai" ]
                  }, {
                    "id" : "outfile",
                    "type" : [ "string" ],
                    "inputBinding" : {
                      "prefix" : "--outfile"
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "out_file",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.outfile)\n    return inputs.outfile;\n  return null;\n}\n"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 16000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-conpair:0.3.3"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "python", "/usr/bin/conpair/scripts/run_gatk_pileup_for_sample.py" ],
                  "arguments" : [ ],
                  "doc" : "None\n",
                  "id" : "conpair-pileup",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "bam",
                  "source" : "bam"
                }, {
                  "id" : "ref",
                  "source" : "ref_fasta"
                }, {
                  "id" : "gatk",
                  "source" : "gatk_jar_path"
                }, {
                  "id" : "markers_bed",
                  "source" : "conpair_markers_bed"
                }, {
                  "id" : "java_xmx",
                  "valueFrom" : "${ return [\"24g\"]; }"
                }, {
                  "id" : "outfile",
                  "valueFrom" : "${ return inputs.bam.basename.replace(\".bam\", \".pileup\"); }"
                } ],
                "out" : [ {
                  "id" : "out_file"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              } ],
              "id" : "gather-metrics-sample",
              "class" : "Workflow"
            },
            "in" : [ {
              "id" : "bait_intervals",
              "source" : "bait_intervals"
            }, {
              "id" : "target_intervals",
              "source" : "target_intervals"
            }, {
              "id" : "fp_intervals",
              "source" : "fp_intervals"
            }, {
              "id" : "ref_fasta",
              "source" : "ref_fasta"
            }, {
              "id" : "conpair_markers_bed",
              "source" : "conpair_markers_bed"
            }, {
              "id" : "genome",
              "source" : "genome"
            }, {
              "id" : "gatk_jar_path",
              "source" : "gatk_jar_path"
            }, {
              "id" : "bam",
              "source" : "mark_duplicates/bam"
            } ],
            "out" : [ {
              "id" : "gcbias_pdf"
            }, {
              "id" : "gcbias_metrics"
            }, {
              "id" : "gcbias_summary"
            }, {
              "id" : "as_metrics"
            }, {
              "id" : "hs_metrics"
            }, {
              "id" : "per_target_coverage"
            }, {
              "id" : "insert_metrics"
            }, {
              "id" : "insert_pdf"
            }, {
              "id" : "doc_basecounts"
            }, {
              "id" : "conpair_pileup"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          } ],
          "id" : "sample-workflow",
          "class" : "Workflow"
        },
        "scatter" : [ "sample" ],
        "scatterMethod" : "dotproduct",
        "in" : [ {
          "id" : "sample",
          "source" : "pair"
        }, {
          "id" : "genome",
          "source" : "genome"
        }, {
          "id" : "opt_dup_pix_dist",
          "source" : "opt_dup_pix_dist"
        }, {
          "id" : "gatk_jar_path",
          "source" : "gatk_jar_path"
        }, {
          "id" : "bait_intervals",
          "source" : "bait_intervals"
        }, {
          "id" : "target_intervals",
          "source" : "target_intervals"
        }, {
          "id" : "fp_intervals",
          "source" : "fp_intervals"
        }, {
          "id" : "ref_fasta",
          "source" : "ref_fasta"
        }, {
          "id" : "mouse_fasta",
          "source" : "mouse_fasta"
        }, {
          "id" : "conpair_markers_bed",
          "source" : "conpair_markers_bed"
        } ],
        "out" : [ {
          "id" : "clstats1"
        }, {
          "id" : "clstats2"
        }, {
          "id" : "bam"
        }, {
          "id" : "md_metrics"
        }, {
          "id" : "as_metrics"
        }, {
          "id" : "hs_metrics"
        }, {
          "id" : "insert_metrics"
        }, {
          "id" : "insert_pdf"
        }, {
          "id" : "per_target_coverage"
        }, {
          "id" : "doc_basecounts"
        }, {
          "id" : "gcbias_pdf"
        }, {
          "id" : "gcbias_metrics"
        }, {
          "id" : "gcbias_summary"
        }, {
          "id" : "conpair_pileup"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "realignment",
        "run" : {
          "cwlVersion" : "v1.0",
          "inputs" : [ {
            "id" : "bams",
            "type" : "File[]",
            "secondaryFiles" : [ "^.bai" ]
          }, {
            "id" : "pair",
            "type" : {
              "items" : {
                "fields" : {
                  "CN" : "string",
                  "ID" : "string",
                  "LB" : "string",
                  "PL" : "string",
                  "PU" : "string[]",
                  "R1" : "File[]",
                  "R2" : "File[]",
                  "RG_ID" : "string[]",
                  "adapter" : "string",
                  "adapter2" : "string",
                  "bam" : "File[]",
                  "bwa_output" : "string",
                  "zR1" : "File[]",
                  "zR2" : "File[]"
                },
                "type" : "record"
              },
              "type" : "array"
            }
          }, {
            "id" : "ref_fasta",
            "type" : "File",
            "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
          }, {
            "id" : "intervals",
            "type" : "string[]"
          }, {
            "id" : "hapmap",
            "type" : "File",
            "secondaryFiles" : [ ".idx" ]
          }, {
            "id" : "dbsnp",
            "type" : "File",
            "secondaryFiles" : [ ".idx" ]
          }, {
            "id" : "indels_1000g",
            "type" : "File",
            "secondaryFiles" : [ ".idx" ]
          }, {
            "id" : "snps_1000g",
            "type" : "File",
            "secondaryFiles" : [ ".idx" ]
          }, {
            "id" : "covariates",
            "type" : "string[]"
          }, {
            "id" : "abra_ram_min",
            "type" : "int"
          } ],
          "outputs" : [ {
            "id" : "covint_list",
            "type" : "File",
            "outputSource" : "combine_intervals/mergedfile"
          }, {
            "id" : "covint_bed",
            "type" : "File",
            "outputSource" : "list2bed/output_file"
          }, {
            "id" : "qual_metrics",
            "type" : "File[]",
            "outputSource" : "parallel_printreads/qual_metrics"
          }, {
            "id" : "qual_pdf",
            "type" : "File[]",
            "outputSource" : "parallel_printreads/qual_pdf"
          }, {
            "id" : "outbams",
            "type" : "File[]",
            "outputSource" : "parallel_printreads/out",
            "secondaryFiles" : [ "^.bai" ]
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "MultipleInputFeatureRequirement"
          }, {
            "class" : "ScatterFeatureRequirement"
          }, {
            "class" : "SubworkflowFeatureRequirement"
          }, {
            "class" : "InlineJavascriptRequirement"
          } ],
          "successCodes" : [ ],
          "steps" : [ {
            "id" : "split_intervals",
            "run" : {
              "inputs" : [ {
                "id" : "interval_list",
                "type" : "string[]"
              } ],
              "outputs" : [ {
                "id" : "intervals",
                "type" : {
                  "items" : {
                    "items" : "string",
                    "type" : "array"
                  },
                  "type" : "array"
                }
              }, {
                "id" : "intervals_id",
                "type" : "string[]"
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              } ],
              "successCodes" : [ ],
              "expression" : "${ var intervals = []; var intervals_id = []; var output_object = {}; var interval_list = inputs.interval_list; while( interval_list.length > 0 ) { var interval_split = interval_list.splice(0, 10); intervals.push(interval_split); intervals_id.push(interval_split.join('_')); } output_object['intervals'] = intervals; output_object['intervals_id'] = intervals_id; return output_object; }",
              "id" : "split_intervals",
              "class" : "ExpressionTool"
            },
            "in" : [ {
              "id" : "interval_list",
              "source" : "intervals"
            } ],
            "out" : [ {
              "id" : "intervals"
            }, {
              "id" : "intervals_id"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "gatk_find_covered_intervals",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "arg_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--arg_file"
                },
                "doc" : "Reads arguments from the specified file"
              }, {
                "id" : "input_file",
                "type" : {
                  "inputBinding" : {
                    "prefix" : "--input_file"
                  },
                  "items" : "File",
                  "type" : "array"
                },
                "inputBinding" : {
                  "position" : 2
                },
                "doc" : "Input file containing sequence data (SAM or BAM)"
              }, {
                "id" : "read_buffer_size",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--read_buffer_size"
                },
                "doc" : "Number of reads per SAM file to buffer in memory"
              }, {
                "id" : "phone_home",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--phone_home"
                },
                "doc" : "Run reporting mode (NO_ET|AWS| STDOUT)"
              }, {
                "id" : "gatk_key",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--gatk_key"
                },
                "doc" : "GATK key file required to run with -et NO_ET"
              }, {
                "id" : "tag",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--tag"
                },
                "doc" : "Tag to identify this GATK run as part of a group of runs"
              }, {
                "id" : "read_filter",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--read_filter"
                },
                "doc" : "Filters to apply to reads before analysis"
              }, {
                "id" : "intervals",
                "type" : {
                  "inputBinding" : {
                    "prefix" : "--intervals",
                    "separate" : true
                  },
                  "items" : "string",
                  "type" : "array"
                },
                "inputBinding" : {
                  "position" : 2
                },
                "doc" : "One or more genomic intervals over which to operate"
              }, {
                "id" : "excludeIntervals",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--excludeIntervals"
                },
                "doc" : "One or more genomic intervals to exclude from processing"
              }, {
                "id" : "interval_set_rule",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--interval_set_rule"
                },
                "doc" : "Set merging approach to use for combining interval inputs (UNION|INTERSECTION)"
              }, {
                "id" : "interval_merging",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--interval_merging"
                },
                "doc" : "Interval merging rule for abutting intervals (ALL| OVERLAPPING_ONLY)"
              }, {
                "id" : "interval_padding",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--interval_padding"
                },
                "doc" : "Amount of padding (in bp) to add to each interval"
              }, {
                "id" : "reference_sequence",
                "type" : "File",
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--reference_sequence"
                },
                "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
              }, {
                "id" : "nonDeterministicRandomSeed",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--nonDeterministicRandomSeed"
                },
                "doc" : "Use a non-deterministic random seed"
              }, {
                "id" : "maxRuntime",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--maxRuntime"
                },
                "doc" : "Stop execution cleanly as soon as maxRuntime has been reached"
              }, {
                "id" : "maxRuntimeUnits",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--maxRuntimeUnits"
                },
                "doc" : "Unit of time used by maxRuntime (NANOSECONDS|MICROSECONDS| MILLISECONDS|SECONDS|MINUTES| HOURS|DAYS)"
              }, {
                "id" : "downsampling_type",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--downsampling_type"
                },
                "doc" : "Type of read downsampling to employ at a given locus (NONE| ALL_READS|BY_SAMPLE)"
              }, {
                "id" : "downsample_to_fraction",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--downsample_to_fraction"
                },
                "doc" : "Fraction of reads to downsample to"
              }, {
                "id" : "downsample_to_coverage",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--downsample_to_coverage"
                },
                "doc" : "Target coverage threshold for downsampling to coverage"
              }, {
                "id" : "baq",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--baq"
                },
                "doc" : "Type of BAQ calculation to apply in the engine (OFF| CALCULATE_AS_NECESSARY| RECALCULATE)"
              }, {
                "id" : "baqGapOpenPenalty",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--baqGapOpenPenalty"
                },
                "doc" : "BAQ gap open penalty"
              }, {
                "id" : "refactor_NDN_cigar_string",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--refactor_NDN_cigar_string"
                },
                "doc" : "refactor cigar string with NDN elements to one element"
              }, {
                "id" : "fix_misencoded_quality_scores",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--fix_misencoded_quality_scores"
                },
                "doc" : "Fix mis-encoded base quality scores"
              }, {
                "id" : "allow_potentially_misencoded_quality_scores",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--allow_potentially_misencoded_quality_scores"
                },
                "doc" : "Ignore warnings about base quality score encoding"
              }, {
                "id" : "useOriginalQualities",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--useOriginalQualities"
                },
                "doc" : "Use the base quality scores from the OQ tag"
              }, {
                "id" : "defaultBaseQualities",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--defaultBaseQualities"
                },
                "doc" : "Assign a default base quality"
              }, {
                "id" : "performanceLog",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--performanceLog"
                },
                "doc" : "Write GATK runtime performance log to this file"
              }, {
                "id" : "BQSR",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--BQSR"
                },
                "doc" : "Input covariates table file for on-the-fly base quality score recalibration"
              }, {
                "id" : "disable_indel_quals",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--disable_indel_quals"
                },
                "doc" : "Disable printing of base insertion and deletion tags (with -BQSR)"
              }, {
                "id" : "emit_original_quals",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--emit_original_quals"
                },
                "doc" : "Emit the OQ tag with the original base qualities (with -BQSR)"
              }, {
                "id" : "preserve_qscores_less_than",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--preserve_qscores_less_than"
                },
                "doc" : "Don't recalibrate bases with quality scores less than this threshold (with -BQSR)"
              }, {
                "id" : "globalQScorePrior",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--globalQScorePrior"
                },
                "doc" : "Global Qscore Bayesian prior to use for BQSR"
              }, {
                "id" : "validation_strictness",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--validation_strictness"
                },
                "doc" : "How strict should we be with validation (STRICT|LENIENT| SILENT)"
              }, {
                "id" : "remove_program_records",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--remove_program_records"
                },
                "doc" : "Remove program records from the SAM header"
              }, {
                "id" : "keep_program_records",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--keep_program_records"
                },
                "doc" : "Keep program records in the SAM header"
              }, {
                "id" : "sample_rename_mapping_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--sample_rename_mapping_file"
                },
                "doc" : "Rename sample IDs on-the-fly at runtime using the provided mapping file"
              }, {
                "id" : "unsafe",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--unsafe"
                },
                "doc" : "Enable unsafe operations - nothing will be checked at runtime (ALLOW_N_CIGAR_READS| ALLOW_UNINDEXED_BAM| ALLOW_UNSET_BAM_SORT_ORDER| NO_READ_ORDER_VERIFICATION| ALLOW_SEQ_DICT_INCOMPATIBILITY| LENIENT_VCF_PROCESSING|ALL)"
              }, {
                "id" : "sites_only",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--sites_only"
                },
                "doc" : "Just output sites without genotypes (i.e. only the first 8 columns of the VCF)"
              }, {
                "id" : "never_trim_vcf_format_field",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--never_trim_vcf_format_field"
                },
                "doc" : "Always output all the records in VCF FORMAT fields, even if some are missing"
              }, {
                "id" : "bam_compression",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--bam_compression"
                },
                "doc" : "Compression level to use for writing BAM files (0 - 9, higher is more compressed)"
              }, {
                "id" : "simplifyBAM",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--simplifyBAM"
                },
                "doc" : "If provided, output BAM files will be simplified to include just key reads for downstream variation discovery analyses (removing duplicates, PF-, non-primary reads), as well stripping all extended tags from the kept reads except the read group identifier"
              }, {
                "id" : "disable_bam_indexing",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--disable_bam_indexing"
                },
                "doc" : "Turn off on-the-fly creation of"
              }, {
                "id" : "generate_md5",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--generate_md5"
                },
                "doc" : "Enable on-the-fly creation of"
              }, {
                "id" : "num_threads",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--num_threads"
                },
                "doc" : "Number of data threads to allocate to this analysis"
              }, {
                "id" : "num_cpu_threads_per_data_thread",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--num_cpu_threads_per_data_thread"
                },
                "doc" : "Number of CPU threads to allocate per data thread"
              }, {
                "id" : "monitorThreadEfficiency",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--monitorThreadEfficiency"
                },
                "doc" : "Enable threading efficiency monitoring"
              }, {
                "id" : "num_bam_file_handles",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--num_bam_file_handles"
                },
                "doc" : "Total number of BAM file handles to keep open simultaneously"
              }, {
                "id" : "read_group_black_list",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--read_group_black_list"
                },
                "doc" : "Exclude read groups based on tags"
              }, {
                "id" : "pedigree",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--pedigree"
                },
                "doc" : "Pedigree files for samples"
              }, {
                "id" : "pedigreeString",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--pedigreeString"
                },
                "doc" : "Pedigree string for samples"
              }, {
                "id" : "pedigreeValidationType",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--pedigreeValidationType"
                },
                "doc" : "Validation strictness for pedigree information (STRICT| SILENT)"
              }, {
                "id" : "variant_index_type",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--variant_index_type"
                },
                "doc" : "Type of IndexCreator to use for VCF/BCF indices (DYNAMIC_SEEK| DYNAMIC_SIZE|LINEAR|INTERVAL)"
              }, {
                "id" : "variant_index_parameter",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--variant_index_parameter"
                },
                "doc" : "Parameter to pass to the VCF/BCF IndexCreator"
              }, {
                "id" : "logging_level",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--logging_level"
                },
                "doc" : "Set the minimum level of logging"
              }, {
                "id" : "log_to_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--log_to_file"
                },
                "doc" : "Set the logging location"
              }, {
                "id" : "out",
                "type" : "string",
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--out"
                },
                "doc" : "An output file created by the walker. Will overwrite contents if file exists"
              }, {
                "id" : "uncovered",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--uncovered"
                },
                "doc" : "output intervals that fail the coverage threshold instead"
              }, {
                "id" : "coverage_threshold",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--coverage_threshold"
                },
                "doc" : "The minimum allowable coverage to be considered covered"
              }, {
                "id" : "minBaseQuality",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--minBaseQuality"
                },
                "doc" : "The minimum allowable base quality score to be counted for coverage"
              }, {
                "id" : "minMappingQuality",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--minMappingQuality"
                },
                "doc" : "The minimum allowable mapping quality score to be counted for coverage"
              }, {
                "id" : "activityProfileOut",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--activityProfileOut"
                },
                "doc" : "Output the raw activity profile results in IGV format"
              }, {
                "id" : "activeRegionOut",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--activeRegionOut"
                },
                "doc" : "Output the active region to this IGV formatted file"
              }, {
                "id" : "activeRegionIn",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--activeRegionIn"
                },
                "doc" : "Use this interval list file as the active regions to process"
              }, {
                "id" : "activeRegionExtension",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--activeRegionExtension"
                },
                "doc" : "The active region extension; if not provided defaults to Walker annotated default"
              }, {
                "id" : "forceActive",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--forceActive"
                },
                "doc" : "If provided, all bases will be tagged as active"
              }, {
                "id" : "activeRegionMaxSize",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--activeRegionMaxSize"
                },
                "doc" : "The active region maximum size; if not provided defaults to Walker annotated default"
              }, {
                "id" : "bandPassSigma",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--bandPassSigma"
                },
                "doc" : "The sigma of the band pass filter Gaussian kernel; if not provided defaults to Walker annotated default"
              }, {
                "id" : "activeProbabilityThreshold",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--activeProbabilityThreshold"
                },
                "doc" : "Threshold for the probability of a profile state being active."
              }, {
                "id" : "filter_reads_with_N_cigar",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--filter_reads_with_N_cigar"
                },
                "doc" : "filter out reads with CIGAR containing the N operator, instead of stop processing and report an error."
              }, {
                "id" : "filter_mismatching_base_and_quals",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--filter_mismatching_base_and_quals"
                },
                "doc" : "if a read has mismatching number of bases and base qualities, filter out the read instead of blowing up."
              }, {
                "id" : "filter_bases_not_stored",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--filter_bases_not_stored"
                },
                "doc" : "if a read has no stored bases (i.e. a '*'), filter out the read instead of blowing up."
              } ],
              "outputs" : [ {
                "id" : "fci_list",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.out)\n    return inputs.out;\n  return null;\n}\n"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : 24000,
                "coresMin" : 2
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-gatk:3.3-0"
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "java" ],
              "arguments" : [ {
                "position" : 1,
                "prefix" : "-jar",
                "shellQuote" : false,
                "valueFrom" : "/usr/bin/gatk.jar"
              }, {
                "position" : 1,
                "prefix" : "-T",
                "shellQuote" : false,
                "valueFrom" : "FindCoveredIntervals"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-XX:-UseGCOverheadLimit"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
              } ],
              "doc" : "None\n",
              "id" : "gatk-FindCoveredIntervals",
              "class" : "CommandLineTool"
            },
            "scatter" : [ "intervals", "out" ],
            "scatterMethod" : "dotproduct",
            "in" : [ {
              "id" : "pair",
              "source" : "pair"
            }, {
              "id" : "intervals_list",
              "source" : "intervals"
            }, {
              "id" : "reference_sequence",
              "source" : "ref_fasta"
            }, {
              "id" : "coverage_threshold",
              "valueFrom" : "${ return [\"3\"];}"
            }, {
              "id" : "minBaseQuality",
              "valueFrom" : "${ return [\"20\"];}"
            }, {
              "id" : "intervals",
              "source" : "split_intervals/intervals"
            }, {
              "id" : "input_file",
              "source" : "bams"
            }, {
              "id" : "out",
              "source" : "split_intervals/intervals_id"
            } ],
            "out" : [ {
              "id" : "fci_list"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "combine_intervals",
            "run" : {
              "inputs" : [ {
                "id" : "files",
                "type" : "File[]",
                "inputBinding" : {
                  "position" : 1
                }
              }, {
                "id" : "output_filename",
                "type" : "string"
              } ],
              "outputs" : [ {
                "id" : "mergedfile",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "random_stdout_a27c4780-e7af-41d3-ab93-e4f6f98c57ef"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "MultipleInputFeatureRequirement"
              } ],
              "successCodes" : [ ],
              "stdout" : "$(inputs.output_filename)",
              "baseCommand" : [ "cat" ],
              "arguments" : [ ],
              "id" : "combine_intervals",
              "class" : "CommandLineTool"
            },
            "in" : [ {
              "id" : "files",
              "source" : "gatk_find_covered_intervals/fci_list"
            }, {
              "id" : "pair",
              "source" : "pair"
            }, {
              "id" : "output_filename",
              "valueFrom" : "${ return inputs.pair[0].ID + \".\" + inputs.pair[1].ID + \".fci.list\"; }"
            } ],
            "out" : [ {
              "id" : "mergedfile"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "list2bed",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "input_file",
                "type" : [ "string", "File", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "prefix" : "--input_file"
                },
                "doc" : "picard interval list"
              }, {
                "id" : "no_sort",
                "default" : true,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "prefix" : "--no_sort"
                },
                "doc" : "sort bed file output"
              }, {
                "id" : "output_filename",
                "type" : "string",
                "inputBinding" : {
                  "prefix" : "--output_file"
                },
                "doc" : "output bed file"
              } ],
              "outputs" : [ {
                "id" : "output_file",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.output_filename)\n    return inputs.output_filename;\n  return null;\n}\n"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : 2000,
                "coresMin" : 1
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-list2bed:1.0.1"
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "python", "/usr/bin/list2bed.py" ],
              "arguments" : [ ],
              "doc" : "Convert a Picard interval list file to a UCSC BED format\n",
              "id" : "list2bed",
              "class" : "CommandLineTool"
            },
            "in" : [ {
              "id" : "input_file",
              "source" : "combine_intervals/mergedfile"
            }, {
              "id" : "output_filename",
              "valueFrom" : "${ return inputs.input_file.basename.replace(\".list\", \".bed\"); }"
            } ],
            "out" : [ {
              "id" : "output_file"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "abra",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "abra_ram_min",
                "type" : "int"
              }, {
                "id" : "threads",
                "default" : "16",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--threads"
                },
                "doc" : "Number of threads (default - 16)"
              }, {
                "id" : "bwa_ref",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--bwa-ref"
                },
                "doc" : "bwa ref"
              }, {
                "id" : "mmr",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mmr"
                },
                "doc" : "Max allowed mismatch rate when mapping reads back to contigs (default - 0.05)"
              }, {
                "id" : "kmer",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--kmer"
                },
                "doc" : "Optional assembly kmer size(delimit with commas if multiple sizes specified)"
              }, {
                "id" : "skip",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--skip"
                },
                "doc" : "If no target specified, skip realignment of chromosomes matching specified regex. Skipped reads are output without modification. Specify none to disable. (default - GL.*|hs37d5|chr.*random|chrUn. *|chrEBV|CMV|HBV|HCV.*|HIV. *|KSHV|HTLV.*|MCV|SV40|HPV.*)"
              }, {
                "id" : "sua",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--sua"
                },
                "doc" : "Do not use unmapped reads anchored by mate to trigger assembly. These reads are still eligible to contribute to assembly"
              }, {
                "id" : "contigs",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--contigs"
                },
                "doc" : "Optional file to which assembled contigs are written"
              }, {
                "id" : "ssc",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--ssc"
                },
                "doc" : "Skip usage of soft clipped sequences as putative contigs"
              }, {
                "id" : "keep_tmp",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--keep-tmp"
                },
                "doc" : "Do not delete the temporary directory"
              }, {
                "id" : "gtf",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--gtf"
                },
                "doc" : "GTF file defining exons and transcripts"
              }, {
                "id" : "mapq",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mapq"
                },
                "doc" : "Minimum mapping quality for a read to be used in assembly and be eligible for realignment (default - 20)"
              }, {
                "id" : "ref",
                "type" : "File",
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--ref"
                }
              }, {
                "id" : "index",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--index"
                },
                "doc" : "Enable BAM index generation when outputting sorted alignments (may require additonal memory)"
              }, {
                "id" : "out",
                "type" : {
                  "items" : "string",
                  "type" : "array"
                },
                "inputBinding" : {
                  "itemSeparator" : ",",
                  "position" : 2,
                  "prefix" : "--out"
                },
                "doc" : "Required list of output sam or bam file (s) separated by comma"
              }, {
                "id" : "sga",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--sga"
                },
                "doc" : "Scoring used for contig alignments (match, mismatch_penalty, gap_open_penalty, gap_extend_penalty) (default - 8,32,48,1)"
              }, {
                "id" : "mbq",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mbq"
                },
                "doc" : "Minimum base quality for inclusion in assembly. This value is compared against the sum of base qualities per kmer position (default - 20)"
              }, {
                "id" : "mnf",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mnf"
                },
                "doc" : "Assembly minimum node frequency (default - 1)"
              }, {
                "id" : "cons",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--cons"
                },
                "doc" : "Use positional consensus sequence when aligning high quality soft clipping"
              }, {
                "id" : "msr",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--msr"
                },
                "doc" : "Max reads to keep in memory per sample during the sort phase. When this value is exceeded, sort spills to disk (default - 1000000)"
              }, {
                "id" : "nosort",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--nosort"
                },
                "doc" : "Do not attempt to sort final output"
              }, {
                "id" : "in",
                "type" : {
                  "items" : "File",
                  "type" : "array"
                },
                "inputBinding" : {
                  "itemSeparator" : ",",
                  "position" : 2,
                  "prefix" : "--in"
                },
                "secondaryFiles" : [ "^.bai" ],
                "doc" : "Required list of input sam or bam file (s) separated by comma"
              }, {
                "id" : "ca",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--ca"
                },
                "doc" : "Contig anchor [M_bases_at_contig_edge, max_mismatches_near_edge] (default - 10,2)"
              }, {
                "id" : "rcf",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--rcf"
                },
                "doc" : "Minimum read candidate fraction for triggering assembly (default - 0.01)"
              }, {
                "id" : "gkl",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--gkl"
                },
                "doc" : "If specified, use GKL Intel Deflater (experimental)"
              }, {
                "id" : "maxn",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--maxn"
                },
                "doc" : "Maximum pre-pruned nodes in regional assembly (default - 150000)"
              }, {
                "id" : "undup",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--undup"
                },
                "doc" : "Unset duplicate flag"
              }, {
                "id" : "cl",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--cl"
                },
                "doc" : "Compression level of output bam file (s) (default - 5)"
              }, {
                "id" : "sc",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--sc"
                },
                "doc" : "Soft clip contig args [max_contigs, min_base_qual,frac_high_qual_bases, min_soft_clip_len] (default - 16,13,80,15)"
              }, {
                "id" : "sa",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--sa"
                },
                "doc" : "Skip assembly"
              }, {
                "id" : "mrn",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mrn"
                },
                "doc" : "Reads with noise score exceeding this value are not remapped. numMismatches+(numIndels*2) < readLength*mnr (default - 0.1)"
              }, {
                "id" : "junctions",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--junctions"
                },
                "doc" : "Splice junctions definition file"
              }, {
                "id" : "mrr",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mrr"
                },
                "doc" : "Regions containing more reads than this value are not processed. Use -1 to disable. (default - 1000000)"
              }, {
                "id" : "sobs",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--sobs"
                },
                "doc" : "Do not use observed indels in original alignments to generate contigs"
              }, {
                "id" : "dist",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--dist"
                },
                "doc" : "Max read move distance (default - 1000)"
              }, {
                "id" : "mer",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mer"
                },
                "doc" : "Min edge pruning ratio. Default value is appropriate for relatively sensitive somatic cases. May be increased for improved speed in germline only cases. (default - 0.01)"
              }, {
                "id" : "amq",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--amq"
                },
                "doc" : "Set mapq for alignments that map equally well to reference and an ABRA generated contig. default of -1 disables (default - -1)"
              }, {
                "id" : "mcl",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mcl"
                },
                "doc" : "Assembly minimum contig length (default - -1)"
              }, {
                "id" : "mad",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mad"
                },
                "doc" : "Regions with average depth exceeding this value will be downsampled (default - 1000)"
              }, {
                "id" : "single",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--single"
                },
                "doc" : "Input is single end"
              }, {
                "id" : "ws",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--ws"
                },
                "doc" : "Processing window size and overlap (size,overlap) (default - 400,200)"
              }, {
                "id" : "mac",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mac"
                },
                "doc" : "Max assembled contigs (default - 64)"
              }, {
                "id" : "in_vcf",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--in-vcf"
                },
                "doc" : "VCF containing known (or suspected) variant sites. Very large files should be avoided."
              }, {
                "id" : "target_kmers",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--target-kmers"
                },
                "doc" : "BED-like file containing target regions with per region kmer sizes in 4th column"
              }, {
                "id" : "targets",
                "type" : [ "null", "File", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--targets"
                },
                "doc" : "BED file containing target regions"
              }, {
                "id" : "log",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--log"
                },
                "doc" : "Logging level (trace,debug,info,warn, error) (default - info)"
              }, {
                "id" : "mcr",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mcr"
                },
                "doc" : "Max number of cached reads per sample per thread (default - 1000000)"
              } ],
              "outputs" : [ {
                "id" : "outbams",
                "type" : "File[]",
                "outputBinding" : {
                  "glob" : "${\n  return inputs.out;\n}\n"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : "$(inputs.abra_ram_min)",
                "coresMin" : 16
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-abra:2.17"
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "java" ],
              "arguments" : [ {
                "position" : 1,
                "prefix" : "-jar",
                "shellQuote" : false,
                "valueFrom" : "/usr/bin/abra.jar"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
              }, {
                "position" : 2,
                "prefix" : "--tmpdir",
                "shellQuote" : false,
                "valueFrom" : "$(runtime.tmpdir)"
              } ],
              "doc" : "None\n",
              "id" : "abra",
              "class" : "CommandLineTool"
            },
            "in" : [ {
              "id" : "abra_ram_min",
              "source" : "abra_ram_min"
            }, {
              "id" : "in",
              "source" : "bams"
            }, {
              "id" : "ref",
              "source" : "ref_fasta"
            }, {
              "id" : "out",
              "valueFrom" : "${ return inputs.in.map(function(x){ return x.basename.replace(\".bam\", \".abra.bam\"); }); }"
            }, {
              "id" : "targets",
              "source" : "list2bed/output_file"
            } ],
            "out" : [ {
              "id" : "outbams"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "index_bams",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "bam",
                "type" : "File",
                "inputBinding" : {
                  "prefix" : "--bam"
                }
              } ],
              "outputs" : [ {
                "id" : "bam_indexed",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "$(inputs.bam.basename)"
                },
                "secondaryFiles" : [ "^.bai", ".bai" ]
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "ResourceRequirement",
                "ramMin" : 16000,
                "coresMin" : 1
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-cmo-utils:1.9.15"
              }, {
                "class" : "InitialWorkDirRequirement",
                "listing" : [ "$(inputs.bam)" ]
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "cmo_index" ],
              "arguments" : [ ],
              "label" : "cmo-index",
              "class" : "CommandLineTool"
            },
            "scatter" : [ "bam" ],
            "scatterMethod" : "dotproduct",
            "in" : [ {
              "id" : "bam",
              "source" : "abra/outbams"
            } ],
            "out" : [ {
              "id" : "bam_indexed"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "gatk_base_recalibrator",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "arg_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--arg_file"
                },
                "doc" : "Reads arguments from the specified file"
              }, {
                "id" : "input_file",
                "type" : [ "null", {
                  "inputBinding" : {
                    "prefix" : "--input_file"
                  },
                  "items" : "File",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2
                },
                "secondaryFiles" : [ "^.bai" ],
                "doc" : "Input file containing sequence data (SAM or BAM)"
              }, {
                "id" : "read_buffer_size",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--read_buffer_size"
                },
                "doc" : "Number of reads per SAM file to buffer in memory"
              }, {
                "id" : "phone_home",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--phone_home"
                },
                "doc" : "Run reporting mode (NO_ET|AWS|STDOUT)"
              }, {
                "id" : "gatk_key",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--gatk_key"
                },
                "doc" : "GATK key file required to run with -et NO_ET"
              }, {
                "id" : "tag",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--tag"
                },
                "doc" : "Tag to identify this GATK run as part of a group of runs"
              }, {
                "id" : "read_filter",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--read_filter"
                },
                "doc" : "Filters to apply to reads before analysis"
              }, {
                "id" : "intervals",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--intervals"
                },
                "doc" : "One or more genomic intervals over which to operate"
              }, {
                "id" : "excludeIntervals",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--excludeIntervals"
                },
                "doc" : "One or more genomic intervals to exclude from processing"
              }, {
                "id" : "interval_set_rule",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--interval_set_rule"
                },
                "doc" : "Set merging approach to use for combining interval inputs (UNION|INTERSECTION)"
              }, {
                "id" : "interval_merging",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--interval_merging"
                },
                "doc" : "Interval merging rule for abutting intervals (ALL| OVERLAPPING_ONLY)"
              }, {
                "id" : "interval_padding",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--interval_padding"
                },
                "doc" : "Amount of padding (in bp) to add to each interval"
              }, {
                "id" : "reference_sequence",
                "type" : "File",
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--reference_sequence"
                },
                "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
              }, {
                "id" : "nonDeterministicRandomSeed",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--nonDeterministicRandomSeed"
                },
                "doc" : "Use a non-deterministic random seed"
              }, {
                "id" : "maxRuntime",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--maxRuntime"
                },
                "doc" : "Stop execution cleanly as soon as maxRuntime has been reached"
              }, {
                "id" : "maxRuntimeUnits",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--maxRuntimeUnits"
                },
                "doc" : "Unit of time used by maxRuntime (NANOSECONDS|MICROSECONDS| MILLISECONDS|SECONDS|MINUTES| HOURS|DAYS)"
              }, {
                "id" : "downsampling_type",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--downsampling_type"
                },
                "doc" : "Type of read downsampling to employ at a given locus (NONE|ALL_READS|BY_SAMPLE)"
              }, {
                "id" : "downsample_to_fraction",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--downsample_to_fraction"
                },
                "doc" : "Fraction of reads to downsample to"
              }, {
                "id" : "downsample_to_coverage",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--downsample_to_coverage"
                },
                "doc" : "Target coverage threshold for downsampling to coverage"
              }, {
                "id" : "baq",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--baq"
                },
                "doc" : "Type of BAQ calculation to apply in the engine (OFF| CALCULATE_AS_NECESSARY| RECALCULATE)"
              }, {
                "id" : "baqGapOpenPenalty",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--baqGapOpenPenalty"
                },
                "doc" : "BAQ gap open penalty"
              }, {
                "id" : "refactor_NDN_cigar_string",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--refactor_NDN_cigar_string"
                },
                "doc" : "refactor cigar string with NDN elements to one element"
              }, {
                "id" : "fix_misencoded_quality_scores",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--fix_misencoded_quality_scores"
                },
                "doc" : "Fix mis-encoded base quality scores"
              }, {
                "id" : "allow_potentially_misencoded_quality_scores",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--allow_potentially_misencoded_quality_scores"
                },
                "doc" : "Ignore warnings about base quality score encoding"
              }, {
                "id" : "useOriginalQualities",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--useOriginalQualities"
                },
                "doc" : "Use the base quality scores from the OQ tag"
              }, {
                "id" : "defaultBaseQualities",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--defaultBaseQualities"
                },
                "doc" : "Assign a default base quality"
              }, {
                "id" : "performanceLog",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--performanceLog"
                },
                "doc" : "Write GATK runtime performance log to this file"
              }, {
                "id" : "BQSR",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--BQSR"
                },
                "doc" : "Input covariates table file for on-the-fly base quality score recalibration"
              }, {
                "id" : "disable_indel_quals",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--disable_indel_quals"
                },
                "doc" : "Disable printing of base insertion and deletion tags (with -BQSR)"
              }, {
                "id" : "emit_original_quals",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--emit_original_quals"
                },
                "doc" : "Emit the OQ tag with the original base qualities (with -BQSR)"
              }, {
                "id" : "preserve_qscores_less_than",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--preserve_qscores_less_than"
                },
                "doc" : "Don't recalibrate bases with quality scores less than this threshold (with -BQSR)"
              }, {
                "id" : "globalQScorePrior",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--globalQScorePrior"
                },
                "doc" : "Global Qscore Bayesian prior to use for BQSR"
              }, {
                "id" : "validation_strictness",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--validation_strictness"
                },
                "doc" : "How strict should we be with validation (STRICT|LENIENT| SILENT)"
              }, {
                "id" : "remove_program_records",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--remove_program_records"
                },
                "doc" : "Remove program records from the SAM header"
              }, {
                "id" : "keep_program_records",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--keep_program_records"
                },
                "doc" : "Keep program records in the SAM header"
              }, {
                "id" : "sample_rename_mapping_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--sample_rename_mapping_file"
                },
                "doc" : "Rename sample IDs on-the-fly at runtime using the provided mapping file"
              }, {
                "id" : "unsafe",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--unsafe"
                },
                "doc" : "Enable unsafe operations - nothing will be checked at runtime (ALLOW_N_CIGAR_READS| ALLOW_UNINDEXED_BAM| ALLOW_UNSET_BAM_SORT_ORDER| NO_READ_ORDER_VERIFICATION| ALLOW_SEQ_DICT_INCOMPATIBILITY| LENIENT_VCF_PROCESSING|ALL)"
              }, {
                "id" : "sites_only",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--sites_only"
                },
                "doc" : "Just output sites without genotypes (i.e. only the first 8 columns of the VCF)"
              }, {
                "id" : "never_trim_vcf_format_field",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--never_trim_vcf_format_field"
                },
                "doc" : "Always output all the records in VCF FORMAT fields, even if some are missing"
              }, {
                "id" : "bam_compression",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--bam_compression"
                },
                "doc" : "Compression level to use for writing BAM files (0 - 9, higher is more compressed)"
              }, {
                "id" : "simplifyBAM",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--simplifyBAM"
                },
                "doc" : "If provided, output BAM files will be simplified to include just key reads for downstream variation discovery analyses (removing duplicates, PF-, non-primary reads), as well stripping all extended tags from the kept reads except the read group identifier"
              }, {
                "id" : "disable_bam_indexing",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--disable_bam_indexing"
                },
                "doc" : "Turn off on-the-fly creation of"
              }, {
                "id" : "generate_md5",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--generate_md5"
                },
                "doc" : "Enable on-the-fly creation of"
              }, {
                "id" : "num_threads",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--num_threads"
                },
                "doc" : "Number of data threads to allocate to this analysis"
              }, {
                "id" : "num_cpu_threads_per_data_thread",
                "default" : "8",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--num_cpu_threads_per_data_thread"
                },
                "doc" : "Number of CPU threads to allocate per data thread"
              }, {
                "id" : "monitorThreadEfficiency",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--monitorThreadEfficiency"
                },
                "doc" : "Enable threading efficiency monitoring"
              }, {
                "id" : "num_bam_file_handles",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--num_bam_file_handles"
                },
                "doc" : "Total number of BAM file handles to keep open simultaneously"
              }, {
                "id" : "read_group_black_list",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--read_group_black_list"
                },
                "doc" : "Exclude read groups based on tags"
              }, {
                "id" : "pedigree",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--pedigree"
                },
                "doc" : "Pedigree files for samples"
              }, {
                "id" : "pedigreeString",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--pedigreeString"
                },
                "doc" : "Pedigree string for samples"
              }, {
                "id" : "pedigreeValidationType",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--pedigreeValidationType"
                },
                "doc" : "Validation strictness for pedigree information (STRICT| SILENT)"
              }, {
                "id" : "variant_index_type",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--variant_index_type"
                },
                "doc" : "Type of IndexCreator to use for VCF/BCF indices (DYNAMIC_SEEK| DYNAMIC_SIZE|LINEAR|INTERVAL)"
              }, {
                "id" : "variant_index_parameter",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--variant_index_parameter"
                },
                "doc" : "Parameter to pass to the VCF/BCF IndexCreator"
              }, {
                "id" : "logging_level",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--logging_level"
                },
                "doc" : "Set the minimum level of logging"
              }, {
                "id" : "log_to_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--log_to_file"
                },
                "doc" : "Set the logging location"
              }, {
                "id" : "out",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--out"
                },
                "doc" : "The output recalibration table file to create"
              }, {
                "id" : "knownSites",
                "type" : {
                  "inputBinding" : {
                    "prefix" : "--knownSites"
                  },
                  "items" : "File",
                  "type" : "array"
                },
                "inputBinding" : {
                  "position" : 2
                },
                "secondaryFiles" : [ ".idx" ],
                "doc" : "A database of known polymorphic sites to skip over in the recalibration algorithm"
              }, {
                "id" : "list",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--list"
                },
                "doc" : "List the available covariates and exit"
              }, {
                "id" : "covariate",
                "type" : {
                  "inputBinding" : {
                    "prefix" : "--covariate"
                  },
                  "items" : "string",
                  "type" : "array"
                },
                "inputBinding" : {
                  "position" : 2
                },
                "doc" : "One or more covariates to be used in the recalibration. Can be specified multiple times"
              }, {
                "id" : "no_standard_covs",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--no_standard_covs"
                },
                "doc" : "Do not use the standard set of covariates, but rather just the ones listed using the -cov argumentthout_dbsnp_potentially_ruining_quality,--run_without_dbsnp_potentially_ruining_quality If specified, allows the recalibrator to be used without a dbsnp rod. Very unsafe and for expert users only."
              }, {
                "id" : "solid_recal_mode",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--solid_recal_mode"
                },
                "doc" : "How should we recalibrate solid bases in which the reference was inserted? Options = DO_NOTHING, SET_Q_ZERO, SET_Q_ZERO_BASE_N, or REMOVE_REF_BIAS (DO_NOTHING| SET_Q_ZERO|SET_Q_ZERO_BASE_N| REMOVE_REF_BIAS)"
              }, {
                "id" : "solid_nocall_strategy",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--solid_nocall_strategy"
                },
                "doc" : "Defines the behavior of the recalibrator when it encounters no calls in the color space. Options = THROW_EXCEPTION, LEAVE_READ_UNRECALIBRATED, or PURGE_READ (THROW_EXCEPTION| LEAVE_READ_UNRECALIBRATED| PURGE_READ)"
              }, {
                "id" : "mismatches_context_size",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mismatches_context_size"
                },
                "doc" : "Size of the k-mer context to be used for base mismatches"
              }, {
                "id" : "indels_context_size",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--indels_context_size"
                },
                "doc" : "Size of the k-mer context to be used for base insertions and deletions"
              }, {
                "id" : "maximum_cycle_value",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--maximum_cycle_value"
                },
                "doc" : "The maximum cycle value permitted for the Cycle covariate"
              }, {
                "id" : "mismatches_default_quality",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--mismatches_default_quality"
                },
                "doc" : "default quality for the base mismatches covariate"
              }, {
                "id" : "insertions_default_quality",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--insertions_default_quality"
                },
                "doc" : "default quality for the base insertions covariate"
              }, {
                "id" : "deletions_default_quality",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--deletions_default_quality"
                },
                "doc" : "default quality for the base deletions covariate"
              }, {
                "id" : "low_quality_tail",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--low_quality_tail"
                },
                "doc" : "minimum quality for the bases in the tail of the reads to be considered"
              }, {
                "id" : "quantizing_levels",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--quantizing_levels"
                },
                "doc" : "number of distinct quality scores in the quantized output"
              }, {
                "id" : "binary_tag_name",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--binary_tag_name"
                },
                "doc" : "the binary tag covariate name if using it"
              }, {
                "id" : "sort_by_all_columns",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--sort_by_all_columns"
                },
                "doc" : "Sort the rows in the tables of reports"
              }, {
                "id" : "lowMemoryMode",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--lowMemoryMode"
                },
                "doc" : "Reduce memory usage in multi-threaded code at the expense of threading efficiency"
              }, {
                "id" : "bqsrBAQGapOpenPenalty",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--bqsrBAQGapOpenPenalty"
                },
                "doc" : "BQSR BAQ gap open penalty (Phred Scaled). Default value is 40. 30 is perhaps better for whole genome call sets"
              }, {
                "id" : "filter_reads_with_N_cigar",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--filter_reads_with_N_cigar"
                },
                "doc" : "filter out reads with CIGAR containing the N operator, instead of stop processing and report an error."
              }, {
                "id" : "filter_mismatching_base_and_quals",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--filter_mismatching_base_and_quals"
                },
                "doc" : "if a read has mismatching number of bases and base qualities, filter out the read instead of blowing up."
              }, {
                "id" : "filter_bases_not_stored",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--filter_bases_not_stored"
                },
                "doc" : "if a read has no stored bases (i.e. a '*'), filter out the read instead of blowing up."
              } ],
              "outputs" : [ {
                "id" : "recal_matrix",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.out)\n    return inputs.out;\n  return null;\n}\n"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : 24000,
                "coresMin" : 4
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-gatk:3.3-0"
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "java" ],
              "arguments" : [ {
                "position" : 1,
                "prefix" : "-jar",
                "shellQuote" : false,
                "valueFrom" : "/usr/bin/gatk.jar"
              }, {
                "position" : 1,
                "prefix" : "-T",
                "shellQuote" : false,
                "valueFrom" : "BaseRecalibrator"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-XX:-UseGCOverheadLimit"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
              } ],
              "doc" : "None\n",
              "id" : "gatk-BaseRecalibrator",
              "class" : "CommandLineTool"
            },
            "in" : [ {
              "id" : "reference_sequence",
              "source" : "ref_fasta"
            }, {
              "id" : "input_file",
              "source" : "index_bams/bam_indexed"
            }, {
              "id" : "dbsnp",
              "source" : "dbsnp"
            }, {
              "id" : "hapmap",
              "source" : "hapmap"
            }, {
              "id" : "indels_1000g",
              "source" : "indels_1000g"
            }, {
              "id" : "snps_1000g",
              "source" : "snps_1000g"
            }, {
              "id" : "knownSites",
              "valueFrom" : "${return [inputs.dbsnp,inputs.hapmap, inputs.indels_1000g, inputs.snps_1000g]}"
            }, {
              "id" : "covariate",
              "source" : "covariates"
            }, {
              "id" : "out",
              "valueFrom" : "${ return \"recal.matrix\"; }"
            }, {
              "id" : "read_filter",
              "valueFrom" : "${ return [\"BadCigar\"]; }"
            } ],
            "out" : [ {
              "id" : "recal_matrix"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "parallel_printreads",
            "run" : {
              "inputs" : [ {
                "id" : "input_file",
                "type" : "File"
              }, {
                "id" : "reference_sequence",
                "type" : "File"
              }, {
                "id" : "BQSR",
                "type" : "File"
              } ],
              "outputs" : [ {
                "id" : "out",
                "type" : "File",
                "outputSource" : "gatk_print_reads/out_bam",
                "secondaryFiles" : [ "^.bai" ]
              }, {
                "id" : "qual_metrics",
                "type" : "File",
                "outputSource" : "quality_metrics/qual_file"
              }, {
                "id" : "qual_pdf",
                "type" : "File",
                "outputSource" : "quality_metrics/qual_hist"
              } ],
              "hints" : [ ],
              "requirements" : [ ],
              "successCodes" : [ ],
              "steps" : [ {
                "id" : "gatk_print_reads",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "filter_bases_not_stored",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--filter_bases_not_stored"
                    },
                    "doc" : "if a read has no stored bases (i.e. a '*'), filter out the read instead of blowing up."
                  }, {
                    "id" : "out",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--out"
                    },
                    "doc" : "Write output to this BAM filename instead of STDOUT"
                  }, {
                    "id" : "readGroup",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--readGroup"
                    },
                    "doc" : "Exclude all reads with this read group from the output"
                  }, {
                    "id" : "platform",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--platform"
                    },
                    "doc" : "Exclude all reads with this platform from the output"
                  }, {
                    "id" : "number",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--number"
                    },
                    "doc" : "Print the first n reads from the file, discarding the rest"
                  }, {
                    "id" : "sample_file",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--sample_file"
                    },
                    "doc" : "File containing a list of samples (one per line). Can be specified multiple times"
                  }, {
                    "id" : "sample_name",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--sample_name"
                    },
                    "doc" : "Sample name to be included in the analysis. Can be specified multiple times."
                  }, {
                    "id" : "simplify",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--simplify"
                    },
                    "doc" : "Simplify all reads."
                  }, {
                    "id" : "arg_file",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--arg_file"
                    },
                    "doc" : "Reads arguments from the specified file"
                  }, {
                    "id" : "input_file",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--input_file"
                    },
                    "doc" : "Input file containing sequence data (SAM or BAM)"
                  }, {
                    "id" : "read_buffer_size",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--read_buffer_size"
                    },
                    "doc" : "Number of reads per SAM file to buffer in memory"
                  }, {
                    "id" : "phone_home",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--phone_home"
                    },
                    "doc" : "Run reporting mode (NO_ET|AWS| STDOUT)"
                  }, {
                    "id" : "gatk_key",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--gatk_key"
                    },
                    "doc" : "GATK key file required to run with -et NO_ET"
                  }, {
                    "id" : "tag",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--tag"
                    },
                    "doc" : "Tag to identify this GATK run as part of a group of runs"
                  }, {
                    "id" : "read_filter",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--read_filter"
                    },
                    "doc" : "Filters to apply to reads before analysis"
                  }, {
                    "id" : "intervals",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--intervals"
                    },
                    "doc" : "One or more genomic intervals over which to operate"
                  }, {
                    "id" : "excludeIntervals",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--excludeIntervals"
                    },
                    "doc" : "One or more genomic intervals to exclude from processing"
                  }, {
                    "id" : "interval_set_rule",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--interval_set_rule"
                    },
                    "doc" : "Set merging approach to use for combining interval inputs (UNION|INTERSECTION)"
                  }, {
                    "id" : "interval_merging",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--interval_merging"
                    },
                    "doc" : "Interval merging rule for abutting intervals (ALL| OVERLAPPING_ONLY)"
                  }, {
                    "id" : "interval_padding",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--interval_padding"
                    },
                    "doc" : "Amount of padding (in bp) to add to each interval"
                  }, {
                    "id" : "reference_sequence",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--reference_sequence"
                    },
                    "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
                  }, {
                    "id" : "nonDeterministicRandomSeed",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--nonDeterministicRandomSeed"
                    },
                    "doc" : "Use a non-deterministic random seed"
                  }, {
                    "id" : "maxRuntime",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--maxRuntime"
                    },
                    "doc" : "Stop execution cleanly as soon as maxRuntime has been reached"
                  }, {
                    "id" : "maxRuntimeUnits",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--maxRuntimeUnits"
                    },
                    "doc" : "Unit of time used by maxRuntime (NANOSECONDS|MICROSECONDS| MILLISECONDS|SECONDS|MINUTES| HOURS|DAYS)"
                  }, {
                    "id" : "downsampling_type",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--downsampling_type"
                    },
                    "doc" : "Type of read downsampling to employ at a given locus (NONE| ALL_READS|BY_SAMPLE)"
                  }, {
                    "id" : "downsample_to_fraction",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--downsample_to_fraction"
                    },
                    "doc" : "Fraction of reads to downsample to"
                  }, {
                    "id" : "downsample_to_coverage",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--downsample_to_coverage"
                    },
                    "doc" : "Target coverage threshold for downsampling to coverage"
                  }, {
                    "id" : "baq",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--baq"
                    },
                    "doc" : "Type of BAQ calculation to apply in the engine (OFF| CALCULATE_AS_NECESSARY| RECALCULATE)"
                  }, {
                    "id" : "baqGapOpenPenalty",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--baqGapOpenPenalty"
                    },
                    "doc" : "BAQ gap open penalty"
                  }, {
                    "id" : "refactor_NDN_cigar_string",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--refactor_NDN_cigar_string"
                    },
                    "doc" : "refactor cigar string with NDN elements to one element"
                  }, {
                    "id" : "fix_misencoded_quality_scores",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--fix_misencoded_quality_scores"
                    },
                    "doc" : "Fix mis-encoded base quality scores"
                  }, {
                    "id" : "allow_potentially_misencoded_quality_scores",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--allow_potentially_misencoded_quality_scores"
                    },
                    "doc" : "Ignore warnings about base quality score encoding"
                  }, {
                    "id" : "useOriginalQualities",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--useOriginalQualities"
                    },
                    "doc" : "Use the base quality scores from the OQ tag"
                  }, {
                    "id" : "defaultBaseQualities",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--defaultBaseQualities"
                    },
                    "doc" : "Assign a default base quality"
                  }, {
                    "id" : "performanceLog",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--performanceLog"
                    },
                    "doc" : "Write GATK runtime performance log to this file"
                  }, {
                    "id" : "BQSR",
                    "type" : [ "null", "string", "File" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--BQSR"
                    },
                    "doc" : "Input covariates table file for on-the-fly base quality score recalibration"
                  }, {
                    "id" : "disable_indel_quals",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--disable_indel_quals"
                    },
                    "doc" : "Disable printing of base insertion and deletion tags (with -BQSR)"
                  }, {
                    "id" : "emit_original_quals",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--emit_original_quals"
                    },
                    "doc" : "Emit the OQ tag with the original base qualities (with -BQSR)"
                  }, {
                    "id" : "preserve_qscores_less_than",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--preserve_qscores_less_than"
                    },
                    "doc" : "Don't recalibrate bases with quality scores less than this threshold (with -BQSR)"
                  }, {
                    "id" : "globalQScorePrior",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--globalQScorePrior"
                    },
                    "doc" : "Global Qscore Bayesian prior to use for BQSR"
                  }, {
                    "id" : "validation_strictness",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--validation_strictness"
                    },
                    "doc" : "How strict should we be with validation (STRICT|LENIENT| SILENT)"
                  }, {
                    "id" : "remove_program_records",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--remove_program_records"
                    },
                    "doc" : "Remove program records from the SAM header"
                  }, {
                    "id" : "keep_program_records",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--keep_program_records"
                    },
                    "doc" : "Keep program records in the SAM header"
                  }, {
                    "id" : "sample_rename_mapping_file",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--sample_rename_mapping_file"
                    },
                    "doc" : "Rename sample IDs on-the-fly at runtime using the provided mapping file"
                  }, {
                    "id" : "unsafe",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--unsafe"
                    },
                    "doc" : "Enable unsafe operations - nothing will be checked at runtime (ALLOW_N_CIGAR_READS| ALLOW_UNINDEXED_BAM| ALLOW_UNSET_BAM_SORT_ORDER| NO_READ_ORDER_VERIFICATION| ALLOW_SEQ_DICT_INCOMPATIBILITY| LENIENT_VCF_PROCESSING|ALL)"
                  }, {
                    "id" : "sites_only",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--sites_only"
                    },
                    "doc" : "Just output sites without genotypes (i.e. only the first 8 columns of the VCF)"
                  }, {
                    "id" : "never_trim_vcf_format_field",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--never_trim_vcf_format_field"
                    },
                    "doc" : "Always output all the records in VCF FORMAT fields, even if some are missing"
                  }, {
                    "id" : "bam_compression",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--bam_compression"
                    },
                    "doc" : "Compression level to use for writing BAM files (0 - 9, higher is more compressed)"
                  }, {
                    "id" : "simplifyBAM",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--simplifyBAM"
                    },
                    "doc" : "If provided, output BAM files will be simplified to include just key reads for downstream variation discovery analyses (removing duplicates, PF-, non-primary reads), as well stripping all extended tags from the kept reads except the read group identifier"
                  }, {
                    "id" : "disable_bam_indexing",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--disable_bam_indexing"
                    },
                    "doc" : "Turn off on-the-fly creation of"
                  }, {
                    "id" : "generate_md5",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--generate_md5"
                    },
                    "doc" : "Enable on-the-fly creation of"
                  }, {
                    "id" : "num_threads",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--num_threads"
                    },
                    "doc" : "Number of data threads to allocate to this analysis"
                  }, {
                    "id" : "num_cpu_threads_per_data_thread",
                    "default" : "2",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--num_cpu_threads_per_data_thread"
                    },
                    "doc" : "Number of CPU threads to allocate per data thread"
                  }, {
                    "id" : "monitorThreadEfficiency",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--monitorThreadEfficiency"
                    },
                    "doc" : "Enable threading efficiency monitoring"
                  }, {
                    "id" : "num_bam_file_handles",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--num_bam_file_handles"
                    },
                    "doc" : "Total number of BAM file handles to keep open simultaneously"
                  }, {
                    "id" : "read_group_black_list",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--read_group_black_list"
                    },
                    "doc" : "Exclude read groups based on tags"
                  }, {
                    "id" : "pedigree",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--pedigree"
                    },
                    "doc" : "Pedigree files for samples"
                  }, {
                    "id" : "pedigreeString",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--pedigreeString"
                    },
                    "doc" : "Pedigree string for samples"
                  }, {
                    "id" : "pedigreeValidationType",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--pedigreeValidationType"
                    },
                    "doc" : "Validation strictness for pedigree information (STRICT| SILENT)"
                  }, {
                    "id" : "variant_index_type",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--variant_index_type"
                    },
                    "doc" : "Type of IndexCreator to use for VCF/BCF indices (DYNAMIC_SEEK| DYNAMIC_SIZE|LINEAR|INTERVAL)"
                  }, {
                    "id" : "variant_index_parameter",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--variant_index_parameter"
                    },
                    "doc" : "Parameter to pass to the VCF/BCF IndexCreator"
                  }, {
                    "id" : "logging_level",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--logging_level"
                    },
                    "doc" : "Set the minimum level of logging"
                  }, {
                    "id" : "log_to_file",
                    "type" : [ "null", {
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--log_to_file"
                    },
                    "doc" : "Set the logging location"
                  }, {
                    "id" : "filter_reads_with_N_cigar",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--filter_reads_with_N_cigar"
                    },
                    "doc" : "filter out reads with CIGAR containing the N operator, instead of stop processing and report an error."
                  }, {
                    "id" : "filter_mismatching_base_and_quals",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "--filter_mismatching_base_and_quals"
                    },
                    "doc" : "if a read has mismatching number of bases and base qualities, filter out the read instead of blowing up."
                  } ],
                  "outputs" : [ {
                    "id" : "out_bam",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.out)\n    return inputs.out;\n  return null;\n}\n"
                    },
                    "secondaryFiles" : [ "^.bai" ]
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 36000,
                    "coresMin" : 2
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-gatk:3.3-0"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "java" ],
                  "arguments" : [ {
                    "position" : 1,
                    "prefix" : "-jar",
                    "shellQuote" : false,
                    "valueFrom" : "/usr/bin/gatk.jar"
                  }, {
                    "position" : 1,
                    "prefix" : "-T",
                    "shellQuote" : false,
                    "valueFrom" : "PrintReads"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-XX:-UseGCOverheadLimit"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
                  } ],
                  "doc" : "None\n",
                  "id" : "gatk-PrintReads",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "reference_sequence",
                  "source" : "reference_sequence"
                }, {
                  "id" : "BQSR",
                  "source" : "BQSR"
                }, {
                  "id" : "input_file",
                  "source" : "input_file"
                }, {
                  "id" : "num_cpu_threads_per_data_thread",
                  "valueFrom" : "${ return \"5\"; }"
                }, {
                  "id" : "emit_original_quals",
                  "valueFrom" : "${ return true; }"
                }, {
                  "id" : "baq",
                  "valueFrom" : "${ return ['RECALCULATE'];}"
                }, {
                  "id" : "out",
                  "valueFrom" : "${ return inputs.input_file.basename.replace(\".bam\", \".printreads.bam\");}"
                } ],
                "out" : [ {
                  "id" : "out_bam"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "quality_metrics",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "I",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "I=",
                      "separate" : false
                    }
                  }, {
                    "id" : "REFERENCE_SEQUENCE",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "REFERENCE_SEQUENCE=",
                      "separate" : false
                    }
                  }, {
                    "id" : "EXT",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "FILE_EXTENSION=",
                      "separate" : false
                    },
                    "doc" : "Append the given file extension to all metric file names (ex. OUTPUT.insert_size_metrics.EXT). None if null Default value - null."
                  }, {
                    "id" : "PROGRAM",
                    "type" : [ "null", {
                      "inputBinding" : {
                        "prefix" : "PROGRAM=",
                        "separate" : false
                      },
                      "items" : "string",
                      "type" : "array"
                    } ],
                    "inputBinding" : {
                      "position" : 2
                    },
                    "doc" : "List of metrics programs to apply during the pass through the SAM file. Possible values - {CollectAlignmentSummaryMetrics, CollectInsertSizeMetrics, QualityScoreDistribution, MeanQualityByCycle} This option may be specified 0 or more times. This option can be set to 'null' to clear the default list."
                  }, {
                    "id" : "INTERVALS",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "INTERVALS=",
                      "separate" : false
                    },
                    "doc" : "An optional list of intervals to restrict analysis to. Only pertains to some of the PROGRAMs. Programs whose stand-alone CLP does not have an INTERVALS argument will silently ignore this argument. Default value - null."
                  }, {
                    "id" : "DB_SNP",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "DB_SNP=",
                      "separate" : false
                    },
                    "doc" : "VCF format dbSNP file, used to exclude regions around known polymorphisms from analysis by some PROGRAMs; PROGRAMs whose CLP doesn't allow for this argument will quietly ignore it. Default value - null."
                  }, {
                    "id" : "UNPAIRED",
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "INCLUDE_UNPAIRED=True"
                    },
                    "doc" : "Include unpaired reads in CollectSequencingArtifactMetrics. If set to true then all paired reads will be included as well - MINIMUM_INSERT_SIZE and MAXIMUM_INSERT_SIZE will be ignored in CollectSequencingArtifactMetrics. Default value - false. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
                  }, {
                    "id" : "O",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "OUTPUT=",
                      "separate" : false
                    },
                    "doc" : "Base name of output files. Required."
                  }, {
                    "id" : "AS",
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "ASSUME_SORTED=True",
                      "separate" : false
                    },
                    "doc" : "If true (default), then the sort order in the header file will be ignored. Default value - true. This option can be set to 'null' to clear the default value. Possible values - {true, false}"
                  }, {
                    "id" : "STOP_AFTER",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "STOP_AFTER=",
                      "separate" : false
                    },
                    "doc" : "Stop after processing N reads, mainly for debugging. Default value - 0. This option can be set to 'null' to clear the default value."
                  }, {
                    "id" : "QUIET",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "QUIET=True"
                    }
                  }, {
                    "id" : "CREATE_MD5_FILE",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_MD5_FILE=True"
                    }
                  }, {
                    "id" : "CREATE_INDEX",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "CREATE_INDEX=True"
                    }
                  }, {
                    "id" : "VERBOSITY",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VERBOSITY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "VALIDATION_STRINGENCY",
                    "default" : "SILENT",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "VALIDATION_STRINGENCY=",
                      "separate" : false
                    }
                  }, {
                    "id" : "COMPRESSION_LEVEL",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "COMPRESSION_LEVEL=",
                      "separate" : false
                    }
                  }, {
                    "id" : "MAX_RECORDS_IN_RAM",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "position" : 2,
                      "prefix" : "MAX_RECORDS_IN_RAM=",
                      "separate" : false
                    }
                  } ],
                  "outputs" : [ {
                    "id" : "qual_file",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.O)\n    return inputs.O.concat('.quality_by_cycle_metrics');\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "qual_hist",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.O)\n    return inputs.O.concat('.quality_by_cycle.pdf');\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "is_file",
                    "type" : "File?",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.O)\n    return inputs.O.concat('.insert_size_metrics');\n  return null;\n}\n"
                    }
                  }, {
                    "id" : "is_hist",
                    "type" : "File?",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.O)\n    return inputs.O.concat('.insert_size_histogram.pdf');\n  return null;\n}\n"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 16000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-picard:2.9"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "java" ],
                  "arguments" : [ {
                    "position" : 1,
                    "prefix" : "-jar",
                    "shellQuote" : false,
                    "valueFrom" : "/usr/bin/picard-tools/picard.jar"
                  }, {
                    "position" : 1,
                    "shellQuote" : false,
                    "valueFrom" : "CollectMultipleMetrics"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-XX:-UseGCOverheadLimit"
                  }, {
                    "position" : 0,
                    "shellQuote" : false,
                    "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
                  }, {
                    "position" : 2,
                    "shellQuote" : false,
                    "valueFrom" : "TMP_DIR=$(runtime.tmpdir)"
                  } ],
                  "doc" : "None\n",
                  "id" : "picard-CollectMultipleMetrics",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "I",
                  "source" : "gatk_print_reads/out_bam"
                }, {
                  "id" : "REFERENCE_SEQUENCE",
                  "source" : "reference_sequence"
                }, {
                  "id" : "PROGRAM",
                  "valueFrom" : "${return [\"null\",\"MeanQualityByCycle\"]}"
                }, {
                  "id" : "O",
                  "valueFrom" : "${ return inputs.I.basename.replace(\".bam\", \".qmetrics\")}"
                } ],
                "out" : [ {
                  "id" : "qual_file"
                }, {
                  "id" : "qual_hist"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              } ],
              "id" : "parallel_printreads",
              "class" : "Workflow"
            },
            "scatter" : [ "input_file" ],
            "scatterMethod" : "dotproduct",
            "in" : [ {
              "id" : "input_file",
              "source" : "index_bams/bam_indexed"
            }, {
              "id" : "reference_sequence",
              "source" : "ref_fasta"
            }, {
              "id" : "BQSR",
              "source" : "gatk_base_recalibrator/recal_matrix"
            } ],
            "out" : [ {
              "id" : "out"
            }, {
              "id" : "qual_metrics"
            }, {
              "id" : "qual_pdf"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          } ],
          "id" : "realignment",
          "class" : "Workflow"
        },
        "in" : [ {
          "id" : "pair",
          "source" : "pair"
        }, {
          "id" : "bams",
          "source" : "sample_alignment/bam"
        }, {
          "id" : "hapmap",
          "source" : "hapmap"
        }, {
          "id" : "dbsnp",
          "source" : "dbsnp"
        }, {
          "id" : "indels_1000g",
          "source" : "indels_1000g"
        }, {
          "id" : "snps_1000g",
          "source" : "snps_1000g"
        }, {
          "id" : "covariates",
          "source" : "covariates"
        }, {
          "id" : "genome",
          "source" : "genome"
        }, {
          "id" : "ref_fasta",
          "source" : "ref_fasta"
        }, {
          "id" : "intervals",
          "source" : "intervals"
        }, {
          "id" : "abra_ram_min",
          "source" : "abra_ram_min"
        } ],
        "out" : [ {
          "id" : "outbams"
        }, {
          "id" : "covint_list"
        }, {
          "id" : "covint_bed"
        }, {
          "id" : "qual_metrics"
        }, {
          "id" : "qual_pdf"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      } ],
      "id" : "alignment-pair",
      "class" : "Workflow"
    },
    "in" : [ {
      "id" : "runparams",
      "source" : "runparams"
    }, {
      "id" : "db_files",
      "source" : "db_files"
    }, {
      "id" : "pair",
      "source" : "pair"
    }, {
      "id" : "genome",
      "valueFrom" : "${ return inputs.runparams.genome }"
    }, {
      "id" : "intervals",
      "valueFrom" : "${ return inputs.runparams.intervals }"
    }, {
      "id" : "opt_dup_pix_dist",
      "valueFrom" : "${ return inputs.runparams.opt_dup_pix_dist }"
    }, {
      "id" : "hapmap",
      "source" : "hapmap"
    }, {
      "id" : "dbsnp",
      "source" : "dbsnp"
    }, {
      "id" : "indels_1000g",
      "source" : "indels_1000g"
    }, {
      "id" : "snps_1000g",
      "source" : "snps_1000g"
    }, {
      "id" : "covariates",
      "valueFrom" : "${ return inputs.runparams.covariates }"
    }, {
      "id" : "abra_scratch",
      "valueFrom" : "${ return inputs.runparams.abra_scratch }"
    }, {
      "id" : "abra_ram_min",
      "valueFrom" : "${ return inputs.runparams.abra_ram_min }"
    }, {
      "id" : "gatk_jar_path",
      "valueFrom" : "${ return inputs.runparams.gatk_jar_path }"
    }, {
      "id" : "bait_intervals",
      "valueFrom" : "${ return inputs.db_files.bait_intervals }"
    }, {
      "id" : "target_intervals",
      "valueFrom" : "${ return inputs.db_files.target_intervals }"
    }, {
      "id" : "fp_intervals",
      "valueFrom" : "${ return inputs.db_files.fp_intervals }"
    }, {
      "id" : "ref_fasta",
      "source" : "ref_fasta"
    }, {
      "id" : "mouse_fasta",
      "source" : "mouse_fasta"
    }, {
      "id" : "conpair_markers_bed",
      "valueFrom" : "${ return inputs.db_files.conpair_markers_bed }"
    } ],
    "out" : [ {
      "id" : "bams"
    }, {
      "id" : "clstats1"
    }, {
      "id" : "clstats2"
    }, {
      "id" : "md_metrics"
    }, {
      "id" : "covint_list"
    }, {
      "id" : "bed"
    }, {
      "id" : "as_metrics"
    }, {
      "id" : "hs_metrics"
    }, {
      "id" : "insert_metrics"
    }, {
      "id" : "insert_pdf"
    }, {
      "id" : "per_target_coverage"
    }, {
      "id" : "qual_metrics"
    }, {
      "id" : "qual_pdf"
    }, {
      "id" : "doc_basecounts"
    }, {
      "id" : "gcbias_pdf"
    }, {
      "id" : "gcbias_metrics"
    }, {
      "id" : "gcbias_summary"
    }, {
      "id" : "conpair_pileup"
    } ],
    "hints" : [ ],
    "requirements" : [ ]
  }, {
    "id" : "variant_calling",
    "run" : {
      "cwlVersion" : "v1.0",
      "inputs" : [ {
        "id" : "tumor_bam",
        "type" : "File"
      }, {
        "id" : "normal_bam",
        "type" : "File"
      }, {
        "id" : "genome",
        "type" : "string"
      }, {
        "id" : "bed",
        "type" : "File"
      }, {
        "id" : "normal_sample_name",
        "type" : "string"
      }, {
        "id" : "tumor_sample_name",
        "type" : "string"
      }, {
        "id" : "dbsnp",
        "type" : "File",
        "secondaryFiles" : [ ".idx" ]
      }, {
        "id" : "cosmic",
        "type" : "File",
        "secondaryFiles" : [ ".idx" ]
      }, {
        "id" : "mutect_dcov",
        "type" : "int"
      }, {
        "id" : "mutect_rf",
        "type" : "string[]"
      }, {
        "id" : "refseq",
        "type" : "File"
      }, {
        "id" : "hotspot_vcf",
        "type" : "string"
      }, {
        "id" : "ref_fasta",
        "type" : "File",
        "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
      }, {
        "id" : "facets_pcval",
        "type" : "int"
      }, {
        "id" : "facets_cval",
        "type" : "int"
      }, {
        "id" : "facets_snps",
        "type" : "File"
      }, {
        "id" : "complex_nn",
        "type" : "float"
      }, {
        "id" : "complex_tn",
        "type" : "float"
      } ],
      "outputs" : [ {
        "id" : "combine_vcf",
        "type" : "File",
        "outputSource" : "tabix_index/tabix_output_file",
        "secondaryFiles" : [ ".tbi" ]
      }, {
        "id" : "annotate_vcf",
        "type" : "File",
        "outputSource" : "annotate/annotate_vcf_output_file"
      }, {
        "id" : "facets_png",
        "type" : "File[]",
        "outputSource" : "call_variants/facets_png"
      }, {
        "id" : "facets_txt_hisens",
        "type" : "File",
        "outputSource" : "call_variants/facets_txt_hisens"
      }, {
        "id" : "facets_txt_purity",
        "type" : "File",
        "outputSource" : "call_variants/facets_txt_purity"
      }, {
        "id" : "facets_out",
        "type" : "File[]",
        "outputSource" : "call_variants/facets_out"
      }, {
        "id" : "facets_rdata",
        "type" : "File[]",
        "outputSource" : "call_variants/facets_rdata"
      }, {
        "id" : "facets_seg",
        "type" : "File[]",
        "outputSource" : "call_variants/facets_seg"
      }, {
        "id" : "facets_counts",
        "type" : "File",
        "outputSource" : "call_variants/facets_counts"
      }, {
        "id" : "mutect_vcf",
        "type" : "File",
        "outputSource" : "call_variants/mutect_vcf"
      }, {
        "id" : "mutect_callstats",
        "type" : "File",
        "outputSource" : "call_variants/mutect_callstats"
      }, {
        "id" : "vardict_vcf",
        "type" : "File",
        "outputSource" : "call_variants/vardict_vcf"
      }, {
        "id" : "vardict_norm_vcf",
        "type" : "File",
        "outputSource" : "filtering/vardict_vcf_filtering_output",
        "secondaryFiles" : [ ".tbi" ]
      }, {
        "id" : "mutect_norm_vcf",
        "type" : "File",
        "outputSource" : "filtering/mutect_vcf_filtering_output",
        "secondaryFiles" : [ ".tbi" ]
      } ],
      "hints" : [ ],
      "requirements" : [ {
        "class" : "MultipleInputFeatureRequirement"
      }, {
        "class" : "ScatterFeatureRequirement"
      }, {
        "class" : "SubworkflowFeatureRequirement"
      }, {
        "class" : "InlineJavascriptRequirement"
      }, {
        "class" : "StepInputExpressionRequirement"
      } ],
      "successCodes" : [ ],
      "steps" : [ {
        "id" : "normal_index",
        "run" : {
          "cwlVersion" : "v1.0",
          "inputs" : [ {
            "id" : "bam",
            "type" : "File",
            "inputBinding" : {
              "prefix" : "--bam"
            }
          } ],
          "outputs" : [ {
            "id" : "bam_indexed",
            "type" : "File",
            "outputBinding" : {
              "glob" : "$(inputs.bam.basename)"
            },
            "secondaryFiles" : [ "^.bai", ".bai" ]
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "ResourceRequirement",
            "ramMin" : 16000,
            "coresMin" : 1
          }, {
            "class" : "DockerRequirement",
            "dockerPull" : "mskcc/roslin-variant-cmo-utils:1.9.15"
          }, {
            "class" : "InitialWorkDirRequirement",
            "listing" : [ "$(inputs.bam)" ]
          } ],
          "successCodes" : [ ],
          "baseCommand" : [ "cmo_index" ],
          "arguments" : [ ],
          "label" : "cmo-index",
          "class" : "CommandLineTool"
        },
        "in" : [ {
          "id" : "bam",
          "source" : "normal_bam"
        } ],
        "out" : [ {
          "id" : "bam_indexed"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "tumor_index",
        "run" : {
          "cwlVersion" : "v1.0",
          "inputs" : [ {
            "id" : "bam",
            "type" : "File",
            "inputBinding" : {
              "prefix" : "--bam"
            }
          } ],
          "outputs" : [ {
            "id" : "bam_indexed",
            "type" : "File",
            "outputBinding" : {
              "glob" : "$(inputs.bam.basename)"
            },
            "secondaryFiles" : [ "^.bai", ".bai" ]
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "ResourceRequirement",
            "ramMin" : 16000,
            "coresMin" : 1
          }, {
            "class" : "DockerRequirement",
            "dockerPull" : "mskcc/roslin-variant-cmo-utils:1.9.15"
          }, {
            "class" : "InitialWorkDirRequirement",
            "listing" : [ "$(inputs.bam)" ]
          } ],
          "successCodes" : [ ],
          "baseCommand" : [ "cmo_index" ],
          "arguments" : [ ],
          "label" : "cmo-index",
          "class" : "CommandLineTool"
        },
        "in" : [ {
          "id" : "bam",
          "source" : "tumor_bam"
        } ],
        "out" : [ {
          "id" : "bam_indexed"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "call_variants",
        "run" : {
          "inputs" : [ {
            "id" : "tumor_bam",
            "type" : "File"
          }, {
            "id" : "genome",
            "type" : "string"
          }, {
            "id" : "normal_bam",
            "type" : "File"
          }, {
            "id" : "ref_fasta",
            "type" : "File"
          }, {
            "id" : "normal_sample_name",
            "type" : "string"
          }, {
            "id" : "tumor_sample_name",
            "type" : "string"
          }, {
            "id" : "dbsnp",
            "type" : "File"
          }, {
            "id" : "cosmic",
            "type" : "File"
          }, {
            "id" : "mutect_dcov",
            "type" : "int"
          }, {
            "id" : "mutect_rf",
            "type" : "string[]"
          }, {
            "id" : "bed",
            "type" : "File"
          }, {
            "id" : "refseq",
            "type" : "File"
          }, {
            "id" : "facets_pcval",
            "type" : "int"
          }, {
            "id" : "facets_cval",
            "type" : "int"
          }, {
            "id" : "facets_snps",
            "type" : "File"
          } ],
          "outputs" : [ {
            "id" : "mutect_vcf",
            "type" : "File",
            "outputSource" : "mutect/output"
          }, {
            "id" : "mutect_callstats",
            "type" : "File",
            "outputSource" : "mutect/callstats_output"
          }, {
            "id" : "vardict_vcf",
            "type" : "File",
            "outputSource" : "vardict/output"
          }, {
            "id" : "facets_png",
            "type" : "File[]",
            "outputSource" : "facets/facets_png_output"
          }, {
            "id" : "facets_txt_hisens",
            "type" : "File",
            "outputSource" : "facets/facets_txt_output_hisens"
          }, {
            "id" : "facets_txt_purity",
            "type" : "File",
            "outputSource" : "facets/facets_txt_output_purity"
          }, {
            "id" : "facets_out",
            "type" : "File[]",
            "outputSource" : "facets/facets_out_output"
          }, {
            "id" : "facets_rdata",
            "type" : "File[]",
            "outputSource" : "facets/facets_rdata_output"
          }, {
            "id" : "facets_seg",
            "type" : "File[]",
            "outputSource" : "facets/facets_seg_output"
          }, {
            "id" : "facets_counts",
            "type" : "File",
            "outputSource" : "facets/facets_counts_output"
          } ],
          "hints" : [ ],
          "requirements" : [ ],
          "successCodes" : [ ],
          "steps" : [ {
            "id" : "facets",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "normal_bam",
                "type" : "File"
              }, {
                "id" : "tumor_bam",
                "type" : "File"
              }, {
                "id" : "tumor_sample_name",
                "type" : "string"
              }, {
                "id" : "genome",
                "type" : "string"
              }, {
                "id" : "facets_pcval",
                "type" : "int"
              }, {
                "id" : "facets_cval",
                "type" : "int"
              }, {
                "id" : "facets_snps",
                "type" : "File"
              } ],
              "outputs" : [ {
                "id" : "facets_png_output",
                "type" : "File[]",
                "outputSource" : "facets/png_files"
              }, {
                "id" : "facets_txt_output_purity",
                "type" : "File",
                "outputSource" : "facets/txt_files_purity"
              }, {
                "id" : "facets_txt_output_hisens",
                "type" : "File",
                "outputSource" : "facets/txt_files_hisens"
              }, {
                "id" : "facets_out_output",
                "type" : "File[]",
                "outputSource" : "facets/out_files"
              }, {
                "id" : "facets_rdata_output",
                "type" : "File[]",
                "outputSource" : "facets/rdata_files"
              }, {
                "id" : "facets_seg_output",
                "type" : "File[]",
                "outputSource" : "facets/seg_files"
              }, {
                "id" : "facets_counts_output",
                "type" : "File",
                "outputSource" : "snp_pileup/out_file"
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "MultipleInputFeatureRequirement"
              }, {
                "class" : "ScatterFeatureRequirement"
              }, {
                "class" : "SubworkflowFeatureRequirement"
              }, {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "StepInputExpressionRequirement"
              } ],
              "successCodes" : [ ],
              "steps" : [ {
                "id" : "snp_pileup",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "count_orphans",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--count-orphans"
                    },
                    "doc" : "Do not discard anomalous read pairs."
                  }, {
                    "id" : "max_depth",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--max-depth"
                    },
                    "doc" : "Sets the maximum depth. Default is 4000."
                  }, {
                    "id" : "gzip",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--gzip"
                    },
                    "doc" : "Compresses the output file with BGZF."
                  }, {
                    "id" : "progress",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--progress"
                    },
                    "doc" : "Show a progress bar. WARNING - requires additionaltime to calculate number of SNPs, and will takelonger than normal."
                  }, {
                    "id" : "pseudo_snps",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--pseudo-snps"
                    },
                    "doc" : "Every MULTIPLE positions, if there is no SNP,insert a blank record with the total count at theposition."
                  }, {
                    "id" : "min_map_quality",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--min-map-quality"
                    },
                    "doc" : "Sets the minimum threshold for mappingquality. Default is 0."
                  }, {
                    "id" : "min_base_quality",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--min-base-quality"
                    },
                    "doc" : "Sets the minimum threshold for base quality.Default is 0."
                  }, {
                    "id" : "min_read_counts",
                    "default" : "10,0",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--min-read-counts"
                    },
                    "doc" : "Comma separated list of minimum read counts fora position to be output. Default is 0."
                  }, {
                    "id" : "verbose",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--verbose"
                    },
                    "doc" : "Show detailed messages."
                  }, {
                    "id" : "ignore_overlaps",
                    "default" : false,
                    "type" : [ "null", "boolean" ],
                    "inputBinding" : {
                      "prefix" : "--ignore-overlaps"
                    },
                    "doc" : "Disable read-pair overlap detection."
                  }, {
                    "id" : "vcf",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 1
                    },
                    "doc" : "vcf file"
                  }, {
                    "id" : "output_file",
                    "type" : "string",
                    "inputBinding" : {
                      "position" : 2
                    },
                    "doc" : "output file"
                  }, {
                    "id" : "normal_bam",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 3
                    },
                    "doc" : "normal bam"
                  }, {
                    "id" : "tumor_bam",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 4
                    },
                    "doc" : "tumor bam"
                  }, {
                    "id" : "stderr",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--stderr"
                    },
                    "doc" : "log stderr to file"
                  }, {
                    "id" : "stdout",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--stdout"
                    },
                    "doc" : "log stdout to file"
                  } ],
                  "outputs" : [ {
                    "id" : "out_file",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${\n  if (inputs.output_file)\n    return inputs.output_file;\n  return null;\n}\n"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 8000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-htstools:0.1.1"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "/usr/bin/snp-pileup" ],
                  "arguments" : [ ],
                  "doc" : "run snp-pileup\n",
                  "id" : "htstools-snp-pileup",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "vcf",
                  "source" : "facets_snps"
                }, {
                  "id" : "output_file",
                  "valueFrom" : "${ return inputs.normal_bam.basename.replace(\".bam\", \"\") + \"__\" + inputs.tumor_bam.basename.replace(\".bam\", \"\") + \".dat.gz\"; }"
                }, {
                  "id" : "normal_bam",
                  "source" : "normal_bam"
                }, {
                  "id" : "tumor_bam",
                  "source" : "tumor_bam"
                }, {
                  "id" : "count_orphans",
                  "valueFrom" : "${ return true; }"
                }, {
                  "id" : "gzip",
                  "valueFrom" : "${ return true; }"
                }, {
                  "default" : "50",
                  "id" : "pseudo_snps"
                } ],
                "out" : [ {
                  "id" : "out_file"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "facets",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "cval",
                    "default" : 100,
                    "type" : [ "null", "int" ],
                    "inputBinding" : {
                      "prefix" : "--cval"
                    },
                    "doc" : "critical value for segmentation"
                  }, {
                    "id" : "snp_nbhd",
                    "default" : 250,
                    "type" : [ "null", "int" ],
                    "inputBinding" : {
                      "prefix" : "--snp_nbhd"
                    },
                    "doc" : "window size"
                  }, {
                    "id" : "ndepth",
                    "default" : 35,
                    "type" : [ "null", "int" ],
                    "inputBinding" : {
                      "prefix" : "--ndepth"
                    },
                    "doc" : "threshold for depth in the normal sample"
                  }, {
                    "id" : "min_nhet",
                    "default" : 25,
                    "type" : [ "null", "int" ],
                    "inputBinding" : {
                      "prefix" : "--min_nhet"
                    },
                    "doc" : "minimum number of heterozygote snps in a segment used for bivariate t-statistic during clustering of segments"
                  }, {
                    "id" : "purity_cval",
                    "default" : 500,
                    "type" : [ "null", "int" ],
                    "inputBinding" : {
                      "prefix" : "--purity_cval"
                    },
                    "doc" : "critical value for segmentation"
                  }, {
                    "id" : "purity_snp_nbhd",
                    "default" : 250,
                    "type" : [ "null", "int" ],
                    "inputBinding" : {
                      "prefix" : "--purity_snp_nbhd"
                    },
                    "doc" : "window size"
                  }, {
                    "id" : "purity_ndepth",
                    "default" : 35,
                    "type" : [ "null", "int" ],
                    "inputBinding" : {
                      "prefix" : "--purity_ndepth"
                    },
                    "doc" : "threshold for depth in the normal sample"
                  }, {
                    "id" : "purity_min_nhet",
                    "default" : 25,
                    "type" : [ "null", "int" ],
                    "inputBinding" : {
                      "prefix" : "--purity_min_nhet"
                    },
                    "doc" : "minimum number of heterozygote snps in a segment used for bivariate t-statistic during clustering of segments"
                  }, {
                    "id" : "dipLogR",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--dipLogR"
                    },
                    "doc" : "diploid log ratio"
                  }, {
                    "id" : "genome",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--genome"
                    },
                    "doc" : "Genome of counts file"
                  }, {
                    "id" : "counts_file",
                    "type" : "File",
                    "inputBinding" : {
                      "prefix" : "--counts_file"
                    },
                    "doc" : "paired Counts File"
                  }, {
                    "id" : "TAG",
                    "type" : "string",
                    "inputBinding" : {
                      "prefix" : "--TAG"
                    },
                    "doc" : "output prefix"
                  }, {
                    "id" : "directory",
                    "type" : "string",
                    "inputBinding" : {
                      "prefix" : "--directory"
                    },
                    "doc" : "output prefix"
                  }, {
                    "id" : "R_lib",
                    "default" : "latest",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--R_lib"
                    },
                    "doc" : "Which version of FACETs to load into R"
                  }, {
                    "id" : "single_chrom",
                    "default" : "F",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--single_chrom"
                    },
                    "doc" : "Perform analysis on single chromosome"
                  }, {
                    "id" : "ggplot2",
                    "default" : "T",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--ggplot2"
                    },
                    "doc" : "Plots using ggplot2"
                  }, {
                    "id" : "seed",
                    "default" : 1000,
                    "type" : [ "null", "int" ],
                    "inputBinding" : {
                      "prefix" : "--seed"
                    },
                    "doc" : "Set the seed for reproducibility"
                  }, {
                    "id" : "tumor_id",
                    "type" : [ "null", "string" ],
                    "inputBinding" : {
                      "prefix" : "--tumor_id"
                    },
                    "doc" : "Set the value for tumor id"
                  } ],
                  "outputs" : [ {
                    "id" : "png_files",
                    "type" : "File[]",
                    "outputBinding" : {
                      "glob" : "*.png"
                    }
                  }, {
                    "id" : "txt_files_purity",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "*_purity.cncf.txt"
                    }
                  }, {
                    "id" : "txt_files_hisens",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "*_hisens.cncf.txt"
                    }
                  }, {
                    "id" : "out_files",
                    "type" : "File[]",
                    "outputBinding" : {
                      "glob" : "*.out"
                    }
                  }, {
                    "id" : "rdata_files",
                    "type" : "File[]",
                    "outputBinding" : {
                      "glob" : "*.Rdata"
                    }
                  }, {
                    "id" : "seg_files",
                    "type" : "File[]",
                    "outputBinding" : {
                      "glob" : "*.seg"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 8000,
                    "coresMin" : 1
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-facets:1.6.3"
                  } ],
                  "successCodes" : [ ],
                  "baseCommand" : [ "python", "/usr/bin/facets-suite/facets", "doFacets" ],
                  "arguments" : [ ],
                  "doc" : "Run FACETS on tumor-normal SNP read counts generated using cmo_snp-pileup\n",
                  "id" : "facets-doFacets",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "default" : "hg19",
                  "id" : "genome"
                }, {
                  "id" : "counts_file",
                  "source" : "snp_pileup/out_file"
                }, {
                  "id" : "TAG",
                  "valueFrom" : "${ return inputs.counts_file.basename.replace(\".dat.gz\", \"\"); }"
                }, {
                  "default" : ".",
                  "id" : "directory"
                }, {
                  "id" : "purity_cval",
                  "source" : "facets_pcval"
                }, {
                  "id" : "cval",
                  "source" : "facets_cval"
                }, {
                  "id" : "tumor_id",
                  "source" : "tumor_sample_name"
                } ],
                "out" : [ {
                  "id" : "png_files"
                }, {
                  "id" : "txt_files_purity"
                }, {
                  "id" : "txt_files_hisens"
                }, {
                  "id" : "out_files"
                }, {
                  "id" : "rdata_files"
                }, {
                  "id" : "seg_files"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              } ],
              "id" : "facets",
              "class" : "Workflow"
            },
            "in" : [ {
              "id" : "normal_bam",
              "source" : "normal_bam"
            }, {
              "id" : "tumor_bam",
              "source" : "tumor_bam"
            }, {
              "id" : "tumor_sample_name",
              "source" : "tumor_sample_name"
            }, {
              "id" : "genome",
              "source" : "genome"
            }, {
              "id" : "facets_pcval",
              "source" : "facets_pcval"
            }, {
              "id" : "facets_cval",
              "source" : "facets_cval"
            }, {
              "id" : "facets_snps",
              "source" : "facets_snps"
            } ],
            "out" : [ {
              "id" : "facets_png_output"
            }, {
              "id" : "facets_txt_output_hisens"
            }, {
              "id" : "facets_txt_output_purity"
            }, {
              "id" : "facets_out_output"
            }, {
              "id" : "facets_rdata_output"
            }, {
              "id" : "facets_seg_output"
            }, {
              "id" : "facets_counts_output"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "vardict",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "bedfile",
                "type" : "File?"
              }, {
                "id" : "b2",
                "type" : "File?",
                "secondaryFiles" : [ ".bai" ]
              }, {
                "id" : "b",
                "type" : "File?",
                "secondaryFiles" : [ ".bai" ]
              }, {
                "id" : "C",
                "type" : "boolean?"
              }, {
                "id" : "D",
                "type" : "boolean?"
              }, {
                "id" : "N",
                "type" : "string?"
              }, {
                "id" : "N2",
                "type" : "string?"
              }, {
                "id" : "x",
                "type" : "string?"
              }, {
                "id" : "z",
                "type" : "string?"
              }, {
                "id" : "th",
                "type" : "string?"
              }, {
                "id" : "M",
                "type" : "string?"
              }, {
                "id" : "I",
                "type" : "string?"
              }, {
                "id" : "H",
                "type" : "boolean?"
              }, {
                "id" : "F",
                "type" : "string?"
              }, {
                "id" : "E",
                "type" : "string?"
              }, {
                "id" : "T",
                "type" : "string?"
              }, {
                "id" : "m",
                "type" : "string?"
              }, {
                "id" : "k",
                "type" : "string?"
              }, {
                "id" : "i",
                "type" : "boolean?"
              }, {
                "id" : "hh",
                "type" : "boolean?"
              }, {
                "id" : "g",
                "type" : "string?"
              }, {
                "id" : "f",
                "type" : "string?"
              }, {
                "id" : "e",
                "type" : "string?"
              }, {
                "id" : "d",
                "type" : "string?"
              }, {
                "id" : "c",
                "type" : "string?"
              }, {
                "id" : "a",
                "type" : "string?"
              }, {
                "id" : "O",
                "type" : "string?"
              }, {
                "id" : "P",
                "type" : "string?"
              }, {
                "id" : "Q",
                "type" : "string?"
              }, {
                "id" : "R",
                "type" : "string?"
              }, {
                "id" : "V",
                "type" : "string?"
              }, {
                "id" : "VS",
                "type" : "string?"
              }, {
                "id" : "X",
                "type" : "string?"
              }, {
                "id" : "Z",
                "type" : "string?"
              }, {
                "id" : "B",
                "type" : "int?"
              }, {
                "id" : "S",
                "type" : "string?"
              }, {
                "id" : "n",
                "type" : "string?"
              }, {
                "id" : "o",
                "type" : "string?"
              }, {
                "id" : "p",
                "type" : "boolean?"
              }, {
                "id" : "q",
                "type" : "string?"
              }, {
                "id" : "r",
                "type" : "string?"
              }, {
                "id" : "t",
                "type" : "boolean?"
              }, {
                "id" : "vcf",
                "type" : "string?"
              }, {
                "id" : "G",
                "type" : "File",
                "secondaryFiles" : [ ".fai" ]
              }, {
                "id" : "f_1",
                "type" : "string?"
              } ],
              "outputs" : [ {
                "id" : "output",
                "type" : "File",
                "outputSource" : "vardict_1/output"
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "MultipleInputFeatureRequirement"
              }, {
                "class" : "ScatterFeatureRequirement"
              }, {
                "class" : "SubworkflowFeatureRequirement"
              }, {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "StepInputExpressionRequirement"
              } ],
              "successCodes" : [ ],
              "steps" : [ {
                "id" : "vardict",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "B",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-B"
                    },
                    "doc" : "The minimum"
                  }, {
                    "id" : "C",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-C"
                    },
                    "doc" : "Indicate the chromosome names are just numbers, such as 1, 2, not chr1, chr2"
                  }, {
                    "id" : "D",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-D"
                    },
                    "doc" : "Debug mode. Will print some error messages and append full genotype at the end."
                  }, {
                    "id" : "E",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-E"
                    },
                    "doc" : "The column for region end, e.g. gene end"
                  }, {
                    "id" : "F",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-F"
                    },
                    "doc" : "The hexical to filter reads using samtools. Default - 0x500 (filter 2nd alignments and duplicates). Use -F 0 to turn it off."
                  }, {
                    "id" : "G",
                    "type" : "File",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-G"
                    },
                    "secondaryFiles" : [ ".fai" ]
                  }, {
                    "id" : "H",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-H"
                    },
                    "doc" : "Print this help page"
                  }, {
                    "id" : "I",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-I"
                    },
                    "doc" : "The indel size. Default - 120bp"
                  }, {
                    "id" : "M",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-M"
                    },
                    "doc" : "The minimum matches for a read to be considered. If, after soft-clipping, the matched bp is less than INT, then the read is discarded. It's meant for PCR based targeted sequencing where there's no insert and the matching is only the primers. Default - 0, or no filtering"
                  }, {
                    "id" : "N",
                    "type" : "string?",
                    "doc" : "Tumor Sample Name"
                  }, {
                    "id" : "N2",
                    "type" : "string?",
                    "doc" : "Normal Sample Name"
                  }, {
                    "id" : "O",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-O"
                    },
                    "doc" : "The reads should have at least mean MapQ to be considered a valid variant. Default - no filtering"
                  }, {
                    "id" : "P",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-P"
                    },
                    "doc" : "The read position filter. If the mean variants position is less that specified, it's considered false positive. Default - 5"
                  }, {
                    "id" : "Q",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-Q"
                    },
                    "doc" : "If set, reads with mapping quality less than INT will be filtered and ignored"
                  }, {
                    "id" : "R",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-R"
                    },
                    "doc" : "The region of interest. In the format of chr -start-end. If end is omitted, then a single position. No BED is needed."
                  }, {
                    "id" : "S",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-S"
                    },
                    "doc" : "The column for region start, e.g. gene start"
                  }, {
                    "id" : "T",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-T"
                    },
                    "doc" : "Trim bases after [INT] bases in the reads"
                  }, {
                    "id" : "V",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-V"
                    },
                    "doc" : "The lowest frequency in normal sample allowed for a putative somatic mutations. Default to 0.05"
                  }, {
                    "id" : "VS",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-VS"
                    },
                    "doc" : "How strict to be when reading a SAM or BAM. STRICT - throw an exception if something looks wrong. LENIENT - Emit warnings but keep going if possible. SILENT - Like LENIENT, only don't emit warning messages. Default - LENIENT"
                  }, {
                    "id" : "X",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-X"
                    },
                    "doc" : "Extension of bp to look for mismatches after insersion or deletion. Default to 3 bp, or only calls when they're within 3 bp."
                  }, {
                    "id" : "Z",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-Z"
                    },
                    "doc" : "For downsampling fraction. e.g. 0.7 means roughly 70%% downsampling. Default - No downsampling. Use with caution. The downsampling will be random and non-reproducible."
                  }, {
                    "id" : "a",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-a"
                    },
                    "doc" : "Indicate it's amplicon based calling. Reads don't map to the amplicon will be skipped. A read pair is considered belonging the amplicon if the edges are less than int bp to the amplicon, and overlap fraction is at least float. Default - 10 -0.95"
                  }, {
                    "id" : "b",
                    "type" : "File",
                    "secondaryFiles" : [ ".bai" ],
                    "doc" : "Tumor bam"
                  }, {
                    "id" : "b2",
                    "type" : "File",
                    "secondaryFiles" : [ ".bai" ],
                    "doc" : "Normal bam"
                  }, {
                    "id" : "bedfile",
                    "type" : "File?",
                    "inputBinding" : {
                      "position" : 1
                    }
                  }, {
                    "id" : "c",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-c"
                    },
                    "doc" : "The column for chromosome"
                  }, {
                    "id" : "d",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-d"
                    },
                    "doc" : "The delimiter for split region_info, default to tab \"\\t\""
                  }, {
                    "id" : "e",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-e"
                    },
                    "doc" : "The column for segment ends in the region, e.g. exon ends"
                  }, {
                    "id" : "f",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-f"
                    },
                    "doc" : "The threshold for allele frequency, default - 0.05 or 5%%"
                  }, {
                    "id" : "g",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-g"
                    },
                    "doc" : "The column for gene name, or segment annotation"
                  }, {
                    "id" : "h",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-hh"
                    },
                    "doc" : "Print a header row decribing columns"
                  }, {
                    "id" : "i",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-i"
                    },
                    "doc" : "Output splicing read counts"
                  }, {
                    "id" : "k",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-k"
                    },
                    "doc" : "Indicate whether to perform local realignment. Default - 1. Set to 0 to disable it. For Ion or PacBio, 0 is recommended."
                  }, {
                    "id" : "m",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-m"
                    },
                    "doc" : "If set, reads with mismatches more than INT will be filtered and ignored. Gaps are not counted as mismatches. Valid only for bowtie2/TopHat or BWA aln followed by sampe. BWA mem is calculated as NM - Indels. Default - 8, or reads with more than 8 mismatches will not be used."
                  }, {
                    "id" : "n",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-n"
                    },
                    "doc" : "The regular expression to extract sample name from bam filenames. Default to - /([^\\/\\._]+?)_[^\\/]*.bam/"
                  }, {
                    "id" : "o",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-o"
                    },
                    "doc" : "The Qratio of (good_quality_reads)/(bad_quality_reads+0.5). The quality is defined by -q option. Default - 1.5"
                  }, {
                    "id" : "p",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-p"
                    },
                    "doc" : "Do pileup regarless the frequency"
                  }, {
                    "id" : "q",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-q"
                    },
                    "doc" : "The phred score for a base to be considered a good call. Default - 25 (for Illumina) For PGM, set it to ~15, as PGM tends to under estimate base quality."
                  }, {
                    "id" : "r",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-r"
                    },
                    "doc" : "The minimum"
                  }, {
                    "id" : "s",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-s"
                    },
                    "doc" : "The column for segment starts in the region, e.g. exon starts"
                  }, {
                    "id" : "t",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-t"
                    },
                    "doc" : "Indicate to remove duplicated reads. Only one pair with same start positions will be kept"
                  }, {
                    "id" : "th",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-th"
                    },
                    "doc" : "Threads count."
                  }, {
                    "id" : "three",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-3"
                    },
                    "doc" : "Indicate to move indels to 3-prime if alternative alignment can be achieved."
                  }, {
                    "id" : "x",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-x"
                    },
                    "doc" : "The number of nucleotide to extend for each segment, default - 0 -y"
                  }, {
                    "id" : "z",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-z"
                    },
                    "doc" : "Indicate wehther is zero-based cooridates, as IGV does. Default - 1 for BED file or amplicon BED file. Use 0 to turn it off. When use -R option, it's set to 0AUTHOR. Written by Zhongwu Lai, AstraZeneca, Boston, USAREPORTING BUGS. Report bugs to zhongwu@yahoo.comCOPYRIGHT. This is free software - you are free to change and redistribute it. There is NO WARRANTY, to the extent permitted by law."
                  } ],
                  "outputs" : [ {
                    "id" : "output",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "vardict_app_output.vcf"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 24000,
                    "coresMin" : 4
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-vardict:1.5.1"
                  } ],
                  "successCodes" : [ ],
                  "stdout" : "vardict_app_output.vcf",
                  "baseCommand" : [ "/usr/bin/vardict/bin/VarDict" ],
                  "arguments" : [ {
                    "position" : 1,
                    "prefix" : "-b",
                    "valueFrom" : "${\n    return inputs.b.path + \"|\" + inputs.b2.path;\n}"
                  }, {
                    "position" : 0,
                    "prefix" : "-N",
                    "valueFrom" : "${\n    if (inputs.N2)\n        return [inputs.N, inputs.N2];\n    else\n        return inputs.N;\n}"
                  } ],
                  "id" : "vardict",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "B",
                  "source" : "B"
                }, {
                  "id" : "C",
                  "source" : "C"
                }, {
                  "id" : "D",
                  "source" : "D"
                }, {
                  "id" : "E",
                  "source" : "E"
                }, {
                  "id" : "F",
                  "source" : "F"
                }, {
                  "id" : "G",
                  "source" : "G"
                }, {
                  "id" : "H",
                  "source" : "H"
                }, {
                  "id" : "I",
                  "source" : "I"
                }, {
                  "id" : "M",
                  "source" : "M"
                }, {
                  "id" : "N",
                  "source" : "N"
                }, {
                  "id" : "O",
                  "source" : "O"
                }, {
                  "id" : "P",
                  "source" : "P"
                }, {
                  "id" : "Q",
                  "source" : "Q"
                }, {
                  "id" : "R",
                  "source" : "R"
                }, {
                  "id" : "S",
                  "source" : "S"
                }, {
                  "id" : "T",
                  "source" : "T"
                }, {
                  "id" : "V",
                  "source" : "V"
                }, {
                  "id" : "VS",
                  "source" : "VS"
                }, {
                  "id" : "X",
                  "source" : "X"
                }, {
                  "id" : "Z",
                  "source" : "Z"
                }, {
                  "id" : "a",
                  "source" : "a"
                }, {
                  "id" : "b",
                  "source" : "b"
                }, {
                  "id" : "b2",
                  "source" : "b2"
                }, {
                  "id" : "bedfile",
                  "source" : "bedfile"
                }, {
                  "id" : "c",
                  "source" : "c"
                }, {
                  "id" : "d",
                  "source" : "d"
                }, {
                  "id" : "e",
                  "source" : "e"
                }, {
                  "id" : "f",
                  "source" : "f"
                }, {
                  "id" : "g",
                  "source" : "g"
                }, {
                  "id" : "h",
                  "source" : "hh"
                }, {
                  "id" : "i",
                  "source" : "i"
                }, {
                  "id" : "k",
                  "source" : "k"
                }, {
                  "id" : "m",
                  "source" : "m"
                }, {
                  "id" : "n",
                  "source" : "n"
                }, {
                  "id" : "o",
                  "source" : "o"
                }, {
                  "id" : "p",
                  "source" : "p"
                }, {
                  "id" : "q",
                  "source" : "q"
                }, {
                  "id" : "r",
                  "source" : "r"
                }, {
                  "id" : "t",
                  "source" : "t"
                }, {
                  "id" : "th",
                  "source" : "th"
                }, {
                  "id" : "vcf",
                  "source" : "vcf"
                }, {
                  "id" : "v",
                  "valueFrom" : "${ return inputs.vcf.replace(\".vcf\", \"_tmp.vcf\") }"
                }, {
                  "id" : "x",
                  "source" : "x"
                }, {
                  "id" : "z",
                  "source" : "z"
                } ],
                "out" : [ {
                  "id" : "output"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "testsomatic",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "input_vardict",
                    "type" : "File"
                  } ],
                  "outputs" : [ {
                    "id" : "output_var",
                    "type" : "File?",
                    "outputBinding" : {
                      "glob" : "output_testsomatic.var"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 12000,
                    "coresMin" : 2
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-vardict:1.5.1"
                  } ],
                  "successCodes" : [ ],
                  "stdin" : "$(inputs.input_vardict.path)",
                  "stdout" : "output_testsomatic.var",
                  "baseCommand" : [ "Rscript", "/usr/bin/vardict/testsomatic.R" ],
                  "arguments" : [ ],
                  "id" : "testsomatic",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "input_vardict",
                  "source" : "vardict/output"
                } ],
                "out" : [ {
                  "id" : "output_var"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              }, {
                "id" : "vardict_1",
                "run" : {
                  "cwlVersion" : "v1.0",
                  "inputs" : [ {
                    "id" : "C",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-C"
                    },
                    "doc" : "Indicate the chromosome names are just numbers, such as 1, 2, not chr1, chr2"
                  }, {
                    "id" : "D",
                    "type" : "float?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-D"
                    },
                    "doc" : "Debug mode. Will print some error messages and append full genotype at the end."
                  }, {
                    "id" : "F",
                    "type" : "float?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-F"
                    },
                    "doc" : "The hexical to filter reads using samtools. Default - 0x500 (filter 2nd alignments and duplicates). Use -F 0 to turn it off."
                  }, {
                    "id" : "I",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-I"
                    },
                    "doc" : "The indel size. Default - 120bp"
                  }, {
                    "id" : "M",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-M"
                    },
                    "doc" : "The minimum matches for a read to be considered. If, after soft-clipping, the matched bp is less than INT, then the read is discarded. It's meant for PCR based targeted sequencing where there's no insert and the matching is only the primers. Default - 0, or no filtering"
                  }, {
                    "id" : "N",
                    "type" : "string?",
                    "doc" : "Tumor Sample Name"
                  }, {
                    "id" : "N2",
                    "type" : "string?",
                    "doc" : "Normal Sample Name"
                  }, {
                    "id" : "P",
                    "type" : "float?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-P"
                    },
                    "doc" : "The read position filter. If the mean variants position is less that specified, it's considered false positive. Default - 5"
                  }, {
                    "id" : "Q",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-Q"
                    },
                    "doc" : "If set, reads with mapping quality less than INT will be filtered and ignored"
                  }, {
                    "id" : "S",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-S"
                    },
                    "doc" : "The column for region start, e.g. gene start"
                  }, {
                    "id" : "f",
                    "type" : "string?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-f"
                    },
                    "doc" : "The threshold for allele frequency, default - 0.05 or 5%%"
                  }, {
                    "id" : "m",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-m"
                    },
                    "doc" : "If set, reads with mismatches more than INT will be filtered and ignored. Gaps are not counted as mismatches. Valid only for bowtie2/TopHat or BWA aln followed by sampe. BWA mem is calculated as NM - Indels. Default - 8, or reads with more than 8 mismatches will not be used."
                  }, {
                    "id" : "o",
                    "type" : "float?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-o"
                    },
                    "doc" : "The Qratio of (good_quality_reads)/(bad_quality_reads+0.5). The quality is defined by -q option. Default - 1.5"
                  }, {
                    "id" : "p",
                    "type" : "float?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-p"
                    },
                    "doc" : "Do pileup regarless the frequency"
                  }, {
                    "id" : "vcf",
                    "type" : "string",
                    "doc" : "output vcf file"
                  }, {
                    "id" : "A",
                    "type" : "boolean?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-A"
                    }
                  }, {
                    "id" : "c",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-c"
                    }
                  }, {
                    "id" : "q",
                    "type" : "float?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-q"
                    }
                  }, {
                    "id" : "d",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-d"
                    }
                  }, {
                    "id" : "v",
                    "type" : "int?",
                    "inputBinding" : {
                      "position" : 0,
                      "prefix" : "-v"
                    }
                  }, {
                    "id" : "input_vcf",
                    "type" : "File?"
                  } ],
                  "outputs" : [ {
                    "id" : "output",
                    "type" : "File",
                    "outputBinding" : {
                      "glob" : "${ return inputs.vcf; }"
                    }
                  } ],
                  "hints" : [ ],
                  "requirements" : [ {
                    "class" : "InlineJavascriptRequirement"
                  }, {
                    "class" : "ResourceRequirement",
                    "ramMin" : 32000,
                    "coresMin" : 4
                  }, {
                    "class" : "DockerRequirement",
                    "dockerPull" : "mskcc/roslin-variant-vardict:1.5.1"
                  } ],
                  "successCodes" : [ ],
                  "stdin" : "$(inputs.input_vcf.path)",
                  "stdout" : "${ return inputs.vcf; }",
                  "baseCommand" : [ "perl", "/usr/bin/vardict/var2vcf_paired.pl" ],
                  "arguments" : [ {
                    "position" : 0,
                    "prefix" : "-N",
                    "valueFrom" : "${\n    return inputs.N + \"|\" + inputs.N2;\n}"
                  } ],
                  "id" : "vardict_var2vcf",
                  "class" : "CommandLineTool"
                },
                "in" : [ {
                  "id" : "N",
                  "source" : "N"
                }, {
                  "id" : "N2",
                  "source" : "N2"
                }, {
                  "id" : "f",
                  "source" : "f_1"
                }, {
                  "id" : "vcf",
                  "source" : "vcf"
                }, {
                  "id" : "input_vcf",
                  "source" : "testsomatic/output_var"
                } ],
                "out" : [ {
                  "id" : "output"
                } ],
                "hints" : [ ],
                "requirements" : [ ]
              } ],
              "id" : "vardict",
              "label" : "vardict",
              "class" : "Workflow"
            },
            "in" : [ {
              "id" : "G",
              "source" : "ref_fasta"
            }, {
              "id" : "b",
              "source" : "tumor_bam"
            }, {
              "id" : "b2",
              "source" : "normal_bam"
            }, {
              "id" : "N",
              "source" : "tumor_sample_name"
            }, {
              "id" : "N2",
              "source" : "normal_sample_name"
            }, {
              "id" : "bedfile",
              "source" : "bed"
            }, {
              "default" : true,
              "id" : "C"
            }, {
              "default" : false,
              "id" : "D"
            }, {
              "default" : "2000",
              "id" : "x"
            }, {
              "default" : false,
              "id" : "H"
            }, {
              "default" : "4",
              "id" : "th"
            }, {
              "default" : "3",
              "id" : "E"
            }, {
              "default" : false,
              "id" : "i"
            }, {
              "default" : false,
              "id" : "hh"
            }, {
              "default" : "0.01",
              "id" : "f"
            }, {
              "default" : "1",
              "id" : "c"
            }, {
              "default" : "20",
              "id" : "Q"
            }, {
              "default" : "5",
              "id" : "X"
            }, {
              "default" : "1",
              "id" : "z"
            }, {
              "default" : "2",
              "id" : "S"
            }, {
              "default" : false,
              "id" : "p"
            }, {
              "default" : "20",
              "id" : "q"
            }, {
              "default" : false,
              "id" : "t"
            }, {
              "id" : "vcf",
              "valueFrom" : "${ return inputs.b.basename.replace(\".bam\", \".\") + inputs.b2.basename.replace(\".bam\", \".vardict.vcf\") }"
            } ],
            "out" : [ {
              "id" : "output"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "mutect",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "analysis_type",
                "default" : "MuTect",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "-T"
                }
              }, {
                "id" : "arg_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--arg_file"
                },
                "doc" : "Reads arguments from the specified file"
              }, {
                "id" : "input_file_normal",
                "type" : [ "null", "File" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--input_file:normal"
                },
                "secondaryFiles" : [ ".bai" ],
                "doc" : "SAM or BAM file(s)"
              }, {
                "id" : "input_file_tumor",
                "type" : [ "null", "File" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--input_file:tumor"
                },
                "secondaryFiles" : [ ".bai" ],
                "doc" : "SAM or BAM file(s)"
              }, {
                "id" : "read_buffer_size",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--read_buffer_size"
                },
                "doc" : "Number of reads per SAM file to buffer in memory"
              }, {
                "id" : "phone_home",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--phone_home"
                },
                "doc" : "What kind of GATK run report should we generate? STANDARD is the default, can be NO_ET so nothing is posted to the run repository. Please see -phone-home-and-how-does-it-affect-me#latest for details. (NO_ET|STANDARD|STDOUT)"
              }, {
                "id" : "gatk_key",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--gatk_key"
                },
                "doc" : "GATK Key file. Required if running with -et NO_ET. Please see -phone-home-and-how-does-it-affect-me#latest for details."
              }, {
                "id" : "tag",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--tag"
                },
                "doc" : "Arbitrary tag string to identify this GATK run as part of a group of runs, for later analysis"
              }, {
                "id" : "read_filter",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--read_filter"
                },
                "doc" : "Specify filtration criteria to apply to each read individually"
              }, {
                "id" : "intervals",
                "type" : [ "null", "string", "File" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--intervals"
                },
                "doc" : "One or more genomic intervals over which to operate. Can be explicitly specified on the command line or in a file (including a rod file)"
              }, {
                "id" : "excludeIntervals",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--excludeIntervals"
                },
                "doc" : "One or more genomic intervals to exclude from processing. Can be explicitly specified on the command line or in a file (including a rod file)"
              }, {
                "id" : "interval_set_rule",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--interval_set_rule"
                },
                "doc" : "Indicates the set merging approach the interval parser should use to combine the various -L or -XL inputs (UNION| INTERSECTION)"
              }, {
                "id" : "interval_merging",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--interval_merging"
                },
                "doc" : "Indicates the interval merging rule we should use for abutting intervals (ALL| OVERLAPPING_ONLY)"
              }, {
                "id" : "interval_padding",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--interval_padding"
                },
                "doc" : "Indicates how many basepairs of padding to include around each of the intervals specified with the -L/"
              }, {
                "id" : "reference_sequence",
                "type" : "File",
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--reference_sequence"
                },
                "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
              }, {
                "id" : "nonDeterministicRandomSeed",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--nonDeterministicRandomSeed"
                },
                "doc" : "Makes the GATK behave non deterministically, that is, the random numbers generated will be different in every run"
              }, {
                "id" : "disableRandomization",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--disableRandomization"
                },
                "doc" : "Completely eliminates randomization from nondeterministic methods. To be used mostly in the testing framework where dynamic parallelism can result in differing numbers of calls to the generator."
              }, {
                "id" : "maxRuntime",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--maxRuntime"
                },
                "doc" : "If provided, that GATK will stop execution cleanly as soon after maxRuntime has been exceeded, truncating the run but not exiting with a failure. By default the value is interpreted in minutes, but this can be changed by maxRuntimeUnits"
              }, {
                "id" : "maxRuntimeUnits",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--maxRuntimeUnits"
                },
                "doc" : "The TimeUnit for maxRuntime (NANOSECONDS| MICROSECONDS|MILLISECONDS|SECONDS|MINUTES| HOURS|DAYS)"
              }, {
                "id" : "enable_extended_output",
                "default" : true,
                "type" : "boolean",
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--enable_extended_output"
                }
              }, {
                "id" : "downsampling_type",
                "default" : "NONE",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--downsampling_type"
                }
              }, {
                "id" : "baq",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--baq"
                },
                "doc" : "Type of BAQ calculation to apply in the engine (OFF|CALCULATE_AS_NECESSARY| RECALCULATE)"
              }, {
                "id" : "baqGapOpenPenalty",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--baqGapOpenPenalty"
                },
                "doc" : "BAQ gap open penalty (Phred Scaled). Default value is 40. 30 is perhaps better for whole genome call sets"
              }, {
                "id" : "performanceLog",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--performanceLog"
                },
                "doc" : "If provided, a GATK runtime performance log will be written to this file"
              }, {
                "id" : "useOriginalQualities",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--useOriginalQualities"
                },
                "doc" : "If set, use the original base quality scores from the OQ tag when present instead of the standard scores"
              }, {
                "id" : "BQSR",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--BQSR"
                },
                "doc" : "The input covariates table file which enables on-the-fly base quality score recalibration"
              }, {
                "id" : "disable_indel_quals",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--disable_indel_quals"
                },
                "doc" : "If true, disables printing of base insertion and base deletion tags (with -BQSR)"
              }, {
                "id" : "emit_original_quals",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--emit_original_quals"
                },
                "doc" : "If true, enables printing of the OQ tag with the original base qualities (with -BQSR)"
              }, {
                "id" : "preserve_qscores_less_than",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--preserve_qscores_less_than"
                },
                "doc" : "Bases with quality scores less than this threshold won't be recalibrated (with -BQSR)"
              }, {
                "id" : "defaultBaseQualities",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--defaultBaseQualities"
                },
                "doc" : "If reads are missing some or all base quality scores, this value will be used for all base quality scores"
              }, {
                "id" : "validation_strictness",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--validation_strictness"
                },
                "doc" : "How strict should we be with validation (STRICT|LENIENT|SILENT)"
              }, {
                "id" : "remove_program_records",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--remove_program_records"
                },
                "doc" : "Should we override the Walker's default and remove program records from the SAM header"
              }, {
                "id" : "keep_program_records",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--keep_program_records"
                },
                "doc" : "Should we override the Walker's default and keep program records from the SAM header"
              }, {
                "id" : "unsafe",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--unsafe"
                },
                "doc" : "If set, enables unsafe operations - nothing will be checked at runtime. For expert users only who know what they are doing. We do not support usage of this argument. (ALLOW_UNINDEXED_BAM| ALLOW_UNSET_BAM_SORT_ORDER| NO_READ_ORDER_VERIFICATION| ALLOW_SEQ_DICT_INCOMPATIBILITY| LENIENT_VCF_PROCESSING|ALL)"
              }, {
                "id" : "num_threads",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--num_threads"
                },
                "doc" : "How many data threads should be allocated to running this analysis."
              }, {
                "id" : "num_cpu_threads_per_data_thread",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--num_cpu_threads_per_data_thread"
                },
                "doc" : "How many CPU threads should be allocated per data thread to running this analysis?"
              }, {
                "id" : "monitorThreadEfficiency",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--monitorThreadEfficiency"
                },
                "doc" : "Enable GATK threading efficiency monitoring"
              }, {
                "id" : "num_bam_file_handles",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--num_bam_file_handles"
                },
                "doc" : "The total number of BAM file handles to keep open simultaneously"
              }, {
                "id" : "read_group_black_list",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--read_group_black_list"
                },
                "doc" : "Filters out read groups matching <TAG> -<STRING> or a .txt file containing the filter strings one per line."
              }, {
                "id" : "pedigree",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--pedigree"
                },
                "doc" : "Pedigree files for samples"
              }, {
                "id" : "pedigreeString",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--pedigreeString"
                },
                "doc" : "Pedigree string for samples"
              }, {
                "id" : "pedigreeValidationType",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--pedigreeValidationType"
                },
                "doc" : "How strict should we be in validating the pedigree information? (STRICT|SILENT)"
              }, {
                "id" : "logging_level",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--logging_level"
                },
                "doc" : "Set the minimum level of logging, i.e. setting INFO get's you INFO up to FATAL, setting ERROR gets you ERROR and FATAL level logging."
              }, {
                "id" : "log_to_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--log_to_file"
                },
                "doc" : "Set the logging location"
              }, {
                "id" : "noop",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--noop"
                },
                "doc" : "used for debugging, basically exit as soon as we get the reads"
              }, {
                "id" : "tumor_sample_name",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--tumor_sample_name"
                },
                "doc" : "name to use for tumor in output files"
              }, {
                "id" : "bam_tumor_sample_name",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--bam_tumor_sample_name"
                },
                "doc" : "if the tumor bam contains multiple samples, only use read groups with SM equal to this value"
              }, {
                "id" : "normal_sample_name",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--normal_sample_name"
                },
                "doc" : "name to use for normal in output files"
              }, {
                "id" : "force_output",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--force_output"
                },
                "doc" : "force output for each site"
              }, {
                "id" : "force_alleles",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--force_alleles"
                },
                "doc" : "force output for all alleles at each site"
              }, {
                "id" : "only_passing_calls",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--only_passing_calls"
                },
                "doc" : "only emit passing calls"
              }, {
                "id" : "initial_tumor_lod",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--initial_tumor_lod"
                },
                "doc" : "Initial LOD threshold for calling tumor variant"
              }, {
                "id" : "tumor_lod",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--tumor_lod"
                },
                "doc" : "LOD threshold for calling tumor variant"
              }, {
                "id" : "fraction_contamination",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--fraction_contamination"
                },
                "doc" : "estimate of fraction (0-1) of physical contamination with other unrelated samples"
              }, {
                "id" : "minimum_mutation_cell_fraction",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--minimum_mutation_cell_fraction"
                },
                "doc" : "minimum fraction of cells which are presumed to have a mutation, used to handle non-clonality and contamination"
              }, {
                "id" : "normal_lod",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--normal_lod"
                },
                "doc" : "LOD threshold for calling normal non-germline"
              }, {
                "id" : "dbsnp_normal_lod",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--dbsnp_normal_lod"
                },
                "doc" : "LOD threshold for calling normal non-variant at dbsnp sites"
              }, {
                "id" : "somatic_classification_normal_power_threshold",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--somatic_classification_normal_power_threshold"
                },
                "doc" : "Power threshold for normal to <somatic_classification_normal_power_threshold> determine germline vs variant"
              }, {
                "id" : "minimum_normal_allele_fraction",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--minimum_normal_allele_fraction"
                },
                "doc" : "minimum allele fraction to be considered in normal, useful for normal sample contaminated with tumor"
              }, {
                "id" : "tumor_f_pretest",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--tumor_f_pretest"
                },
                "doc" : "for computational efficiency, reject sites with allelic fraction below this threshold"
              }, {
                "id" : "min_qscore",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--min_qscore"
                },
                "doc" : "threshold for minimum base quality score"
              }, {
                "id" : "gap_events_threshold",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--gap_events_threshold"
                },
                "doc" : "how many gapped events (ins/del) are allowed in proximity to this candidate"
              }, {
                "id" : "heavily_clipped_read_fraction",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--heavily_clipped_read_fraction"
                },
                "doc" : "if this fraction or more of the bases in a read are soft/hard clipped, do not use this read for mutation calling"
              }, {
                "id" : "clipping_bias_pvalue_threshold",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--clipping_bias_pvalue_threshold"
                },
                "doc" : "pvalue threshold for fishers exact test of clipping bias in mutant reads vs ref reads"
              }, {
                "id" : "fraction_mapq0_threshold",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--fraction_mapq0_threshold"
                },
                "doc" : "threshold for determining if there is relatedness between the alt and ref allele read piles"
              }, {
                "id" : "pir_median_threshold",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--pir_median_threshold"
                },
                "doc" : "threshold for clustered read position artifact median"
              }, {
                "id" : "pir_mad_threshold",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--pir_mad_threshold"
                },
                "doc" : "threshold for clustered read position artifact MAD"
              }, {
                "id" : "required_maximum_alt_allele_mapping_quality_score",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--required_maximum_alt_allele_mapping_quality_score"
                },
                "doc" : "required minimum value for <required_maximum_alt_allele_mapping_quality_score> tumor alt allele maximum mapping quality score"
              }, {
                "id" : "max_alt_alleles_in_normal_count",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--max_alt_alleles_in_normal_count"
                },
                "doc" : "threshold for maximum alternate allele counts in normal"
              }, {
                "id" : "max_alt_alleles_in_normal_qscore_sum",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--max_alt_alleles_in_normal_qscore_sum"
                },
                "doc" : "threshold for maximum alternate allele quality score sum in normal"
              }, {
                "id" : "max_alt_allele_in_normal_fraction",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--max_alt_allele_in_normal_fraction"
                },
                "doc" : "threshold for maximum alternate allele fraction in normal"
              }, {
                "id" : "power_constant_qscore",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--power_constant_qscore"
                },
                "doc" : "Phred scale quality score constant to use in power calculations"
              }, {
                "id" : "absolute_copy_number_data",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--absolute_copy_number_data"
                },
                "doc" : "Absolute Copy Number Data, as defined by Absolute, to use in power calculations"
              }, {
                "id" : "power_constant_af",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--power_constant_af"
                },
                "doc" : "Allelic fraction constant to use in power calculations"
              }, {
                "id" : "out",
                "type" : [ "null", "string", "File" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--out"
                },
                "doc" : "Call-stats output"
              }, {
                "id" : "vcf",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--vcf"
                },
                "doc" : "VCF output of mutation candidates"
              }, {
                "id" : "dbsnp",
                "type" : [ "null", "File" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--dbsnp"
                },
                "secondaryFiles" : [ "^.vcf.idx" ],
                "doc" : "VCF file of DBSNP information"
              }, {
                "id" : "cosmic",
                "type" : [ "null", "File" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--cosmic"
                },
                "secondaryFiles" : [ "^.vcf.idx" ],
                "doc" : "VCF file of COSMIC sites"
              }, {
                "id" : "coverage_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--coverage_file"
                },
                "doc" : "write out coverage in WIGGLE format to this file"
              }, {
                "id" : "coverage_20_q20_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--coverage_20_q20_file"
                },
                "doc" : "write out 20x of Q20 coverage in WIGGLE format to this file"
              }, {
                "id" : "power_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--power_file"
                },
                "doc" : "write out power in WIGGLE format to this file"
              }, {
                "id" : "tumor_depth_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--tumor_depth_file"
                },
                "doc" : "write out tumor read depth in WIGGLE format to this file"
              }, {
                "id" : "normal_depth_file",
                "type" : [ "null", {
                  "items" : "string",
                  "type" : "array"
                } ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--normal_depth_file"
                },
                "doc" : "write out normal read depth in WIGGLE format to this file"
              }, {
                "id" : "filter_mismatching_base_and_quals",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--filter_mismatching_base_and_quals"
                },
                "doc" : "if a read has mismatching number of bases and base qualities, filter out the read instead of blowing up."
              }, {
                "id" : "downsample_to_coverage",
                "type" : [ "null", "int" ],
                "inputBinding" : {
                  "position" : 2,
                  "prefix" : "--downsample_to_coverage"
                },
                "doc" : "Target coverage threshold for downsampling to coverage"
              } ],
              "outputs" : [ {
                "id" : "output",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.vcf)\n    return inputs.vcf;\n  return null;\n}\n"
                }
              }, {
                "id" : "callstats_output",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.out)\n    return inputs.out;\n  return null;\n}\n"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : 24000,
                "coresMin" : 1
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-mutect:1.1.4"
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "java" ],
              "arguments" : [ {
                "position" : 1,
                "prefix" : "-jar",
                "shellQuote" : false,
                "valueFrom" : "/usr/bin/mutect.jar"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Xms$(Math.round(parseInt(runtime.ram)/1910))G"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Xmx$(Math.round(parseInt(runtime.ram)/955))G"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-XX:-UseGCOverheadLimit"
              }, {
                "position" : 0,
                "shellQuote" : false,
                "valueFrom" : "-Djava.io.tmpdir=$(runtime.tmpdir)"
              } ],
              "doc" : "None\n",
              "id" : "mutect",
              "class" : "CommandLineTool"
            },
            "in" : [ {
              "id" : "reference_sequence",
              "source" : "ref_fasta"
            }, {
              "id" : "dbsnp",
              "source" : "dbsnp"
            }, {
              "id" : "cosmic",
              "source" : "cosmic"
            }, {
              "id" : "input_file_normal",
              "source" : "normal_bam"
            }, {
              "id" : "input_file_tumor",
              "source" : "tumor_bam"
            }, {
              "id" : "read_filter",
              "source" : "mutect_rf"
            }, {
              "id" : "downsample_to_coverage",
              "source" : "mutect_dcov"
            }, {
              "id" : "intervals",
              "source" : "bed"
            }, {
              "id" : "vcf",
              "valueFrom" : "${ return inputs.input_file_tumor.basename.replace(\".bam\",\".\") + inputs.input_file_normal.basename.replace(\".bam\", \".mutect.vcf\") }"
            }, {
              "id" : "out",
              "valueFrom" : "${ return inputs.input_file_tumor.basename.replace(\".bam\",\".\") + inputs.input_file_normal.basename.replace(\".bam\", \".mutect.txt\") }"
            } ],
            "out" : [ {
              "id" : "output"
            }, {
              "id" : "callstats_output"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          } ],
          "id" : "call-variants",
          "class" : "Workflow"
        },
        "in" : [ {
          "id" : "tumor_bam",
          "source" : "tumor_index/bam_indexed"
        }, {
          "id" : "normal_bam",
          "source" : "normal_index/bam_indexed"
        }, {
          "id" : "genome",
          "source" : "genome"
        }, {
          "id" : "ref_fasta",
          "source" : "ref_fasta"
        }, {
          "id" : "normal_sample_name",
          "source" : "normal_sample_name"
        }, {
          "id" : "tumor_sample_name",
          "source" : "tumor_sample_name"
        }, {
          "id" : "dbsnp",
          "source" : "dbsnp"
        }, {
          "id" : "cosmic",
          "source" : "cosmic"
        }, {
          "id" : "mutect_dcov",
          "source" : "mutect_dcov"
        }, {
          "id" : "mutect_rf",
          "source" : "mutect_rf"
        }, {
          "id" : "bed",
          "source" : "bed"
        }, {
          "id" : "refseq",
          "source" : "refseq"
        }, {
          "id" : "facets_pcval",
          "source" : "facets_pcval"
        }, {
          "id" : "facets_cval",
          "source" : "facets_cval"
        }, {
          "id" : "facets_snps",
          "source" : "facets_snps"
        } ],
        "out" : [ {
          "id" : "vardict_vcf"
        }, {
          "id" : "mutect_vcf"
        }, {
          "id" : "mutect_callstats"
        }, {
          "id" : "facets_png"
        }, {
          "id" : "facets_txt_hisens"
        }, {
          "id" : "facets_txt_purity"
        }, {
          "id" : "facets_out"
        }, {
          "id" : "facets_rdata"
        }, {
          "id" : "facets_seg"
        }, {
          "id" : "facets_counts"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "filtering",
        "run" : {
          "inputs" : [ {
            "id" : "complex_nn",
            "type" : "float"
          }, {
            "id" : "complex_tn",
            "type" : "float"
          }, {
            "id" : "normal_bam",
            "type" : "File"
          }, {
            "id" : "tumor_bam",
            "type" : "File"
          }, {
            "id" : "mutect_vcf",
            "type" : "File"
          }, {
            "id" : "mutect_callstats",
            "type" : "File"
          }, {
            "id" : "vardict_vcf",
            "type" : "File"
          }, {
            "id" : "hotspot_vcf",
            "type" : "string"
          }, {
            "id" : "tumor_sample_name",
            "type" : "string"
          }, {
            "id" : "ref_fasta",
            "type" : "File"
          } ],
          "outputs" : [ {
            "id" : "mutect_vcf_filtering_output",
            "type" : "File",
            "outputSource" : "mutect_filtering_step/vcf",
            "secondaryFiles" : [ ".tbi" ]
          }, {
            "id" : "vardict_vcf_filtering_output",
            "type" : "File",
            "outputSource" : "vardict_filtering_step/vcf",
            "secondaryFiles" : [ ".tbi" ]
          } ],
          "hints" : [ ],
          "requirements" : [ ],
          "successCodes" : [ ],
          "steps" : [ {
            "id" : "mutect_filtering_step",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "verbose",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "prefix" : "--verbose"
                },
                "doc" : "More verbose logging to help with debugging"
              }, {
                "id" : "inputVcf",
                "type" : [ "string", "File" ],
                "inputBinding" : {
                  "prefix" : "--inputVcf"
                },
                "doc" : "Input vcf muTect file which needs to be filtered"
              }, {
                "id" : "inputTxt",
                "type" : [ "string", "File" ],
                "inputBinding" : {
                  "prefix" : "--inputTxt"
                },
                "doc" : "Input txt muTect file which needs to be filtered"
              }, {
                "id" : "tsampleName",
                "type" : "string",
                "inputBinding" : {
                  "prefix" : "--tsampleName"
                },
                "doc" : "Name of the tumor Sample"
              }, {
                "id" : "refFasta",
                "type" : [ "string", "File" ],
                "inputBinding" : {
                  "prefix" : "--refFasta"
                },
                "doc" : "Reference genome in fasta format"
              }, {
                "id" : "dp",
                "default" : 5,
                "type" : [ "null", "int" ],
                "inputBinding" : {
                  "prefix" : "--totaldepth"
                },
                "doc" : "Tumor total depth threshold"
              }, {
                "id" : "ad",
                "default" : 3,
                "type" : [ "null", "int" ],
                "inputBinding" : {
                  "prefix" : "--alleledepth"
                },
                "doc" : "Tumor allele depth threshold"
              }, {
                "id" : "tnr",
                "default" : 5,
                "type" : [ "null", "int" ],
                "inputBinding" : {
                  "prefix" : "--tnRatio"
                },
                "doc" : "Tumor-Normal variant frequency ratio threshold"
              }, {
                "id" : "vf",
                "default" : 0.01,
                "type" : [ "null", "float" ],
                "inputBinding" : {
                  "prefix" : "--variantfraction"
                },
                "doc" : "Tumor variant frequency threshold"
              }, {
                "id" : "hotspotVcf",
                "type" : [ "null", "string", "File" ],
                "inputBinding" : {
                  "prefix" : "--hotspotVcf"
                },
                "doc" : "Input vcf file with hotspots that skip VAF ratio filter"
              }, {
                "id" : "outdir",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "prefix" : "--outDir"
                },
                "doc" : "Full Path to the output dir."
              } ],
              "outputs" : [ {
                "id" : "vcf",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.inputVcf)\n    return inputs.inputVcf.basename.replace(\".vcf\",\"_STDfilter.norm.vcf.gz\");\n  return null;\n}\n"
                },
                "secondaryFiles" : [ "^.tbi", ".tbi" ]
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : 16000,
                "coresMin" : 2
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-basic-filtering:0.3"
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "python", "/usr/bin/basicfiltering/filter_mutect.py" ],
              "arguments" : [ ],
              "doc" : "Filter snps from the output of muTect v1.14\n",
              "id" : "basic-filtering-mutect",
              "class" : "CommandLineTool"
            },
            "in" : [ {
              "id" : "inputVcf",
              "source" : "mutect_vcf"
            }, {
              "id" : "inputTxt",
              "source" : "mutect_callstats"
            }, {
              "id" : "tsampleName",
              "source" : "tumor_sample_name"
            }, {
              "id" : "hotspotVcf",
              "source" : "hotspot_vcf"
            }, {
              "id" : "refFasta",
              "source" : "ref_fasta"
            } ],
            "out" : [ {
              "id" : "vcf"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "vardict_complex_filtering_step",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "inputVcf",
                "type" : "File",
                "inputBinding" : {
                  "prefix" : "--input-vcf"
                },
                "doc" : "Input VCF file"
              }, {
                "id" : "normal_bam",
                "type" : "File",
                "inputBinding" : {
                  "prefix" : "--normal-bam"
                },
                "doc" : "Normal Bam file"
              }, {
                "id" : "tumor_bam",
                "type" : "File",
                "inputBinding" : {
                  "prefix" : "--tumor-bam"
                },
                "doc" : "Tumor Bam file"
              }, {
                "id" : "tumor_id",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "prefix" : "--tumor-id"
                },
                "doc" : "Tumor sample ID"
              }, {
                "id" : "output_vcf",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "prefix" : "--output-vcf"
                },
                "doc" : "Output VCF file"
              }, {
                "id" : "flank_len",
                "default" : 50,
                "type" : [ "null", "int" ],
                "inputBinding" : {
                  "prefix" : "--flank-len"
                },
                "doc" : "Flanking bps around event to check for noise"
              }, {
                "id" : "mapping_qual",
                "default" : 20,
                "type" : [ "null", "int" ],
                "inputBinding" : {
                  "prefix" : "--mapping-qual"
                },
                "doc" : "Minimum mapping quality of noisy reads"
              }, {
                "id" : "nrm_noise",
                "default" : 0.1,
                "type" : [ "null", "float" ],
                "inputBinding" : {
                  "prefix" : "--nrm-noise"
                },
                "doc" : "Maximum allowed normal noise"
              }, {
                "id" : "tum_noise",
                "default" : 0.2,
                "type" : [ "null", "float" ],
                "inputBinding" : {
                  "prefix" : "--tum-noise"
                },
                "doc" : "Maximum allowed tumor noise"
              } ],
              "outputs" : [ {
                "id" : "vcf",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.output_vcf)\n    return inputs.output_vcf;\n  return null;\n}"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InitialWorkDirRequirement",
                "listing" : [ "$(inputs.inputVcf)" ]
              }, {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : 16000,
                "coresMin" : 2
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-basic-filtering:0.3"
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "python", "/usr/bin/basicfiltering/filter_complex.py" ],
              "arguments" : [ ],
              "doc" : "Given a VCF listing somatic events and a TN-pair of BAMS, apply a complex filter based on indels/soft-clipping noise\n",
              "id" : "basic-filtering-complex",
              "class" : "CommandLineTool"
            },
            "in" : [ {
              "id" : "nrm_noise",
              "source" : "complex_nn"
            }, {
              "id" : "tum_noise",
              "source" : "complex_tn"
            }, {
              "id" : "inputVcf",
              "source" : "vardict_vcf"
            }, {
              "id" : "normal_bam",
              "source" : "normal_bam"
            }, {
              "id" : "tumor_bam",
              "source" : "tumor_bam"
            }, {
              "id" : "tumor_id",
              "source" : "tumor_sample_name"
            }, {
              "id" : "output_vcf",
              "valueFrom" : "${ return inputs.inputVcf.basename.replace(\".vcf\", \".complex_filtered.vcf\"); }"
            } ],
            "out" : [ {
              "id" : "vcf"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          }, {
            "id" : "vardict_filtering_step",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "verbose",
                "default" : false,
                "type" : [ "null", "boolean" ],
                "inputBinding" : {
                  "prefix" : "--verbose"
                },
                "doc" : "More verbose logging to help with debugging"
              }, {
                "id" : "inputVcf",
                "type" : [ "string", "File" ],
                "inputBinding" : {
                  "prefix" : "--inputVcf"
                },
                "doc" : "Input vcf vardict file which needs to be filtered"
              }, {
                "id" : "tsampleName",
                "type" : "string",
                "inputBinding" : {
                  "prefix" : "--tsampleName"
                },
                "doc" : "Name of the tumor Sample"
              }, {
                "id" : "refFasta",
                "type" : [ "string", "File" ],
                "inputBinding" : {
                  "prefix" : "--refFasta"
                },
                "doc" : "Reference genome in fasta format"
              }, {
                "id" : "dp",
                "default" : 5,
                "type" : [ "null", "int" ],
                "inputBinding" : {
                  "prefix" : "--totaldepth"
                },
                "doc" : "Tumor total depth threshold"
              }, {
                "id" : "ad",
                "default" : 3,
                "type" : [ "null", "int" ],
                "inputBinding" : {
                  "prefix" : "--alleledepth"
                },
                "doc" : "Tumor allele depth threshold"
              }, {
                "id" : "tnr",
                "default" : 5,
                "type" : [ "null", "int" ],
                "inputBinding" : {
                  "prefix" : "--tnRatio"
                },
                "doc" : "Tumor-Normal variant frequency ratio threshold"
              }, {
                "id" : "vf",
                "default" : 0.01,
                "type" : [ "null", "float" ],
                "inputBinding" : {
                  "prefix" : "--variantfraction"
                },
                "doc" : "Tumor variant frequency threshold"
              }, {
                "id" : "mq",
                "default" : 20,
                "type" : [ "null", "int" ],
                "inputBinding" : {
                  "prefix" : "--minqual"
                },
                "doc" : "Minimum variant call quality"
              }, {
                "id" : "hotspotVcf",
                "type" : [ "null", "string", "File" ],
                "inputBinding" : {
                  "prefix" : "--hotspotVcf"
                },
                "doc" : "Input vcf file with hotspots that skip VAF ratio filter"
              }, {
                "id" : "outdir",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "prefix" : "--outDir"
                },
                "doc" : "Full Path to the output dir."
              } ],
              "outputs" : [ {
                "id" : "vcf",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.inputVcf)\n    return inputs.inputVcf.basename.replace(\".vcf\",\"_STDfilter.norm.vcf.gz\");\n  return null;\n}\n"
                },
                "secondaryFiles" : [ "^.tbi", ".tbi" ]
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : 10000,
                "coresMin" : 2
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-basic-filtering:0.3"
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "python", "/usr/bin/basicfiltering/filter_vardict.py" ],
              "arguments" : [ ],
              "doc" : "Filter snps/indels from the output of vardict v1.4.6\n",
              "id" : "basic-filtering-vardict",
              "class" : "CommandLineTool"
            },
            "in" : [ {
              "id" : "inputVcf",
              "source" : "vardict_complex_filtering_step/vcf"
            }, {
              "id" : "tsampleName",
              "source" : "tumor_sample_name"
            }, {
              "id" : "hotspotVcf",
              "source" : "hotspot_vcf"
            }, {
              "id" : "refFasta",
              "source" : "ref_fasta"
            } ],
            "out" : [ {
              "id" : "vcf"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          } ],
          "id" : "filtering",
          "class" : "Workflow"
        },
        "in" : [ {
          "id" : "complex_nn",
          "source" : "complex_nn"
        }, {
          "id" : "complex_tn",
          "source" : "complex_tn"
        }, {
          "id" : "normal_bam",
          "source" : "normal_bam"
        }, {
          "id" : "tumor_bam",
          "source" : "tumor_bam"
        }, {
          "id" : "mutect_vcf",
          "source" : "call_variants/mutect_vcf"
        }, {
          "id" : "mutect_callstats",
          "source" : "call_variants/mutect_callstats"
        }, {
          "id" : "vardict_vcf",
          "source" : "call_variants/vardict_vcf"
        }, {
          "id" : "tumor_sample_name",
          "source" : "tumor_sample_name"
        }, {
          "id" : "hotspot_vcf",
          "source" : "hotspot_vcf"
        }, {
          "id" : "ref_fasta",
          "source" : "ref_fasta"
        } ],
        "out" : [ {
          "id" : "vardict_vcf_filtering_output"
        }, {
          "id" : "mutect_vcf_filtering_output"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "create_vcf_file_array",
        "run" : {
          "inputs" : [ {
            "id" : "vcf_vardict",
            "type" : "File",
            "secondaryFiles" : [ ".tbi" ]
          }, {
            "id" : "vcf_mutect",
            "type" : "File",
            "secondaryFiles" : [ ".tbi" ]
          } ],
          "outputs" : [ {
            "id" : "vcf_files",
            "type" : {
              "items" : "File",
              "type" : "array"
            },
            "secondaryFiles" : [ ".tbi" ]
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "InlineJavascriptRequirement"
          } ],
          "successCodes" : [ ],
          "expression" : "${ var project_object = {}; project_object['vcf_files'] = [ inputs.vcf_vardict, inputs.vcf_mutect]; return project_object; }",
          "id" : "create-vcf-file-array",
          "class" : "ExpressionTool"
        },
        "in" : [ {
          "id" : "vcf_vardict",
          "source" : "filtering/vardict_vcf_filtering_output"
        }, {
          "id" : "vcf_mutect",
          "source" : "filtering/mutect_vcf_filtering_output"
        } ],
        "out" : [ {
          "id" : "vcf_files"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "concat",
        "run" : {
          "cwlVersion" : "v1.0",
          "inputs" : [ {
            "id" : "threads",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--threads"
            },
            "doc" : "<int> Number of extra output compression threads [0]"
          }, {
            "id" : "compact_PS",
            "default" : false,
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--compact-PS"
            },
            "doc" : "Do not output PS tag at each site, only at the start of a new phase set block."
          }, {
            "id" : "remove_duplicates",
            "default" : false,
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--remove-duplicates"
            },
            "doc" : "Alias for -d none"
          }, {
            "id" : "ligate",
            "default" : false,
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--ligate"
            },
            "doc" : "Ligate phased VCFs by matching phase at overlapping haplotypes"
          }, {
            "id" : "output_type",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--output-type"
            },
            "doc" : "<b|u|z|v> b - compressed BCF, u - uncompressed BCF, z - compressed VCF, v - uncompressed VCF [v]"
          }, {
            "id" : "no_version",
            "default" : false,
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--no-version"
            },
            "doc" : "do not append version and command line to the header"
          }, {
            "id" : "naive",
            "default" : false,
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--naive"
            },
            "doc" : "Concatenate BCF files without recompression (dangerous, use with caution)"
          }, {
            "id" : "allow_overlaps",
            "default" : false,
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--allow-overlaps"
            },
            "doc" : "First coordinate of the next file can precede last record of the current file."
          }, {
            "id" : "min_PQ",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--min-PQ"
            },
            "doc" : "<int> Break phase set if phasing quality is lower than <int> [30]"
          }, {
            "id" : "regions_file",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--regions-file"
            },
            "doc" : "<file> Restrict to regions listed in a file"
          }, {
            "id" : "regions",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--regions"
            },
            "doc" : "<region> Restrict to comma-separated list of regions"
          }, {
            "id" : "rm_dups",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--rm-dups"
            },
            "doc" : "<string> Output duplicate records present in multiple files only once - <snps|indels|both|all|none>"
          }, {
            "id" : "output",
            "default" : "bcftools_concat.vcf",
            "type" : "string",
            "inputBinding" : {
              "prefix" : "--output"
            },
            "doc" : "<file> Write output to a file [standard output]"
          }, {
            "id" : "list",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--file-list"
            },
            "doc" : "<file> Read the list of files from a file."
          }, {
            "id" : "vcf_files_tbi",
            "type" : [ "null", {
              "items" : "File",
              "type" : "array"
            } ],
            "inputBinding" : {
              "position" : 1
            },
            "secondaryFiles" : [ ".tbi" ],
            "doc" : "Array of vcf files to be concatenated into one vcf"
          }, {
            "id" : "vcf_files_csi",
            "type" : [ "null", {
              "items" : "File",
              "type" : "array"
            } ],
            "inputBinding" : {
              "position" : 1
            },
            "secondaryFiles" : [ "^.bcf.csi" ],
            "doc" : "Array of vcf files to be concatenated into one vcf"
          } ],
          "outputs" : [ {
            "id" : "concat_vcf_output_file",
            "type" : "File",
            "outputBinding" : {
              "glob" : "${\n  if (inputs.output)\n    return inputs.output;\n  return null;\n}"
            }
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "InlineJavascriptRequirement"
          }, {
            "class" : "ResourceRequirement",
            "ramMin" : 8000,
            "coresMin" : 1
          }, {
            "class" : "DockerRequirement",
            "dockerPull" : "mskcc/roslin-variant-htslib:1.9"
          } ],
          "successCodes" : [ ],
          "baseCommand" : [ "/usr/bin/bcftools", "concat" ],
          "arguments" : [ ],
          "doc" : "concatenate VCF/BCF files from the same set of samples\n",
          "id" : "bcftools-concat",
          "class" : "CommandLineTool"
        },
        "in" : [ {
          "id" : "vcf_files_tbi",
          "source" : "create_vcf_file_array/vcf_files"
        }, {
          "id" : "tumor_sample_name",
          "source" : "tumor_sample_name"
        }, {
          "id" : "normal_sample_name",
          "source" : "normal_sample_name"
        }, {
          "id" : "allow_overlaps",
          "valueFrom" : "${ return true; }"
        }, {
          "id" : "rm_dups",
          "valueFrom" : "${ return \"all\"; }"
        }, {
          "id" : "output_type",
          "valueFrom" : "${ return \"z\"; }"
        }, {
          "id" : "output",
          "valueFrom" : "${ return inputs.tumor_sample_name + \".\" + inputs.normal_sample_name + \".combined-variants.vcf.gz\" }"
        } ],
        "out" : [ {
          "id" : "concat_vcf_output_file"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "tabix_index",
        "run" : {
          "cwlVersion" : "v1.0",
          "inputs" : [ {
            "id" : "input_vcf",
            "type" : "File",
            "inputBinding" : {
              "position" : 1
            },
            "doc" : "VCF to tabix index"
          }, {
            "id" : "zero",
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--zero-based"
            },
            "doc" : "coordinates are zero-based"
          }, {
            "id" : "comment",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--comment"
            },
            "doc" : "skip comment lines starting with CHAR [null]"
          }, {
            "id" : "csi",
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--csi"
            },
            "doc" : "generate CSI index for VCF (default is TBI)"
          }, {
            "id" : "end",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--end"
            },
            "doc" : "column number for region end (if no end, set INT to -b) [5]"
          }, {
            "id" : "being",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--begin"
            },
            "doc" : "column number for region start [4]"
          }, {
            "id" : "force",
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--force"
            },
            "doc" : "overwrite existing index without asking"
          }, {
            "id" : "min_shift",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--min-shift"
            },
            "doc" : "set minimal interval size for CSI indices to 2^INT [14]"
          }, {
            "id" : "preset",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--preset"
            },
            "doc" : "gff, bed, sam, vcf"
          }, {
            "id" : "sequence",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--sequence"
            },
            "doc" : "column number for sequence names (suppressed by -p) [1]"
          }, {
            "id" : "skip_lines",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--skip-lines"
            },
            "doc" : "skip first INT lines [0]"
          }, {
            "id" : "print_header",
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--print-header"
            },
            "doc" : "print also the header lines"
          }, {
            "id" : "only_header",
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--only-header"
            },
            "doc" : "print only the header lines"
          }, {
            "id" : "list_chroms",
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--list-chroms"
            },
            "doc" : "list chromosome names"
          }, {
            "id" : "reheader",
            "type" : [ "null", "File" ],
            "inputBinding" : {
              "prefix" : "--reheader"
            },
            "doc" : "replace the header with the content of FILE"
          }, {
            "id" : "regions",
            "type" : [ "null", "File" ],
            "inputBinding" : {
              "prefix" : "--regions"
            },
            "doc" : "restrict to regions listed in the file"
          }, {
            "id" : "targets",
            "type" : [ "null", "File" ],
            "inputBinding" : {
              "prefix" : "--targets"
            },
            "doc" : "similar to -R but streams rather than index-jumps"
          } ],
          "outputs" : [ {
            "id" : "tabix_output_file",
            "type" : "File",
            "outputBinding" : {
              "glob" : "*.gz"
            },
            "secondaryFiles" : [ ".tbi", ".csi" ]
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "InlineJavascriptRequirement"
          }, {
            "class" : "InitialWorkDirRequirement",
            "listing" : [ "$(inputs.input_vcf)" ]
          }, {
            "class" : "ResourceRequirement",
            "ramMin" : 80000,
            "coresMin" : 1
          }, {
            "class" : "DockerRequirement",
            "dockerPull" : "mskcc/roslin-variant-htslib:1.9"
          } ],
          "successCodes" : [ ],
          "baseCommand" : [ "/usr/local/bin/tabix" ],
          "arguments" : [ ],
          "doc" : "Index vcf files\n",
          "id" : "tabix",
          "class" : "CommandLineTool"
        },
        "in" : [ {
          "id" : "input_vcf",
          "source" : "concat/concat_vcf_output_file"
        }, {
          "id" : "preset",
          "valueFrom" : "${ return \"vcf\"; }"
        } ],
        "out" : [ {
          "id" : "tabix_output_file"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "annotate",
        "run" : {
          "cwlVersion" : "v1.0",
          "inputs" : [ {
            "id" : "annotations",
            "type" : [ "null", "File" ],
            "inputBinding" : {
              "prefix" : "--annotations"
            },
            "doc" : "VCF file or tabix-indexed file with annotations CHR\\tPOS[\\tVALUE]+"
          }, {
            "id" : "threads",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--threads"
            },
            "doc" : "<int> Number of extra output compression threads [0]"
          }, {
            "id" : "collapse",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--collapse"
            },
            "doc" : "matching records by <snps|indels|both|all|some|none>, see man page for details [some]"
          }, {
            "id" : "columns",
            "type" : [ "null", {
              "items" : "string",
              "type" : "array"
            } ],
            "inputBinding" : {
              "itemSeparator" : ",",
              "prefix" : "--columns"
            },
            "doc" : "list of columns in the annotation file, e.g. CHROM,POS,REF,ALT,-,INFO/TAG. See man page for details"
          }, {
            "id" : "exclude",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--exclude"
            },
            "doc" : "exclude sites for which the expression is true (see man page for details)"
          }, {
            "id" : "header_lines",
            "type" : [ "null", "File" ],
            "inputBinding" : {
              "prefix" : "--header-lines"
            },
            "doc" : "lines which should be appended to the VCF header"
          }, {
            "id" : "set_id",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--set-id"
            },
            "doc" : "set ID column, see man page for details"
          }, {
            "id" : "include",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--include"
            },
            "doc" : "select sites for which the expression is true (see man page for details)"
          }, {
            "id" : "keep_sites",
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--keep-sites"
            },
            "doc" : "leave -i/-e sites unchanged instead of discarding them"
          }, {
            "id" : "mark_sites",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--mark-sites"
            },
            "doc" : "add INFO/tag flag to sites which are (\"+\") or are not (\"-\") listed in the -a file"
          }, {
            "id" : "no_version",
            "default" : false,
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--no-version"
            },
            "doc" : "do not append version and command line to the header"
          }, {
            "id" : "output",
            "default" : "bcftools_annotate.vcf",
            "type" : "string",
            "inputBinding" : {
              "prefix" : "--output"
            },
            "doc" : "<file> Write output to a file [standard output]"
          }, {
            "id" : "output_type",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--output-type"
            },
            "doc" : "<b|u|z|v> b - compressed BCF, u - uncompressed BCF, z - compressed VCF, v - uncompressed VCF [v]"
          }, {
            "id" : "regions",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--regions"
            },
            "doc" : "<region> Restrict to comma-separated list of regions"
          }, {
            "id" : "regions_file",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--regions-file"
            },
            "doc" : "<file> Restrict to regions listed in a file"
          }, {
            "id" : "rename_chrs",
            "type" : [ "null", "File" ],
            "inputBinding" : {
              "prefix" : "--rename-chrs"
            },
            "doc" : "First coordinate of the next file can precede last record of the current file."
          }, {
            "id" : "samples",
            "type" : [ "null", {
              "items" : "string",
              "type" : "array"
            } ],
            "inputBinding" : {
              "itemSeparator" : ",",
              "prefix" : "--samples"
            },
            "doc" : "Do not output PS tag at each site, only at the start of a new phase set block."
          }, {
            "id" : "samples_file",
            "type" : [ "null", "File" ],
            "inputBinding" : {
              "prefix" : "--samples-file"
            },
            "doc" : "First coordinate of the next file can precede last record of the current file."
          }, {
            "id" : "remove",
            "type" : [ "null", {
              "items" : "string",
              "type" : "array"
            } ],
            "inputBinding" : {
              "itemSeparator" : ",",
              "prefix" : "--remove"
            },
            "doc" : "Do not output PS tag at each site, only at the start of a new phase set block."
          }, {
            "id" : "vcf_file_tbi",
            "type" : [ "null", "File" ],
            "inputBinding" : {
              "position" : 1
            },
            "secondaryFiles" : [ ".tbi" ],
            "doc" : "Vcf file to be annotated"
          }, {
            "id" : "vcf_file_csi",
            "type" : [ "null", "File" ],
            "inputBinding" : {
              "position" : 1
            },
            "secondaryFiles" : [ "^.bcf.csi" ],
            "doc" : "Vcf file to be annotated"
          } ],
          "outputs" : [ {
            "id" : "annotate_vcf_output_file",
            "type" : "File",
            "outputBinding" : {
              "glob" : "${\n  if (inputs.output)\n    return inputs.output;\n  return null;\n}"
            }
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "InlineJavascriptRequirement"
          }, {
            "class" : "ResourceRequirement",
            "ramMin" : 8000,
            "coresMin" : 1
          }, {
            "class" : "DockerRequirement",
            "dockerPull" : "mskcc/roslin-variant-htslib:1.9"
          } ],
          "successCodes" : [ ],
          "baseCommand" : [ "/usr/bin/bcftools", "annotate" ],
          "arguments" : [ ],
          "doc" : "Annotate and edit VCF/BCF files.\n",
          "id" : "bcftools-annotate",
          "class" : "CommandLineTool"
        },
        "in" : [ {
          "id" : "annotations",
          "source" : "filtering/mutect_vcf_filtering_output"
        }, {
          "id" : "tumor_sample_name",
          "source" : "tumor_sample_name"
        }, {
          "id" : "normal_sample_name",
          "source" : "normal_sample_name"
        }, {
          "id" : "columns",
          "valueFrom" : "${ return [\"INFO/FAILURE_REASON\"]; }"
        }, {
          "id" : "mark_sites",
          "valueFrom" : "${ return \"+set=MuTect\"; }"
        }, {
          "id" : "vcf_file_tbi",
          "source" : "tabix_index/tabix_output_file"
        }, {
          "id" : "output",
          "valueFrom" : "${ return inputs.tumor_sample_name + \".\" + inputs.normal_sample_name + \".annotate-variants.vcf\" }"
        } ],
        "out" : [ {
          "id" : "annotate_vcf_output_file"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      } ],
      "id" : "variants-pair",
      "class" : "Workflow"
    },
    "in" : [ {
      "id" : "runparams",
      "source" : "runparams"
    }, {
      "id" : "db_files",
      "source" : "db_files"
    }, {
      "id" : "bams",
      "source" : "alignment/bams"
    }, {
      "id" : "pair",
      "source" : "pair"
    }, {
      "id" : "normal_bam",
      "valueFrom" : "${ return inputs.bams[1]; }"
    }, {
      "id" : "tumor_bam",
      "valueFrom" : "${ return inputs.bams[0]; }"
    }, {
      "id" : "genome",
      "valueFrom" : "${ return inputs.runparams.genome }"
    }, {
      "id" : "bed",
      "source" : "alignment/bed"
    }, {
      "id" : "normal_sample_name",
      "valueFrom" : "${ return inputs.pair[1].ID; }"
    }, {
      "id" : "tumor_sample_name",
      "valueFrom" : "${ return inputs.pair[0].ID; }"
    }, {
      "id" : "dbsnp",
      "source" : "dbsnp"
    }, {
      "id" : "cosmic",
      "source" : "cosmic"
    }, {
      "id" : "mutect_dcov",
      "valueFrom" : "${ return inputs.runparams.mutect_dcov }"
    }, {
      "id" : "mutect_rf",
      "valueFrom" : "${ return inputs.runparams.mutect_rf }"
    }, {
      "id" : "refseq",
      "valueFrom" : "${ return inputs.db_files.refseq }"
    }, {
      "id" : "hotspot_vcf",
      "valueFrom" : "${ return inputs.db_files.hotspot_vcf }"
    }, {
      "id" : "ref_fasta",
      "source" : "ref_fasta"
    }, {
      "id" : "facets_pcval",
      "valueFrom" : "${ return inputs.runparams.facets_pcval }"
    }, {
      "id" : "facets_cval",
      "valueFrom" : "${ return inputs.runparams.facets_cval }"
    }, {
      "id" : "facets_snps",
      "valueFrom" : "${ return inputs.db_files.facets_snps }"
    }, {
      "id" : "complex_tn",
      "valueFrom" : "${ return inputs.runparams.complex_tn; }"
    }, {
      "id" : "complex_nn",
      "valueFrom" : "${ return inputs.runparams.complex_nn; }"
    } ],
    "out" : [ {
      "id" : "combine_vcf"
    }, {
      "id" : "annotate_vcf"
    }, {
      "id" : "facets_png"
    }, {
      "id" : "facets_txt_hisens"
    }, {
      "id" : "facets_txt_purity"
    }, {
      "id" : "facets_out"
    }, {
      "id" : "facets_rdata"
    }, {
      "id" : "facets_seg"
    }, {
      "id" : "mutect_vcf"
    }, {
      "id" : "mutect_callstats"
    }, {
      "id" : "vardict_vcf"
    }, {
      "id" : "facets_counts"
    }, {
      "id" : "vardict_norm_vcf"
    }, {
      "id" : "mutect_norm_vcf"
    } ],
    "hints" : [ ],
    "requirements" : [ ]
  }, {
    "id" : "maf_processing",
    "run" : {
      "cwlVersion" : "v1.0",
      "inputs" : [ {
        "id" : "pair",
        "type" : {
          "items" : {
            "fields" : {
              "CN" : "string",
              "ID" : "string",
              "LB" : "string",
              "PL" : "string",
              "PU" : "string[]",
              "R1" : "File[]",
              "R2" : "File[]",
              "RG_ID" : "string[]",
              "adapter" : "string",
              "adapter2" : "string",
              "bam" : "File[]",
              "bwa_output" : "string",
              "zR1" : "File[]",
              "zR2" : "File[]"
            },
            "type" : "record"
          },
          "type" : "array"
        }
      }, {
        "id" : "bams",
        "type" : "File[]",
        "secondaryFiles" : [ "^.bai" ]
      }, {
        "id" : "annotate_vcf",
        "type" : "File"
      }, {
        "id" : "normal_sample_name",
        "type" : "string"
      }, {
        "id" : "tumor_sample_name",
        "type" : "string"
      }, {
        "id" : "genome",
        "type" : "string"
      }, {
        "id" : "ref_fasta",
        "type" : "File",
        "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
      }, {
        "id" : "vep_path",
        "type" : "string"
      }, {
        "id" : "custom_enst",
        "type" : "string"
      }, {
        "id" : "exac_filter",
        "type" : "File",
        "secondaryFiles" : [ ".tbi" ]
      }, {
        "id" : "vep_data",
        "type" : "string"
      }, {
        "id" : "curated_bams",
        "type" : "File[]",
        "secondaryFiles" : [ "^.bai" ]
      }, {
        "id" : "hotspot_list",
        "type" : "string"
      } ],
      "outputs" : [ {
        "id" : "maf",
        "type" : "File",
        "outputSource" : "ngs_filters/output"
      }, {
        "id" : "portal_fillout",
        "type" : "File",
        "outputSource" : "fillout_tumor_normal/portal_fillout"
      } ],
      "hints" : [ ],
      "requirements" : [ {
        "class" : "MultipleInputFeatureRequirement"
      }, {
        "class" : "ScatterFeatureRequirement"
      }, {
        "class" : "SubworkflowFeatureRequirement"
      }, {
        "class" : "InlineJavascriptRequirement"
      }, {
        "class" : "StepInputExpressionRequirement"
      } ],
      "successCodes" : [ ],
      "steps" : [ {
        "id" : "create_pairing_file",
        "run" : {
          "inputs" : [ {
            "id" : "pair",
            "type" : {
              "items" : {
                "fields" : {
                  "ID" : "string"
                },
                "type" : "record"
              },
              "type" : "array"
            }
          }, {
            "id" : "echoString",
            "type" : "string",
            "inputBinding" : {
              "position" : 1
            }
          }, {
            "id" : "output_filename",
            "type" : "string"
          } ],
          "outputs" : [ {
            "id" : "pairfile",
            "type" : "File",
            "outputBinding" : {
              "glob" : "random_stdout_d7cc55bc-3d77-442c-a2d8-6f5e26422311"
            }
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "InlineJavascriptRequirement"
          }, {
            "class" : "MultipleInputFeatureRequirement"
          }, {
            "class" : "DockerRequirement",
            "dockerPull" : "alpine:3.8"
          } ],
          "successCodes" : [ ],
          "stdout" : "$(inputs.output_filename)",
          "baseCommand" : [ "echo", "-e" ],
          "arguments" : [ ],
          "id" : "create_TN_pair",
          "class" : "CommandLineTool"
        },
        "in" : [ {
          "id" : "pair",
          "source" : "pair"
        }, {
          "id" : "echoString",
          "valueFrom" : "${ return inputs.pair[1].ID + \"\\t\" + inputs.pair[0].ID; }"
        }, {
          "id" : "output_filename",
          "valueFrom" : "${ return \"tn_pairing_file.txt\"; }"
        } ],
        "out" : [ {
          "id" : "pairfile"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "vcf2maf",
        "run" : {
          "cwlVersion" : "v1.0",
          "inputs" : [ {
            "id" : "cache_version",
            "default" : "86",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--cache-version"
            },
            "doc" : "Version of VEP and its cache to use"
          }, {
            "id" : "species",
            "default" : "homo_sapiens",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--species"
            },
            "doc" : "Species of variants in input"
          }, {
            "id" : "ncbi_build",
            "default" : "GRCh37",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--ncbi-build"
            },
            "doc" : "Genome build of variants in input"
          }, {
            "id" : "ref_fasta",
            "type" : [ "null", "File" ],
            "inputBinding" : {
              "prefix" : "--ref-fasta"
            },
            "doc" : "Reference FASTA file"
          }, {
            "id" : "maf_center",
            "default" : "mskcc.org",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--maf-center"
            },
            "doc" : "Variant calling center to report in MAF"
          }, {
            "id" : "output_maf",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--output-maf"
            },
            "doc" : "Path to output MAF file"
          }, {
            "id" : "max_filter_ac",
            "default" : 10,
            "type" : [ "null", "int" ],
            "inputBinding" : {
              "prefix" : "--max-filter-ac"
            },
            "doc" : "Use tag common_variant if the filter-vcf reports a subpopulation AC higher than this"
          }, {
            "id" : "min_hom_vaf",
            "default" : 0.7,
            "type" : [ "null", "float" ],
            "inputBinding" : {
              "prefix" : "--min-hom-vaf"
            },
            "doc" : "If GT undefined in VCF, minimum allele fraction to call a variant homozygous"
          }, {
            "id" : "remap_chain",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--remap-chain"
            },
            "doc" : "Chain file to remap variants to a different assembly before running VEP"
          }, {
            "id" : "normal_id",
            "default" : "NORMAL",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--normal-id"
            },
            "doc" : "Matched_Norm_Sample_Barcode to report in the MAF"
          }, {
            "id" : "buffer_size",
            "default" : 5000,
            "type" : [ "null", "int" ],
            "inputBinding" : {
              "prefix" : "--buffer-size"
            },
            "doc" : "Number of variants VEP loads at a time; Reduce this for low memory systems"
          }, {
            "id" : "custom_enst",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--custom-enst"
            },
            "doc" : "List of custom ENST IDs that override canonical selection"
          }, {
            "id" : "vcf_normal_id",
            "default" : "NORMAL",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--vcf-normal-id"
            },
            "doc" : "Matched normal ID used in VCFs genotype columns"
          }, {
            "id" : "vep_path",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--vep-path"
            },
            "doc" : "Folder containing variant_effect_predictor.pl or vep binary"
          }, {
            "id" : "vep_data",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--vep-data"
            },
            "doc" : "VEPs base cache/plugin directory"
          }, {
            "id" : "any_allele",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--any-allele"
            },
            "doc" : "When reporting co-located variants, allow mismatched variant alleles too"
          }, {
            "id" : "input_vcf",
            "type" : [ "string", "File" ],
            "inputBinding" : {
              "prefix" : "--input-vcf"
            },
            "doc" : "Path to input file in VCF format"
          }, {
            "id" : "vep_forks",
            "default" : 4,
            "type" : [ "null", "int" ],
            "inputBinding" : {
              "prefix" : "--vep-forks"
            },
            "doc" : "Number of forked processes to use when running VEP"
          }, {
            "id" : "vcf_tumor_id",
            "default" : "TUMOR",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--vcf-tumor-id"
            },
            "doc" : "Tumor sample ID used in VCFs genotype columns"
          }, {
            "id" : "tumor_id",
            "default" : "TUMOR",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--tumor-id"
            },
            "doc" : "Tumor_Sample_Barcode to report in the MAF"
          }, {
            "id" : "filter_vcf",
            "type" : [ "null", "string", "File" ],
            "inputBinding" : {
              "prefix" : "--filter-vcf"
            },
            "secondaryFiles" : [ ".tbi" ],
            "doc" : "The non-TCGA VCF from exac.broadinstitute.org"
          }, {
            "id" : "retain_info",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--retain-info"
            },
            "doc" : "Comma-delimited names of INFO fields to retain as extra columns in MAF"
          }, {
            "id" : "retain_fmt",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--retain-fmt"
            },
            "doc" : "Comma-delimited names of FORMAT fields to retain as extra columns in MAF []"
          } ],
          "outputs" : [ {
            "id" : "output",
            "type" : "File",
            "outputBinding" : {
              "glob" : "${\n  if (inputs.output_maf)\n    return inputs.output_maf;\n  return null;\n}\n"
            }
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "InlineJavascriptRequirement"
          }, {
            "class" : "ResourceRequirement",
            "ramMin" : 8000,
            "coresMin" : 2
          }, {
            "class" : "DockerRequirement",
            "dockerPull" : "mskcc/roslin-variant-vcf2maf:1.6.17"
          } ],
          "successCodes" : [ ],
          "baseCommand" : [ "perl", "/usr/bin/vcf2maf/vcf2maf.pl" ],
          "arguments" : [ {
            "prefix" : "--tmp-dir",
            "shellQuote" : false,
            "valueFrom" : "$(runtime.tmpdir)"
          } ],
          "doc" : "None\n",
          "label" : "vcf2maf",
          "class" : "CommandLineTool"
        },
        "in" : [ {
          "id" : "input_vcf",
          "source" : "annotate_vcf"
        }, {
          "id" : "tumor_id",
          "source" : "tumor_sample_name"
        }, {
          "id" : "vcf_tumor_id",
          "source" : "tumor_sample_name"
        }, {
          "id" : "normal_id",
          "source" : "normal_sample_name"
        }, {
          "id" : "vcf_normal_id",
          "source" : "normal_sample_name"
        }, {
          "id" : "ncbi_build",
          "source" : "genome"
        }, {
          "id" : "filter_vcf",
          "source" : "exac_filter"
        }, {
          "id" : "vep_data",
          "source" : "vep_data"
        }, {
          "id" : "ref_fasta",
          "source" : "ref_fasta"
        }, {
          "id" : "vep_path",
          "source" : "vep_path"
        }, {
          "id" : "custom_enst",
          "source" : "custom_enst"
        }, {
          "default" : "set,TYPE,FAILURE_REASON,MSI,MSILEN,SSF,LSEQ,RSEQ,STATUS,VSB",
          "id" : "retain_info"
        }, {
          "default" : "QUAL,BIAS,HIAF,PMEAN,PSTD,ALD,RD,NM,MQ,IS",
          "id" : "retain_fmt"
        }, {
          "id" : "output_maf",
          "valueFrom" : "${ return inputs.tumor_id + \".\" + inputs.normal_id + \".combined-variants.vep.maf\" }"
        } ],
        "out" : [ {
          "id" : "output"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "remove_variants",
        "run" : {
          "cwlVersion" : "v1.0",
          "inputs" : [ {
            "id" : "verbose",
            "default" : false,
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--verbose"
            },
            "doc" : "make lots of noise"
          }, {
            "id" : "inputMaf",
            "type" : [ "string", "File" ],
            "inputBinding" : {
              "prefix" : "--input-maf"
            },
            "doc" : "Input maf file which needs to be fixed"
          }, {
            "id" : "outputMaf",
            "type" : "string",
            "inputBinding" : {
              "prefix" : "--output-maf"
            },
            "doc" : "Output maf file name"
          }, {
            "id" : "outdir",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--outDir"
            },
            "doc" : "Full Path to the output dir."
          } ],
          "outputs" : [ {
            "id" : "maf",
            "type" : "File",
            "outputBinding" : {
              "glob" : "${\n  if (inputs.outputMaf )\n    return inputs.outputMaf;\n  return null;\n}\n"
            }
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "InlineJavascriptRequirement"
          }, {
            "class" : "ResourceRequirement",
            "ramMin" : 8000,
            "coresMin" : 1
          }, {
            "class" : "DockerRequirement",
            "dockerPull" : "mskcc/roslin-variant-remove-variants:0.1.1"
          } ],
          "successCodes" : [ ],
          "baseCommand" : [ "python", "/usr/bin/remove_variants.py" ],
          "arguments" : [ ],
          "doc" : "Remove snps/indels from the output maf where a complex variant is called\n",
          "id" : "remove-variants",
          "class" : "CommandLineTool"
        },
        "in" : [ {
          "id" : "inputMaf",
          "source" : "vcf2maf/output"
        }, {
          "id" : "outputMaf",
          "valueFrom" : "${ return inputs.inputMaf.basename.replace(\".vep.maf\", \".vep.rmv.maf\") }"
        } ],
        "out" : [ {
          "id" : "maf"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "fillout_tumor_normal",
        "run" : {
          "cwlVersion" : "v1.0",
          "inputs" : [ {
            "id" : "maf",
            "type" : "File",
            "inputBinding" : {
              "prefix" : "--maf"
            },
            "doc" : "MAF file on which to fillout"
          }, {
            "id" : "pairing",
            "type" : [ "null", "File" ],
            "inputBinding" : {
              "prefix" : "--pairing-file"
            },
            "doc" : "Tab separated pairing file, normal tumor"
          }, {
            "id" : "bams",
            "type" : {
              "items" : [ "string", "File" ],
              "type" : "array"
            },
            "inputBinding" : {
              "prefix" : "--bams"
            },
            "doc" : "BAM files to fillout with"
          }, {
            "id" : "ref_fasta",
            "type" : "File",
            "inputBinding" : {
              "prefix" : "--ref-fasta"
            },
            "doc" : "Reference assembly file of BAM files, e.g. hg19/grch37/b37"
          }, {
            "id" : "output",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--output"
            },
            "doc" : "Filename for output of raw fillout data in MAF/VCF format"
          }, {
            "id" : "portal_output",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--portal-output"
            },
            "doc" : "Filename for a portal-friendly output MAF"
          }, {
            "id" : "fillout",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--fillout"
            },
            "doc" : "Precomputed fillout file from GBCMS (using this skips GBCMS)"
          }, {
            "id" : "output_format",
            "type" : "string",
            "inputBinding" : {
              "prefix" : "--format"
            },
            "doc" : "Output format MAF(1) or tab-delimited with VCF based coordinates(2)"
          } ],
          "outputs" : [ {
            "id" : "fillout_out",
            "type" : "File",
            "outputBinding" : {
              "glob" : "${\n  if (inputs.output)\n    return inputs.output;\n  else\n    return inputs.maf.basename.replace(\".maf\", \".fillout\");\n}\n"
            }
          }, {
            "id" : "portal_fillout",
            "type" : "File",
            "outputBinding" : {
              "glob" : "${\n  if (inputs.portal_output)\n    return inputs.portal_output;\n  else\n    return inputs.maf.basename.replace(\".maf\", \".fillout.portal.maf\");\n}\n"
            }
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "InlineJavascriptRequirement"
          }, {
            "class" : "ResourceRequirement",
            "ramMin" : 48000,
            "coresMin" : 4
          }, {
            "class" : "DockerRequirement",
            "dockerPull" : "mskcc/roslin-variant-cmo-utils:1.9.15"
          } ],
          "successCodes" : [ ],
          "baseCommand" : [ "cmo_fillout" ],
          "arguments" : [ {
            "position" : 0,
            "prefix" : "--n_threads",
            "valueFrom" : "$(runtime.cores)"
          } ],
          "doc" : "Fillout allele counts for a MAF file using GetBaseCountsMultiSample on BAMs\n",
          "id" : "cmo-fillout",
          "class" : "CommandLineTool"
        },
        "in" : [ {
          "id" : "pairing",
          "source" : "create_pairing_file/pairfile"
        }, {
          "id" : "maf",
          "source" : "remove_variants/maf"
        }, {
          "id" : "bams",
          "source" : "bams"
        }, {
          "id" : "ref_fasta",
          "source" : "ref_fasta"
        }, {
          "default" : "1",
          "id" : "output_format"
        } ],
        "out" : [ {
          "id" : "fillout_out"
        }, {
          "id" : "portal_fillout"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "fillout_second",
        "run" : {
          "inputs" : [ {
            "id" : "maf",
            "type" : "File"
          }, {
            "id" : "ref_fasta",
            "type" : "File",
            "secondaryFiles" : [ ".amb", ".ann", ".bwt", ".pac", ".sa", ".fai", "^.dict" ]
          }, {
            "id" : "curated_bams",
            "type" : "File[]"
          } ],
          "outputs" : [ {
            "id" : "fillout_curated_bams",
            "type" : "File",
            "outputSource" : "fillout_curated_bams_step/fillout_out"
          } ],
          "hints" : [ ],
          "requirements" : [ ],
          "successCodes" : [ ],
          "steps" : [ {
            "id" : "fillout_curated_bams_step",
            "run" : {
              "cwlVersion" : "v1.0",
              "inputs" : [ {
                "id" : "maf",
                "type" : "File",
                "inputBinding" : {
                  "prefix" : "--maf"
                },
                "doc" : "MAF file on which to fillout"
              }, {
                "id" : "pairing",
                "type" : [ "null", "File" ],
                "inputBinding" : {
                  "prefix" : "--pairing-file"
                },
                "doc" : "Tab separated pairing file, normal tumor"
              }, {
                "id" : "bams",
                "type" : {
                  "items" : [ "string", "File" ],
                  "type" : "array"
                },
                "inputBinding" : {
                  "prefix" : "--bams"
                },
                "doc" : "BAM files to fillout with"
              }, {
                "id" : "ref_fasta",
                "type" : "File",
                "inputBinding" : {
                  "prefix" : "--ref-fasta"
                },
                "doc" : "Reference assembly file of BAM files, e.g. hg19/grch37/b37"
              }, {
                "id" : "output",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "prefix" : "--output"
                },
                "doc" : "Filename for output of raw fillout data in MAF/VCF format"
              }, {
                "id" : "portal_output",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "prefix" : "--portal-output"
                },
                "doc" : "Filename for a portal-friendly output MAF"
              }, {
                "id" : "fillout",
                "type" : [ "null", "string" ],
                "inputBinding" : {
                  "prefix" : "--fillout"
                },
                "doc" : "Precomputed fillout file from GBCMS (using this skips GBCMS)"
              }, {
                "id" : "output_format",
                "type" : "string",
                "inputBinding" : {
                  "prefix" : "--format"
                },
                "doc" : "Output format MAF(1) or tab-delimited with VCF based coordinates(2)"
              } ],
              "outputs" : [ {
                "id" : "fillout_out",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.output)\n    return inputs.output;\n  else\n    return inputs.maf.basename.replace(\".maf\", \".fillout\");\n}\n"
                }
              }, {
                "id" : "portal_fillout",
                "type" : "File",
                "outputBinding" : {
                  "glob" : "${\n  if (inputs.portal_output)\n    return inputs.portal_output;\n  else\n    return inputs.maf.basename.replace(\".maf\", \".fillout.portal.maf\");\n}\n"
                }
              } ],
              "hints" : [ ],
              "requirements" : [ {
                "class" : "InlineJavascriptRequirement"
              }, {
                "class" : "ResourceRequirement",
                "ramMin" : 48000,
                "coresMin" : 4
              }, {
                "class" : "DockerRequirement",
                "dockerPull" : "mskcc/roslin-variant-cmo-utils:1.9.15"
              } ],
              "successCodes" : [ ],
              "baseCommand" : [ "cmo_fillout" ],
              "arguments" : [ {
                "position" : 0,
                "prefix" : "--n_threads",
                "valueFrom" : "$(runtime.cores)"
              } ],
              "doc" : "Fillout allele counts for a MAF file using GetBaseCountsMultiSample on BAMs\n",
              "id" : "cmo-fillout",
              "class" : "CommandLineTool"
            },
            "in" : [ {
              "id" : "maf",
              "source" : "maf"
            }, {
              "id" : "bams",
              "source" : "curated_bams"
            }, {
              "id" : "ref_fasta",
              "source" : "ref_fasta"
            }, {
              "default" : "1",
              "id" : "output_format"
            }, {
              "id" : "output",
              "valueFrom" : "${ return inputs.maf.basename.replace(\".maf\", \".curated.fillout\"); }"
            } ],
            "out" : [ {
              "id" : "fillout_out"
            } ],
            "hints" : [ ],
            "requirements" : [ ]
          } ],
          "id" : "fillout_second",
          "class" : "Workflow"
        },
        "in" : [ {
          "id" : "maf",
          "source" : "fillout_tumor_normal/portal_fillout"
        }, {
          "id" : "ref_fasta",
          "source" : "ref_fasta"
        }, {
          "id" : "curated_bams",
          "source" : "curated_bams"
        } ],
        "out" : [ {
          "id" : "fillout_curated_bams"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      }, {
        "id" : "ngs_filters",
        "run" : {
          "cwlVersion" : "v1.0",
          "inputs" : [ {
            "id" : "verbose",
            "default" : false,
            "type" : [ "null", "boolean" ],
            "inputBinding" : {
              "prefix" : "--verbose"
            },
            "doc" : "make lots of noise"
          }, {
            "id" : "inputMaf",
            "type" : [ "File" ],
            "inputBinding" : {
              "prefix" : "--input-maf"
            },
            "doc" : "Input maf file which needs to be tagged"
          }, {
            "id" : "outputMaf",
            "type" : "string",
            "inputBinding" : {
              "prefix" : "--output-maf"
            },
            "doc" : "Output maf file name"
          }, {
            "id" : "NormalPanelMaf",
            "type" : [ "null", "string", "File" ],
            "inputBinding" : {
              "prefix" : "--normal-panel-maf"
            },
            "doc" : "Path to fillout maf file of panel of standard normals"
          }, {
            "id" : "NormalCohortMaf",
            "type" : [ "null", "string", "File" ],
            "inputBinding" : {
              "prefix" : "--normal-cohort-maf"
            },
            "doc" : "Path to fillout maf file of cohort normals"
          }, {
            "id" : "NormalCohortSamples",
            "type" : [ "null", "string" ],
            "inputBinding" : {
              "prefix" : "--normalSamplesFile"
            },
            "doc" : "File with list of normal samples"
          }, {
            "id" : "inputHSP",
            "type" : [ "null", "string", "File" ],
            "inputBinding" : {
              "prefix" : "--input-hotspot"
            },
            "doc" : "Input txt file which has hotspots"
          } ],
          "outputs" : [ {
            "id" : "output",
            "type" : "File",
            "outputBinding" : {
              "glob" : "${\n  if (inputs.outputMaf)\n    return inputs.outputMaf;\n  return null;\n}\n"
            }
          } ],
          "hints" : [ ],
          "requirements" : [ {
            "class" : "InlineJavascriptRequirement"
          }, {
            "class" : "ResourceRequirement",
            "ramMin" : 36000,
            "coresMin" : 1
          }, {
            "class" : "DockerRequirement",
            "dockerPull" : "mskcc/roslin-variant-ngs-filters:1.4"
          } ],
          "successCodes" : [ ],
          "baseCommand" : [ "python", "/usr/bin/ngs-filters/run_ngs-filters.py" ],
          "arguments" : [ ],
          "doc" : "This tool flags false-positive somatic calls in a given MAF file\n",
          "id" : "ngs-filters",
          "class" : "CommandLineTool"
        },
        "in" : [ {
          "id" : "tumor_sample_name",
          "source" : "tumor_sample_name"
        }, {
          "id" : "normal_sample_name",
          "source" : "normal_sample_name"
        }, {
          "id" : "inputMaf",
          "source" : "fillout_tumor_normal/portal_fillout"
        }, {
          "id" : "outputMaf",
          "valueFrom" : "${ return inputs.tumor_sample_name + \".\" + inputs.normal_sample_name + \".muts.maf\" }"
        }, {
          "id" : "NormalPanelMaf",
          "source" : "fillout_second/fillout_curated_bams"
        }, {
          "id" : "inputHSP",
          "source" : "hotspot_list"
        } ],
        "out" : [ {
          "id" : "output"
        } ],
        "hints" : [ ],
        "requirements" : [ ]
      } ],
      "id" : "maf-processing-pair",
      "class" : "Workflow"
    },
    "in" : [ {
      "id" : "runparams",
      "source" : "runparams"
    }, {
      "id" : "db_files",
      "source" : "db_files"
    }, {
      "id" : "bams",
      "source" : "alignment/bams"
    }, {
      "id" : "annotate_vcf",
      "source" : "variant_calling/annotate_vcf"
    }, {
      "id" : "pair",
      "source" : "pair"
    }, {
      "id" : "genome",
      "valueFrom" : "${ return inputs.runparams.genome }"
    }, {
      "id" : "ref_fasta",
      "source" : "ref_fasta"
    }, {
      "id" : "vep_path",
      "valueFrom" : "${ return inputs.db_files.vep_path }"
    }, {
      "id" : "custom_enst",
      "valueFrom" : "${ return inputs.db_files.custom_enst }"
    }, {
      "id" : "exac_filter",
      "source" : "exac_filter"
    }, {
      "id" : "vep_data",
      "valueFrom" : "${ return inputs.db_files.vep_data }"
    }, {
      "id" : "normal_sample_name",
      "valueFrom" : "${ return inputs.pair[1].ID; }"
    }, {
      "id" : "tumor_sample_name",
      "valueFrom" : "${ return inputs.pair[0].ID; }"
    }, {
      "id" : "curated_bams",
      "source" : "curated_bams"
    }, {
      "id" : "hotspot_list",
      "valueFrom" : "${ return inputs.db_files.hotspot_list }"
    } ],
    "out" : [ {
      "id" : "maf"
    }, {
      "id" : "portal_fillout"
    } ],
    "hints" : [ ],
    "requirements" : [ ]
  } ],
  "id" : "pair-workflow",
  "class" : "Workflow"
}
