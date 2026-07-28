# garf-media-tagging examples


## Tags

```bash
grf execute tags.sql --source media-tagging \
  --media-tagging.tagger-type=gemini \
  --media-tagging.media-type=TEXT \
  --media-tagging.media_paths='The quick brown fox jumps over the lazy dog' \
  --media-tagging.tagging-options.custom-prompt='Find animals in the text.'
```

## Description

```bash
grf execute description.sql --source media-tagging \
  --media-tagging.tagger-type=gemini \
  --media-tagging.media-type=TEXT \
  --media-tagging.media_paths='Download garf-media-tagging now!' \
  --media-tagging.tagging-options.custom-prompt='Is there a call to action in the text.' \
  --media-tagging.tagging-options.custom-schema='boolean'
```
