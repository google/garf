# Installing garf


## Create and activate virtual environment

```
python -m venv .venv
source .venv/bin/activate
```

## Install garf libraries

```
pip install garf-executors
```


## Extras

* Install with support for BQ
```
pip install garf-executors[bq]
```

* Install with support for SqlAlchemy
```
pip install garf-executors[sql]
```

* Install with support for FastAPI endpoint
```
pip install garf-executors[server]
```

* Install everything
```
pip install garf-executors[all]
```
