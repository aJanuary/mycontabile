# mycontabile

Generates a static HTML schedule for a UK Filk convention from a CSV.
The resulting schedule can be hosted on any static file hosting service.

## Requirements

- [uv](https://docs.astral.sh/uv/)

## Generating a schedule

`uv run generate <convention name> <csv file> <logo> <destination folder>`

**convention name**: Name of the convention. Will be used in the page title.

**csv file**: Path to the CSV file containing the programme items.
See [CSV format](#csv-format) for details on the contents.

**logo**: Path to an image to use as the logo. Will be used in the favicon and
app icon. Should be square, and at least 180 x 180 pixels. Can be any format
listed on
https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html

**destination folder**: Folder to write the generated output to. The folder will
be deleted and recreated if it already exists.

## CSV format

The CSV must have the following headings in the first row:

```
ID,Start,End,Title,Room,Start label,End label
```

### ID

Used to keep track of what people have favourited. Even if you change the title
of an item, or the ID has a spelling mistake in it, you should keep the ID the
same, otherwise it will "forget" that people have favourited it.

Required. Must be letters, numbers, dashes or underscores. Each ID must be
unique.

### Start

The start date and time of the programme item.

Required. Should be `yyyy-mm-dd hh:mm` or `dd/mm/yyyy hh:mm`.

### End

The end date and time of the programme item.

Required. Should be `yyyy-mm-dd hh:mm` or `dd/mm/yyyy hh:mm`.

### Title

Title of the programme item.

Required. Does not need to be unique.

### Room

Room the programme item is in.

Required.

### Start label

Label to display for the start time.

By default the start time will be displayed as hh:mm using the 24-hour clock.
This field can be used to override that with something like "early" or "noon".

Optional.

### End label

Label to display for the end time.

By default the end time will be displayed as hh:mm using the 24-hour clock.
This field can be used to override that with something like "late".

Optional.

## Development

### Formatting

`uv run ruff format`
