# Example queries for `garf-youtube-reporting-api`

To execute the queries you may run them in Python (check [Usage](../README.md#usage))
or use `garf-executors` package (install with `pip install garf-executors`).

* [channel_statistics](video_statistics.sql) - Gets views for owned channel for the last 30 days.
  ```
  garf video_statistics.sql \
    --source youtube-reporting-api --output console \
    --macros.start_date=:YYYYMMDD-30 \
    --macros.start_date=:YYYYMMDD-1
  ```

* [video_retention](video_retention.sql) - Gets retention for a single video for the last 30 days.
  garf video_retention.sql \
    --source youtube-reporting-api --output console \
    --macros.video_id=<YOUR_VIDEO_ID_HERE> \
    --macros.start_date=:YYYYMMDD-30 \
    --macros.start_date=:YYYYMMDD-1
