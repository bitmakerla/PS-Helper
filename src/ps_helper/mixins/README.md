# AutoInputMixin for Scrapy Spiders

## Overview
The **AutoInputMixin** is designed to simplify how Scrapy spiders receive and validate input data.  
It supports automatic assignment of input from different sources (CLI arguments, JSON files, or Google Sheets).

------------------------------------------------------------------------

## Installation

```bash
pip install ps-helper
```

(or clone this repository if you’re testing locally).

------------------------------------------------------------------------

## Usage

This mixin supports three primary input methods:

### 1. Command Line Argument (`input`)

```bash
scrapy crawl my_spider -a input='[{"url": "https://example.com"}, {"url": "https://scrapy.org"}]'
```

------------------------------------------------------------------------

### 2. JSON File (`input_file`)

```bash
scrapy crawl my_spider -a input_file='input.json'
```

Example `input.json`:

```json
[
  {"url": "https://example.com"},
  {"url": "https://scrapy.org"}
]
```

------------------------------------------------------------------------

### 3. Google Sheets (`input_sheet`)

```bash
scrapy crawl my_spider -a input_sheet='https://docs.google.com/spreadsheets/d/your_sheet_id_here'
```

Make sure your Google Sheet is shared with the setting **“Anyone with the link can view”**.

------------------------------------------------------------------------

## Example Spider

```python
import scrapy
from scrapy.spiders import Spider
from ps_helper.mixins.input_mixin import AutoInputMixin


input_schema = {
    'ID': {
        'type': 'string',
        'required': True,
    },
    'Price': {
        'type': 'string',
        'required': False,
    },
    'Name': {
        'type': 'string',
        'required': False,
    }
}

class MyCustomSpider(AutoInputMixin, Spider):
    name = 'example_spider'
    # input_schema = input_schema
    input_schema = None

    def parse(self, response):
        pass

    def closed(self, reason):
        if isinstance(self.input, list):
            for i, product in enumerate(self.input, start=1):
                print(f"--- Product {i} ---")
                for key, value in product.items():
                    print(f"{key} = {value}")
        elif isinstance(self.input, dict):
            print("--- Single Product ---")
            for key, value in self.input.items():
                print(f"{key} = {value}")
        else:
            print("Unsupported input format:", type(self.input))

```

---

## Running the Spider

### Using JSON input directly:

```bash
scrapy crawl example_spider -a input='{"ID": "value1", "Price": "value2", "Name": "value3"}'
```

```bash
scrapy crawl example_spider -a input='[{"ID": "value1", "Price": "value2", "Name": "value3"}]'
```

### Using a JSON file:

```bash
scrapy crawl my_spider -a input_file='input.json'
```

**Example input file**

```json
[
    {"ID": "4", "Name": "Product 4", "Price": "400"},
    {"ID": "5", "Name": "Product 5", "Price": "500"}
]
```


### Using a Google Sheet:

```bash
scrapy crawl my_spider -a input_sheet='https://docs.google.com/spreadsheets/d/your_sheet_id_here'
```

**Example input sheet**

| ID | Name       | Price |
|----|------------|-------|
| 4  | Product 4  | 400   |
| 5  | Product 5  | 500   |

------------------------------------------------------------------------

## Notes
- Input is automatically parsed and stored in `self.input`.
- Optional: You can integrate validation with [Cerberus](https://docs.python-cerberus.org/en/stable/) if your input requires strict schema checks.
