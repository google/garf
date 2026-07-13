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
* `output` - output supported by [`garf-io` library](../usage/writers.md).
* `SOURCE_PARAMETER=VALUE` - key-value pairs to refine fetching, check [available source parameters](#available-source-parameters).

###  Available source parameters

| name | values| comments |
|----- | ----- | -------- |
| `endpoint`   | http endpoint when media-tagging API is running |  |
| `db-uri`   | Optional connection string to DB where tagging results can be found |  |
| `tagger-type`*  | Type of [tagger](https://google.github.io/filonov/tagging/overview/#supported-taggers) to use | `media-tagging.tagger-type=gemini` |
| `media-type`* | Type of [media](https://google.github.io/filonov/tagging/media/#supported-media-types) to use |  `media-tagging.media-type=text` |
| `media-paths`*  | Media to tag | `--media-tagging.media_paths='Some text'`. Can use [`gquery` expansion](../usage/executors.md/#gquery-expansion) to get data from a table |
| `tagging-options`*  | Key-value pairs  to [fine-tune tagging process](https://google.github.io/filonov/tagging/overview/#usage) | `--media-tagging.tagging-options.custom-prompt='Is this an advertising?`. |

!!! note
    Source parameters marked with asterix (*) are optional and can be provided in a query filters.

## Queries for Media Tagging API

```sql
SELECT
  media_url,
  content AS tags
FROM tag
WHERE
  media_type = 'image'
  AND tagger_type = 'gemini'
  AND media_paths IN ({{media}})
```

### Resources

* `tag` - identifies tags (pair `name: score`) uniquely defining media.
* `description` - custom description of media; usually fine-tuned via `custom_prompt` parameter.


## Filters

* `media_type` - Required, one of: IMAGE, YOUTUBE_VIDEO, WEBPAGE, TEXT, VIDEO.
* `tagger_type` - Tagger used to identify tags / descriptions.
* `media_paths` - location of media.
* `tagging_options` - optional parameters to fine-tune tagging.
  * `n_tags` - number of tags to return.
  * `tags` - custom tags to find in the media.
  * `custom_prompt` - prompt to send to LLM.
  * `custom_schema` - schema for [structured output](https://ai.google.dev/gemini-api/docs/structured-output).
    Supports several [built-in schemas](#built-in-schemas).

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

## Custom schemas

### Built-in schemas

Instead of specifying a schema verbosely you can use a couple of built-in schemas:


/// tab | string

Used for returning text.

```sql
SELECT
  media_url,
  content.text AS description
FROM description
WHERE
  media_type = 'image'
  AND tagger_type = 'gemini'
  AND media_paths IN ({{media}})
  AND tagging_options.custom_prompt='What is this image about?'
  AND tagging_options.custom_schema='string'
```
///

/// tab | number

Returns floating-point numbers.

```sql
SELECT
  media_url,
  content.text AS share_of_green
FROM description
WHERE
  media_type = 'image'
  AND tagger_type = 'gemini'
  AND media_paths IN ({{media}})
  AND tagging_options.custom_prompt='What is the share of green in this image?'
  AND tagging_options.custom_schema='number'
```
///

/// tab | integer

Returns integers.

```sql
SELECT
  media_url,
  content.text AS image_quality
FROM description
WHERE
  media_type = 'image'
  AND tagger_type = 'gemini'
  AND media_paths IN ({{media}})
  AND tagging_options.custom_prompt='Rate quality of this image from 1 to 5.'
  AND tagging_options.custom_schema='integer'
```
///

/// tab | boolean

Returns True/False

```sql
SELECT
  media_url,
  content.text AS is_advertising
FROM description
WHERE
  media_type = 'image'
  AND tagger_type = 'gemini'
  AND media_paths IN ({{media}})
  AND tagging_options.custom_prompt='Is this image advertising?'
  AND tagging_options.custom_schema='boolean'
```
///

/// tab | enum

 Returns value from a specific set of possible strings for classification tasks.

```sql
SELECT
  media_url,
  content.text AS category
FROM description
WHERE
  media_type = 'image'
  AND tagger_type = 'gemini'
  AND media_paths IN ({{media}})
  AND tagging_options.custom_prompt='Classify this image into one of the categories.'
  AND tagging_options.custom_schema='enum:Category1,Category2'
```
///


### Full schema specification

If built-in schema is not enough you can specify the directly in the query:

```sql
SELECT
  media_url,
  content.text[0].quality_score AS score,
  content.text[0].reason AS reason
FROM description
WHERE
  media_type = 'image'
  AND tagger_type = 'gemini'
  AND media_paths IN ({{media}})
  AND tagging_options.custom_prompt='Rate this image quality and explain why.'
  AND tagging_options.custom_schema = {{
    {
      "type": "object",
      "properties": {
          "quality_score": {"type": "integer",
          "description":
            "Number from 1 to 5 where 1 means the poorest quality and 5 is the highest"
          },
          "reason": {"type": "string", "description": "Reason for assigning a particular score."}
      }
    }
  }}
```
