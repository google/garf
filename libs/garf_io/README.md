# `garf-io` - Writing GarfReport to anywhere

`garf-io` handles reading queries and writing `GarfReport` to various local/remote storages.

Currently it supports writing data to the following destination:

* Console
* Local file
    * CSV
    * Json
* Remote file
    * CSV
    * Json
* Databases:
    * BigQuery
    * Any DB supported by SqlAlchemy
* Google Sheets
