# Example queries for `garf-youtube-data-api`

To execute the queries you may run them in Python (check [Usage](../README.md#usage))
or use `garf-executors` package (install with `pip install garf-executors`).

## Videos
* [video_statistics](video_statistics.sql) - Gets all statistics (like, comments, views, etc.) for provided video ids
  ```
  garf video_statistics.sql \
    --source youtube-data-api --output console --source.ids=video_id1,video_id2
  ```
* [video_info](video_info.sql) - Gets all info (title,description, upload_date) for provided video ids
  ```
  garf video_info.sql \
    --source youtube-data-api --output console --source.ids=video_id1,video_id2
  ```
## Channels
> You can use `--source.forHandle=@handleName` or `--source.forUsername=channelName` for fetch data based on channel names instead of channel_ids.

* [channel_statistics](channel_statistics.sql) - Gets all statistics (subscribers, videos) for provided channel ids
  ```
  garf channel_statistics.sql \
  --source youtube-data-api --output console --source.ids=channel_id1,channel_id2
  ```

* [channel_info](channel_info.sql) - Gets all info (title, description, topics) for provided channel ids
  ```
  garf channel_info.sql \
  --source youtube-data-api --output console --source.ids=channel_id1,channel_id2
  ```
