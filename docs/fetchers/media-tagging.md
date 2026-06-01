## garf for Media Tagging API

[![PyPI](https://img.shields.io/pypi/v/garf-media-tagging?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-media-tagging)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-media-tagging?logo=pypi)](https://pypi.org/project/garf-media-tagging/)

`garf-media-tagging` simplifies interaction with [media_tagging](https://google.github.io/filonov/tagging/overview/) library  via
SQL queries and can be used with [garf](https://google.github.io/garf/) framework.


## Prerequisites

* [media_tagging](https://google.github.io/filonov/tagging/overview/) library installed locally
  or running as a HTTP service.

## Installation

`pip install garf-media-tagging`

## Usage

### Run via CLI

> Install `garf-executors` package to run queries via CLI (`pip install garf-executors`).

```
garf <PATH_TO_QUERIES> --source media-tagging \
  --output <OUTPUT_TYPE> \
  --source.endpoint=MEDIA_TAGGING_API_ENDPOINT_URL
```

where:

* `PATH_TO_QUERIES` - local or remove files containing queries
* `output` - output supported by [`garf-io` library](https://google.github.io/garf/usage/writers/).
* `SOURCE_PARAMETER=VALUE` - key-value pairs to refine fetching, check [available source parameters](#available-source-parameters).

###  Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `endpoint`   | http endpoint when media-tagging API is running |  |
| `db-uri`   | Optional connection string to DB where tagging results can be found |  |


## Queries for Media Tagging API

```sql
SELECT
  media_url,
  content.tags[].name AS tags
FROM tag
WHERE
  media_type = 'image'
  AND tagger_type = 'gemini'
  AND media_path IN ({{media}})
```

### Resources

* `tag` - identifies tags (pair `name: score`) uniquely defining media.
* `description` - custom description of media; usually fine-tuned via `custom_prompt` parameter.


## Filters

* `media_type` - Required, one of: IMAGE, YOUTUBE_VIDEO, WEBPAGE, TEXT, VIDEO.
* `tagger_type` - Tagger used to identify tags / descriptions.
* `media_path` - location of media.
* `tagging_options` - optional parameters to fine-tune tagging.
  * `n_tags` - number of tags to return.
  * `tags` - custom tags to find in the media.
  * `custom_prompt` - prompt to send to LLM.
  * `custom_schema` - schema for structured output.

### Fields

You can extract one of the following elements from reach row of API response.

* `media_type`
* `media_url`
* `identifier`
* `processed_at`
* `content`
    * `text` for description
    * `{name, score}` for tag
* `hash`
