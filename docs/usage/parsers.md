# API Response parsers

Once ApiClient returns response from an API it's Parser's job to convert it to
the format consumable by `GarfReport`.

## Built-in parsers

* `DictParser` - return an element from API following the attribute path.
* `NumericConverterDictParser` - subclass of `DictParser` but tries to convert strings to int/float if possible.

!!! important
    If Parser fails to find an element if returns `None`.

## Create parsers

If response from your API is in the format not supported by built-in parsers you
can build you own parser.

Please refer to [development docs](../development/create-api-response-parser.md) to learn more.
