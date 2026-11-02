# Stamp

Ports [Search Term Amp](https://github.com/google-marketing-solutions/search_term_amp) fetching part to garf workflow.


## Requirements

Install the following libraries:

* `garf-google-ads`
* `garf-executors[duckdb]`

## Running

1. Create `config.yaml`

```yaml
name: CLIENT_NAME
metadata:
  version: '0.0.0'
sources:
  google-ads:
    query_parameters:
      template:
        start_date: :YYYYMMDD-30
        end_date: :YYYYMMDD-1
    fetcher_parameters:
      account:
        - GOOGLE_ADS_ACCOUNT_OR_MCC
  duckdb:
    writer_parameters:
      suffix: CLIENT_NAME

```

2. Fetch data

```bash
grf workflow run -f workflow.yaml -c config.yaml
```
