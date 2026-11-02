# pMaximizer workflow

Ports [pMaximizer](https://github.com/google-marketing-solutions/pmax_best_practices_dashboard) to garf workflow.

## Requirements

Install the following libraries:

* `garf-google-ads`
* `garf-executors[bq]`

## Running

1. Create `config.yaml`

```yaml
name: config_name
metadata:
  version: '0.0.0'
global_parameters:
  query_parameters:
    macro_expansion: True
    macro:
      start_date: :YYYYMMDD-90
      end_date: :YYYYMMDD-1
      bq_dataset: BQ_DATASET_NAME  # Optional; pmax_ads by default
  writer_parameters:
    project: mena-youtube-reach-planner
    dataset: BQ_DATASET_NAME  # same as in macro.bq_dataset
sources:
  google-ads:
    fetcher_parameters:
      account:
        - GOOGLE_ADS_ACCOUNT_OR_MCC
  bq: {}
```

2. Fetch data

```bash
grf workflow run -f workflow.yaml -c config.yaml
```

## Customization

By default the retail version of pMaximizer will be generated; if you want to
opt-out of generating retain specific section run the following command:

```bash
grf workflow run -f workflow.yaml -c config.yaml --exclude shopping*
```
