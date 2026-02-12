# Overview

`garf-executors` and community libraries provide `ReportFetcher` implementations to fetch data from various APIs.

| CLI identifier | Fetcher Class | Library | Options |
| :--- | :--- | :--- | :--- |
| [`bid-manager`](bid-manager.md) | `BidManagerApiReportFetcher` | `garf-bid-manager` | `credentials_file`, `auth_mode` |
| [`google-ads`](google-ads.md) | `GoogleAdsApiReportFetcher` | `garf-google-ads` | `account`, `path-to-config`, `expand-mcc`, `customer-ids-query`, `version` |
| [`google-analytics`](google-analytics-api.md) | `GoogleAnalyticsApiReportFetcher` | `garf-google-analytics` | `property_id` |
| [`merchant-api`](merchant-center-api.md) | `MerchantApiReportFetcher` | `garf-merchant-api` | `account` |
| [`rest`](rest.md) | `RestApiReportFetcher` | `garf-core` | `endpoint`, `apikey` |
| [`search-ads-360`](google-ads.md#search-ads-360) | `SearchAds360ApiReportFetcher` | `garf-google-ads[search-ads-360]` | `account`, `path-to-config`, `expand-mcc`, `customer-ids-query` |
| [`youtube-analytics`](youtube.md#youtube-analytics-api) | `YouTubeAnalyticsApiReportFetcher` | `garf-youtube` | |
| [`youtube-data-api`](youtube.md#youtube-data-api) | `YouTubeDataApiReportFetcher` | `garf-youtube` | `id`, `forHandle`, `forUsername`, `regionCode`, `chart`, `videoId` |
