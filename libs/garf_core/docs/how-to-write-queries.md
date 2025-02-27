# How to write queries

## Table of content

 - [Intro](#intro)
 - [Elements](#elements)
   - [Aliases](#aliases)
   - [Nested Resources](#nested-resources)
   - [Resource Indices](#resource-indices)
   - [Virtual Columns](#virtual-columns)
 - [Macros](#macros)
   - [Macros in virtual columns](#macros-in-virtual-columns)
   - [Common macros](#common-macros)
 - [Templates](#templates)


## Intro
`garf-core` uses SQL-like syntax to write queries.


This is how a generic query might look like:

```
SELECT
  ad_group.id,
  ad_group.name
FROM ad_group
```

When running this query and saving the results we get pretty long and unreadable
column names - `ad_group.id` and `ad_group.name`.

Things might be more complicated if you want to extract and save such objects
as unselectable elements, complex messages and resource names.

In order to simplify data extraction and processing when querying data from API
we introduce additional syntax (see an example below):

```
SELECT
    resource.attribute AS column_name_1,
    resource.attribute:nested.resource AS column_name_3
    resource.attribute~1 AS column_name_4
FROM resource
```

## Elements

* Aliases (`AS column_name`)
* Nested resources (`:nested.resource.name`)
* Resource indices (`~position`)
* Virtual columns (`metric.name / metric.name_2 AS alias`)

### Aliases

Alias is used to give a descriptive name to a metric or attribute fetched from
API when saving data. So instead of column name
`campaign.app_campaign_setting.bidding_strategy_goal_type` you may use something
more user friendly, like `bidding_type`.

Aliases are specified using `AS` keyword as shown below:

```
SELECT
    campaign.app_campaign_setting.bidding_strategy_goal_type AS bidding_type
FROM campaign
```

### Nested Resources

Some fields return structs, and if you want to get a nested attribute scalar value you can use nested resource selectors.
One particular example is working with `change_event` - `change_event.new_resource`
consists of various changes made to an entity and looks something like that:

```
new_resource {
    campaign {
        target_cpa {
            target_cpa_micros: 1000000
        }
    }
}
```

In order to extract a particular element (i.e., final value for `target_cpa_micros`)
we use the `:` syntax - `change_event.new_resource:campaign.target_cpa.target_cpas_micros`:

```
SELECT
    change_event.old_resource:campaign.target_cpa.target_cpa_micros AS old_target_cpa,
    change_event.new_resource:campaign.target_cpa.target_cpa_micros AS new_target_cpa
FROM change_event
```

### Resource Indices

Resource indices are used to extract a particular element from data type
*RESOURCE_NAME*. I.e., if we want to get resource name for `campaign_audience_view.resource_name`
and save it somewhere, the saved result will contain a string *customers/{customer_id}/campaignAudienceViews/{campaign_id}~{criterion_id}*.
Usually we want to get only the last element from (`criterion_id`) and
it can be extracted with `~N` syntax  where *N* is a position of an element you want to extract
(indexing is starting from 0).

If the resource you're selecting looks like this `customers/111/campaignAudienceViews/222~333`
you can specify `campaign_audience_view.resource_name~1` to extract the second element (`333`).
If you specify `campaign_audience_view.resource_name~0` you'll get '222' (the last resource id before ~).

```
SELECT
    campaign_audience_view.resource_name~1 AS criterion_id
FROM campaign_audience_view
```

### Virtual Columns

Virtual columns allow to specify in a query some fields or expressions that are not present natively in API.

```
SELECT
    1 AS counter,
    metrics.clicks / metrics.impressions AS ctr,
    metrics.cost_micros * 1e6 AS cost,
    campaign.app_campaign_setting.bidding_strategy_goal_type AS bidding_type
FROM campaign
```

Virtual columns can contain constants (i.e. `1 AS counter` will add new column `counter` filled with `1`) or expressions.
Expressions can contain field selectors, constants and any arithmetics operations with them.
For example `metrics.clicks / metrics.impressions AS ctr` will calculate `metrics.clicks / metrics.impressions` for each row of API response and store the results in a new column `ctr`.
For this the fields `metrics.clicks` and `metrics.impressions` will be fetched implicitly.
Or for example `campaign.target_cpa.target_cpa_micros / 1000000 AS target_cpa` expression will fetch `campaign.target_cpa.target_cpa_micros` field but return the result of its division by 1000000.

The query parser parses a query and remove all columns which are not simple field accessors (i.e. contains anything except field names).
For constants columns they will be re-added into result after executing the query. For more complex columns with expressions (i.e. some operations with fields) the result will evaluated using the response from an API.


## Macros

You queries can contain macros.
Macro is just a substitution in script text, i.e.

```
SELECT
    campaign.id AS campaign_id,
    metrics.clicks AS clicks
FROM campaign
WHERE
    segments.date BETWEEN "{start_date}" AND "{end_date}"
```

### Macros in virtual columns

Macros can be used not only in WHERE statements as in the example above but also in the SELECT statement.
In that case this macros will be expanded and then treated as a virtual column.

```
SELECT
    "{current_date}" AS date,
    campaign.id AS campaign_id,
    campaign_budget.budget_amount_micros AS budget
FROM campaign
```

This will return all campaign budgets and attach current date (i.e. 2023-06-01) as a date column in the output.

### Common macros

`gaarf` by default has several common macros:

* `date_iso` - current date in YYYYMMDD format (i.e. *19700101*)
* `yesterday_iso` - previous day date in YYYY-MM-DD format (i.e. *19700101*)
* `current_date` - current_date in YYYY-MM-DD format (i.e. *1970-01-01*)
* `current_datetime` - current datetime in YYYY-MM-DD HH:mm-ss format (i.e. *1970-01-01 00:00:00*)

## Templates

Your SQL scripts can be templates using [Jinja](https://jinja.palletsprojects.com) template engine.
Inside templates you can use appropriate syntax and control structures of Jinja.

```
SELECT
  customer_id AS
  {% if level == "0"  %}
  root_account_id
  {% else %}
  leaf_account_id
  {% endif %}
FROM dataset1.table1
```

This will create a column named either `root_account_id` since the specified level is 0.

Template are great when you need to create multiple column based on condition:

```
SELECT
    {% for day in cohort_days %}
        SUM(GetCohort(lag_data.installs, {{day}})) AS installs_{{day}}_day,
    {% endfor %}
FROM asset_performance
```

Please note that all values passed through CLI arguments are strings. But there's a special case - a value containing "," - it's converted to an array.
It will create 4 columns (named `installs_0_day`, `installs_1_day`, etc).
