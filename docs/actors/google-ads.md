## garf actors for Google Ads

[![PyPI](https://img.shields.io/pypi/v/garf-google-ads?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/garf-google-ads)
[![Downloads PyPI](https://img.shields.io/pypi/dw/garf-google-ads?logo=pypi)](https://pypi.org/project/garf-google-ads/)

Modifies entities via [Google Ads API](https://developers.google.com/google-ads-api).

## Install

Install `garf-google-ads` library

/// tab | pip
```
pip install garf-actors garf-google-ads
```
///

/// tab | uv
```
uv pip install garf-actors garf-google-ads
```
///

## Prerequisites

* [Google Ads API](https://console.cloud.google.com/apis/library/googleads.googleapis.com) enabled.
* `google-ads.yaml` file


## Actors

`garf-google-ads` contains a set of specific actors to modify campaigns,
ad groups and targeting criteria.

### Labeler

`Labeler` either adds new labels to the account or assigns then to various
entities (Customer, Campaign, AdGroup, AdGroupAd, AdGroupCriterion).


To add new labels, provide `new_labels` variable (either as a list or
comma-separated values) to `Labeler`.

!!! important
    If provider labels not found, they will be automatically created before
    the assignment.

### Adder

`Adder` allows one to add new entities to Google Ads such as Keywords, Sitelinks,
Assets *without* actually assigning it to the campaign / ad_group /etc.

Actual variables passed to `Adder` varies by the type of the entity being added:

* `Keyword` - `keyword`, `match_type`
* `Text` asset - `text`
* `Video` asset - `video_id`, `title`
* `Sitelink` - `sitelink`, `url`, `description1`, `description2`


### StatusChanger

`StatusChanger` update the status of campaign / ad_group / keyword.


To update status pass `status` variable (takes one of values - `ENABLE`, `PAUSE`, `DELETE`)

### BudgetChanger


`BudgetChanger` allows to increase of decrease existing campaign budget via the
following variables:

* `budget_change` - ratio for changing budget. `-0.5` decreasing the budget by 50%, while `0.1` increases by 10%.
* `max_delta` - (optional) maximum absolute change of the budget.

### Excluder

`Excluder` adds negative criteria (placements, keywords) to ad groups.

## Workflows

`garf-google-ads` contains a set of built-in
[workflows](../usage/actors.md#evaluation-workflow) to simplify getting data
from Google Ads.

### ad_group_performance

Workflow fetches such metrics as `clicks`, `impressions`, `cost` and `conversions` for each ad_group for the last 30 days.

Available parameters:

  * `metrics`
  * `campaign_types`
  * `start_date`
  * `end_date`

### campaign_performance

Workflow fetches such metrics as `clicks`, `impressions`, `cost` and `conversions` for each campaign for the last 30 days.

Available parameters:

  * `metrics`
  * `campaign_types`
  * `start_date`
  * `end_date`

### budgets

Workflow fetches allocated campaign budgets alongside such metrics as `clicks`, `impressions`, `cost` and `conversions` for the last 30 days.

Available parameters:

  * `metrics`
  * `campaign_types`
  * `start_date`
  * `end_date`

### keywords

Workflow fetches ad group level keywords alongside such metrics as `clicks`, `impressions`, `cost` and `conversions` for the last 30 days.

Available parameters:

  * `metrics`
  * `start_date`
  * `end_date`

### labels

Workflow fetches enabled labels available for each account.

### placements

Workflow fetches ad group level placement when ads were shown alongside such metrics as `clicks`, `impressions`, `cost` and `conversions` for the last 30 days.

Available parameters:

  * `metrics`
  * `start_date`
  * `end_date`
  * `campaign_types`
  * `placement_types`

### search_terms

Workflow fetches ad group level search terms alongside such metrics as `clicks`, `impressions`, `cost` and `conversions` for the last 30 days.

Available parameters:

  * `metrics`
  * `start_date`
  * `end_date`
