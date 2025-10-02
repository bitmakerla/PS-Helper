import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import json
from pathlib import Path

svg_icons = {
    "performance": """<svg width="70" height="70" viewBox="0 0 70 70" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M39.375 37.9167L49.5834 26.25M40.8334 43.75C40.8334 46.9718 38.2218 49.5833 35 49.5833C31.7783 49.5833 29.1667 46.9718 29.1667 43.75C29.1667 40.5283 31.7783 37.9167 35 37.9167C38.2218 37.9167 40.8334 40.5283 40.8334 43.75Z" stroke="#FF5733" stroke-width="3" stroke-linecap="round"/>
<path d="M17.5 35C17.5 25.335 25.335 17.5 35 17.5C38.1876 17.5 41.176 18.3522 43.75 19.8412" stroke="#FF5733" stroke-width="3" stroke-linecap="round"/>
<path d="M7.29169 35C7.29169 21.9381 7.29169 15.4072 11.3495 11.3494C15.4073 7.29163 21.9382 7.29163 35 7.29163C48.0617 7.29163 54.5927 7.29163 58.6507 11.3494C62.7084 15.4072 62.7084 21.9381 62.7084 35C62.7084 48.0617 62.7084 54.5927 58.6507 58.6506C54.5927 62.7083 48.0617 62.7083 35 62.7083C21.9382 62.7083 15.4073 62.7083 11.3495 58.6506C7.29169 54.5927 7.29169 48.0617 7.29169 35Z" stroke="#FF5733" stroke-width="3"/>
</svg>""",
    "http": """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" stroke="#1e3a8a" stroke-width="2" fill="none"/>
        <path d="M8 12h8M12 8v8" stroke="#1e3a8a" stroke-width="2" stroke-linecap="round"/>
    </svg>""",
    "monitoring": """<svg width="70" height="70" viewBox="0 0 70 70" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M64.1666 34.6792V37.275C64.1666 47.6583 61.5708 50.225 51.2166 50.225H18.7833C8.42915 50.225 5.83331 47.6292 5.83331 37.275V18.7833C5.83331 8.42918 8.42915 5.83334 18.7833 5.83334H23.3333" stroke="#F8623D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path opacity="0.4" d="M35 50.2256V64.1673" stroke="#F8623D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path opacity="0.4" d="M5.83331 37.9167H64.1666" stroke="#F8623D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M21.875 64.1667H48.125" stroke="#F8623D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M52.0911 27.3285H38.2077C34.1827 27.3285 32.8411 24.6452 32.8411 21.9618V11.6952C32.8411 8.48685 35.4661 5.86185 38.6744 5.86185H52.0911C55.0661 5.86185 57.4577 8.25351 57.4577 11.2285V21.9618C57.4577 24.9368 55.0661 27.3285 52.0911 27.3285Z" stroke="#F8623D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M60.9881 23.0999L57.4589 20.6208V12.5708L60.9881 10.0916C62.7381 8.89578 64.1673 9.62495 64.1673 11.7541V21.4666C64.1673 23.5958 62.7381 24.3249 60.9881 23.0999Z" stroke="#F8623D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",
    "aditionals": """<svg width="70" height="70" viewBox="0 0 70 70" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M5.83331 29.1667H20.4166" stroke="#00BF71" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M5.83331 49.5833H20.4166" stroke="#00BF71" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M5.83331 8.75H55.4166" stroke="#00BF71" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M57.1667 54.25L64.1667 61.25M60.6667 42C60.6667 33.3013 53.6154 26.25 44.9167 26.25C36.218 26.25 29.1667 33.3013 29.1667 42C29.1667 50.6987 36.218 57.75 44.9167 57.75C53.6154 57.75 60.6667 50.6987 60.6667 42Z" stroke="#00BF71" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",
    "spider": """<svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<rect y="0.00244141" width="80" height="80" fill="url(#pattern0_1_167)"/>
<defs>
<pattern id="pattern0_1_167" patternContentUnits="objectBoundingBox" width="1" height="1">
<use xlink:href="#image0_1_167" transform="scale(0.0125)"/>
</pattern>
<image id="image0_1_167" width="80" height="80" preserveAspectRatio="none" xlink:href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFAAAABQCAYAAACOEfKtAAAEf0lEQVR4Ae2bi3EcIQyGU4I7SEpwCS7BJbiDuAR3kHTgdOASXEJKcAkpQZn/hn9HAwK0ZuHWN9qZHbjlIfEhXsL+9i2eIBAEgkAQCAJBIAgEgSAQBILATREQkR/5O7OBuSz8nilvet0i8iHl8zBLsIi85+JmyVpSbwAcxBwAA+AggU8UF5EHEXlK7780J2Fuek3v/SeqdRURkWclh9MhdZk297qU82YSkT/UXIVP3vJH5VOyGX0/qu6p9QTAQbwBMAAOEhgsHhZ4RYBpBeekb4UvXvWMwre/iNwcwHQ4x75Ov819XGUI/+RB37IgVT/ytR7sJanLXV4XZaQwr6dpgZW2jjkjKjBec8X170oZ3ZjvOj/iOnFHvNgYW84EVV8P4IvKy+jY/rUC4409nYNIMH6nM7DliYFiG0DWQ213hjhhwF22WWIFIPTA+1bR9y7V88uQPwUg5XxYCulvFWfCBWBSmnWNhNvCYgHU+ljxipFQnwBoQdPfZgPEMKETgI4B9g5+Nw/qIoLhzPIML0NukgVqZ8JFnobFuIjcK90LJyyGe9K7mGdZx+6wMhwJs7mwWMJmALTkWN9ExFow2BaEx4GjAgGQJD4Zqv2X1Xt/U68irblPpPjVFpiGLYYrXmuHADdcdY9JvYfDNHdoc8/jrpXrCgABp/Vsq/kwpFYFDoCYgGGJvRcLzBEPLKonC+lYVFrPaQC2lDxzWgAc7J1lAHF84mTLEEPkKz16wWAbxhwHrXmvl+aYF88Gd4219cAxXUQe09aAB3eGZwBHXXT4TN1PHVb2W0uhnhpQT7kAqAipHbweCr34UmurCOvpaKW7TlMKTz96BmuqAJrxebkzYUYjrllnABykHwBPATDt73hQtzzSTNMhXFtnfLBYaD0Zx/f8geMB6S7PUnUF6dwXmJdKnTK5oit/m9ea1kWUUsosUwXGhOR8xBnRui9A/fi+ufFxtajOx1YZ9DK+480tWek7HIX1U05eGdKKc2+6t0EZa+ToMv55sbNlKSzPcRbehkJqYN64o35vjexUWJyFHW0o2k2DK8IAaOIfBoi/W8E15mNOvNF7LLO5ihZaIK9cLRqWBcJNxzLWwjIMcPuTjB0AizKrAFJHix5WWKZbYUXHXQAxqaIX9FvAoPCGBRZlKspV2rn78zYHKt2sSuYCpPBWmG7VCLi2sp4VIPSl7oXjIO0q5v6fn/Na8qwAtVUWVtsynMPSGgBxXXnZb1nCVO8izxGPvt/Y/tSNspOeXCAseacDuO352AgrbHSA1cjWt+Z8RtmpU6161gNMja9Z0B6AnIeshnm/jQLE1gUWWlgv4R8aOizHBVAr5SWV5dtlOQ0LZLXb0VTrdng8AA4irQDU24LipNITWXEz0d1UC7fTTa9+pCcHCacMa9t1VQtcI9xDypEndRiHLsM1bahY4BrhDjieLAHQQ6mRJwA24HiSAqCHUiNPAGzA8SQFQA+lRp6rAoReaSXW7p41x6AGlD1JyqHxZduwp72RNwgEgSAQBIJAEAgCQSAIBIFbI/Af510HQg52hnMAAAAASUVORK5CYII="/>
</defs>
</svg>""",
    "goat": """<svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M66.6667 39.9999C66.6667 54.7276 54.7277 66.6666 40 66.6666C25.2724 66.6666 13.3334 54.7276 13.3334 39.9999C13.3334 25.2723 25.2724 13.3333 40 13.3333C54.7277 13.3333 66.6667 25.2723 66.6667 39.9999Z" stroke="#00BF71" stroke-width="3"/>
<path opacity="0.5" d="M50 40C50 45.523 45.523 50 40 50C34.477 50 30 45.523 30 40C30 34.477 34.477 30 40 30C45.523 30 50 34.477 50 40Z" stroke="#00BF71" stroke-width="3"/>
<path opacity="0.5" d="M6.66669 40H13.3334" stroke="#00BF71" stroke-width="3" stroke-linecap="round"/>
<path opacity="0.5" d="M66.6667 40H73.3334" stroke="#00BF71" stroke-width="3" stroke-linecap="round"/>
<path opacity="0.5" d="M40 13.3333V6.66663" stroke="#00BF71" stroke-width="3" stroke-linecap="round"/>
<path opacity="0.5" d="M40 73.3333V66.6666" stroke="#00BF71" stroke-width="3" stroke-linecap="round"/>
</svg>""",
    "top": """<svg width="70" height="70" viewBox="0 0 70 70" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M10.2083 52.5C10.2083 48.3752 10.2083 46.3129 11.4897 45.0313C12.7711 43.75 14.8335 43.75 18.9583 43.75H20.4166C23.1665 43.75 24.5414 43.75 25.3957 44.6043C26.25 45.4586 26.25 46.8335 26.25 49.5833V64.1667H10.2083V52.5Z" stroke="#FF5F3C" stroke-width="2.33333" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M43.75 55.4166C43.75 52.6668 43.75 51.2918 44.6043 50.4375C45.4586 49.5833 46.8335 49.5833 49.5833 49.5833H51.0417C55.1664 49.5833 57.2288 49.5833 58.5104 50.8645C59.7917 52.1461 59.7917 54.2085 59.7917 58.3333V64.1666H43.75V55.4166Z" stroke="#FF5F3C" stroke-width="2.33333" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M5.83331 64.1667H64.1666" stroke="#FF5F3C" stroke-width="2.33333" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M26.25 46.6667C26.25 42.542 26.25 40.4796 27.5314 39.198C28.8128 37.9167 30.8753 37.9167 35 37.9167C39.1248 37.9167 41.1871 37.9167 42.4687 39.198C43.75 40.4796 43.75 42.542 43.75 46.6667V64.1667H26.25V46.6667Z" stroke="#FF5F3C" stroke-width="2.33333" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M37.0157 7.51813L39.0687 11.6583C39.3487 12.2346 40.0951 12.7874 40.7251 12.8933L44.4465 13.5166C46.8262 13.9165 47.3862 15.6573 45.6712 17.3745L42.7781 20.2914C42.2884 20.7854 42.0201 21.7381 42.1718 22.4203L42.9998 26.0312C43.6531 28.8893 42.1484 29.9949 39.6404 28.5012L36.1524 26.4193C35.5224 26.0429 34.4843 26.0429 33.8426 26.4193L30.3546 28.5012C27.8582 29.9949 26.3417 28.8775 26.995 26.0312L27.8232 22.4203C27.9749 21.7381 27.7066 20.7854 27.2166 20.2914L24.3236 17.3745C22.6205 15.6573 23.1688 13.9165 25.5485 13.5166L29.2696 12.8933C29.8879 12.7874 30.6346 12.2346 30.9146 11.6583L32.9676 7.51813C34.0876 5.27163 35.9074 5.27163 37.0157 7.51813Z" stroke="#FF5F3C" stroke-width="2.33333" stroke-linecap="round" stroke-linejoin="round"/>
</svg> """,
    "bar": """<svg width="70" height="70" viewBox="0 0 70 70" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M6 17.6667C6 13.1737 6 10.9272 7.0113 9.27696C7.57716 8.35355 8.35355 7.57716 9.27696 7.0113C10.9272 6 13.1737 6 17.6667 6C22.1596 6 24.4061 6 26.0564 7.0113C26.9798 7.57716 27.7562 8.35355 28.322 9.27696C29.3333 10.9272 29.3333 13.1737 29.3333 17.6667C29.3333 22.1596 29.3333 24.4061 28.322 26.0564C27.7562 26.9798 26.9798 27.7562 26.0564 28.322C24.4061 29.3333 22.1596 29.3333 17.6667 29.3333C13.1737 29.3333 10.9272 29.3333 9.27696 28.322C8.35355 27.7562 7.57716 26.9798 7.0113 26.0564C6 24.4061 6 22.1596 6 17.6667Z" stroke="#00BF71" stroke-width="2.33333"/>
<path d="M39 17.6667C39 13.1737 39 10.9272 40.0112 9.27696C40.577 8.35355 41.3535 7.57716 42.2769 7.0113C43.9271 6 46.1738 6 50.6667 6C55.1595 6 57.4062 6 59.0565 7.0113C59.9799 7.57716 60.7563 8.35355 61.3221 9.27696C62.3333 10.9272 62.3333 13.1737 62.3333 17.6667C62.3333 22.1596 62.3333 24.4061 61.3221 26.0564C60.7563 26.9798 59.9799 27.7562 59.0565 28.322C57.4062 29.3333 55.1595 29.3333 50.6667 29.3333C46.1738 29.3333 43.9271 29.3333 42.2769 28.322C41.3535 27.7562 40.577 26.9798 40.0112 26.0564C39 24.4061 39 22.1596 39 17.6667Z" stroke="#00BF71" stroke-width="2.33333"/>
<path d="M6 50.1667C6 45.6738 6 43.4271 7.0113 41.7769C7.57716 40.8535 8.35355 40.077 9.27696 39.5112C10.9272 38.5 13.1737 38.5 17.6667 38.5C22.1596 38.5 24.4061 38.5 26.0564 39.5112C26.9798 40.077 27.7562 40.8535 28.322 41.7769C29.3333 43.4271 29.3333 45.6738 29.3333 50.1667C29.3333 54.6595 29.3333 56.9062 28.322 58.5565C27.7562 59.4799 26.9798 60.2563 26.0564 60.8221C24.4061 61.8333 22.1596 61.8333 17.6667 61.8333C13.1737 61.8333 10.9272 61.8333 9.27696 60.8221C8.35355 60.2563 7.57716 59.4799 7.0113 58.5565C6 56.9062 6 54.6595 6 50.1667Z" stroke="#00BF71" stroke-width="2.33333"/>
<path d="M39 50.1667C39 45.6738 39 43.4271 40.0112 41.7769C40.577 40.8535 41.3535 40.077 42.2769 39.5112C43.9271 38.5 46.1738 38.5 50.6667 38.5C55.1595 38.5 57.4062 38.5 59.0565 39.5112C59.9799 40.077 60.7563 40.8535 61.3221 41.7769C62.3333 43.4271 62.3333 45.6738 62.3333 50.1667C62.3333 54.6595 62.3333 56.9062 61.3221 58.5565C60.7563 59.4799 59.9799 60.2563 59.0565 60.8221C57.4062 61.8333 55.1595 61.8333 50.6667 61.8333C46.1738 61.8333 43.9271 61.8333 42.2769 60.8221C41.3535 60.2563 40.577 59.4799 40.0112 58.5565C39 56.9062 39 54.6595 39 50.1667Z" stroke="#00BF71" stroke-width="2.33333"/>
</svg> """,
}

logo = "data:image/png;base64,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"


def generate_html_report(json_path):
    """
    Generates an HTML report from a Scrapy metrics JSON file.

    Args:
        json_path: Path to the JSON file containing the metrics
        output_path: Optional path for the HTML output.
                    If None, uses the JSON filename + '-report.html'

    Returns:
        Path to the generated HTML file
    """
    json_path = Path(json_path)
    json_dir = json_path.parent
    json_name = json_path.stem

    if not json_path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")

    output_filename = f"{json_name}-report.html"
    output_path = json_dir / output_filename

    def format_duration(seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"

    def format_bytes(bytes_value):
        return round(bytes_value / (1024 * 1024), 2)

    def load_scrapy_stats(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        scrapy_stats = {
            "spider_name": data.get("spider_name", "Unknown"),
            "item_scraped_count": data.get("items_scraped", 0),
            "response_received_count": data.get("pages_processed", 0),
            "success_rate": data.get("success_rate", 0),
            "duration": format_duration(data.get("elapsed_time_seconds", 0)),
            "items_per_minute": round(data.get("items_per_minute", 0), 1),
            "pages_per_minute": round(data.get("pages_per_minute", 0), 2),
        }

        http_errors = data.get("http_errors", {})
        status_labels = []
        status_counts = []
        for code, count in http_errors.items():
            if code == "200":
                status_labels.append("200 OK")
            elif code == "404":
                status_labels.append("404 Not Found")
            elif code == "500":
                status_labels.append("500 Server Error")
            elif code == "503":
                status_labels.append("503 Unavailable")
            else:
                status_labels.append(f"{code} Error")
            status_counts.append(count)

        df_status = pd.DataFrame({"Status": status_labels, "Count": status_counts})

        error_data = {}
        for code, count in http_errors.items():
            if code != "200" and count > 0:
                error_data[code] = count

        if data.get("timeouts", 0) > 0:
            error_data["Timeout"] = data["timeouts"]

        retries_by_reason = data.get("retries", {}).get("by_reason", {})
        for reason, count in retries_by_reason.items():
            if count > 0:
                error_data[reason.capitalize()] = count

        if error_data:
            df_errors = (
                pd.DataFrame(
                    {
                        "Error": list(error_data.keys()),
                        "Count": list(error_data.values()),
                    }
                )
                .sort_values("Count", ascending=False)
                .head(5)
            )
        else:
            df_errors = pd.DataFrame({"Error": ["No errors"], "Count": [0]})

        # Timeline
        timeline_data = data.get("timeline", [])
        if timeline_data:
            df_timeline = pd.DataFrame(timeline_data)
            if "interval" in df_timeline.columns:
                df_timeline.rename(columns={"interval": "Time"}, inplace=True)
            if "items" in df_timeline.columns:
                df_timeline.rename(columns={"items": "Items"}, inplace=True)
        else:
            df_timeline = pd.DataFrame({"Time": ["0-1m"], "Items": [0]})

        # Fields coverage
        fields_data = data.get("schema_coverage", {}).get("fields", {})
        if fields_data:
            df_fields = pd.DataFrame(
                {
                    "Field": list(fields_data.keys()),
                    "Complete": [
                        fields_data[k].get("complete", 0) for k in fields_data.keys()
                    ],
                    "Empty": [
                        fields_data[k].get("empty", 0) for k in fields_data.keys()
                    ],
                }
            )
        else:
            schema = data.get("schema_coverage", {})
            total = schema.get("checked", 100)
            valid = schema.get("valid", 100)
            df_fields = pd.DataFrame(
                {"Field": ["Total"], "Complete": [valid], "Empty": [total - valid]}
            )

        # Additional metrics (convert bytes to MB)
        resources = data.get("resources", {})
        resources_formatted = {
            "peak_memory_bytes": format_bytes(resources.get("peak_memory_bytes", 0)),
            "time_per_page_seconds": round(data.get("time_per_page_seconds", 0), 2),
            "downloaded_bytes": format_bytes(resources.get("downloaded_bytes", 0)),
            "requests_failed": data.get("http_errors", {}).get("total_errors", 0),
        }

        return (
            scrapy_stats,
            df_status,
            df_errors,
            df_timeline,
            df_fields,
            resources_formatted,
            data,
        )

    def _generate_retry_reasons_html(data):
        retries = data.get('retries', {})
        by_reason = retries.get('by_reason', {})

        if not by_reason:
            return '<p style="text-align: center; color: #6b7280; padding: 20px;">No retries occurred</p>'

        html = '<div class="retry-table">'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<thead><tr style="border-bottom: 2px solid #e5e7eb;">'
        html += '<th style="text-align: left; padding: 12px; color: #6b7280; font-weight: 600;">Reason</th>'
        html += '<th style="text-align: right; padding: 12px; color: #6b7280; font-weight: 600;">Count</th>'
        html += '<th style="text-align: right; padding: 12px; color: #6b7280; font-weight: 600;">Percentage</th>'
        html += '<th style="text-align: left; padding: 12px; color: #6b7280; font-weight: 600;">Description</th>'
        html += '</tr></thead><tbody>'

        total = retries.get('total', sum(by_reason.values()))

        descriptions = {
            'twisted.web._newclient.ResponseNeverReceived': 'Server did not respond or connection was closed before receiving response',
            'twisted.internet.error.TimeoutError': 'Request timed out - server took too long to respond',
            'twisted.internet.error.ConnectionRefusedError': 'Server refused the connection',
            'twisted.internet.error.DNSLookupError': 'DNS lookup failed - domain not found',
            'twisted.internet.error.ConnectionLost': 'Connection was lost during the request'
        }

        sorted_reasons = sorted(by_reason.items(), key=lambda x: x[1], reverse=True)

        for reason, count in sorted_reasons:
            percentage = (count / total * 100) if total > 0 else 0
            clean_reason = reason.split('.')[-1]  # Get last part of error name
            description = descriptions.get(reason, 'Network or connection error')

            html += '<tr style="border-bottom: 1px solid #f3f4f6;">'
            html += f'<td style="padding: 12px;"><code style="background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-size: 13px;">{clean_reason}</code></td>'
            html += f'<td style="text-align: right; padding: 12px; font-weight: 600; color: #FF5733;">{count:,}</td>'
            html += f'<td style="text-align: right; padding: 12px; color: #6b7280;">{percentage:.1f}%</td>'
            html += f'<td style="padding: 12px; color: #6b7280; font-size: 14px;">{description}</td>'
            html += '</tr>'

        html += '</tbody></table></div>'
        return html

    scrapy_stats, df_status, df_errors, df_timeline, df_fields, resources, data = (
        load_scrapy_stats(json_path)
    )

    # Success rate
    if scrapy_stats["success_rate"] >= 95:
        status_class = "success"
        status_text = "Successful"
        icon = "✅"
    elif scrapy_stats["success_rate"] >= 80:
        status_class = "warning"
        status_text = "With Warnings"
        icon = "⚠️"
    else:
        status_class = "error"
        status_text = "Critical Error"
        icon = "❌"

    # 1. Bar chart
    colors = ["#00BF71", "#f59e0b", "#F8623D", "#FF5733"]

    fig_bar_status = go.Figure(
        data=[
            go.Bar(
                x=df_status["Status"],
                y=df_status["Count"],
                marker=dict(color=colors[: len(df_status)]),
                text=df_status["Count"],
                textposition="outside",
                textfont=dict(size=14, color="#1f2937", family="Poppins"),
                width=0.6,
                hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
            )
        ]
    )

    fig_bar_status.update_layout(
        height=400,
        width=600,
        margin=dict(t=40, b=60, l=50, r=40),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title=dict(
                text="Response Code",
                font=dict(size=14, color="#6b7280", family="Poppins"),
            ),
            tickangle=0,
            tickfont=dict(size=13, color="#1f2937", family="Poppins"),
            showgrid=False,
        ),
        yaxis=dict(
            title=dict(
                text="Count", font=dict(size=14, color="#6b7280", family="Poppins")
            ),
            tickfont=dict(size=13, color="#1f2937", family="Poppins"),
            showgrid=True,
            gridwidth=1,
            gridcolor="#f3f4f6",
        ),
        bargap=0.3,
    )

    # 2. Pie chart
    if df_errors["Count"].sum() > 0 and df_errors.iloc[0]["Error"] != "Sin errores":
        fig_pie = go.Figure(
            data=[
                go.Pie(
                    labels=df_errors["Error"],
                    values=df_errors["Count"],
                    marker=dict(
                        colors=["#FF5733", "#F8623D", "#C67448", "#838E56", "#00BF71"][
                            : len(df_errors)
                        ]
                    ),
                    textposition="inside",
                    textinfo="percent+label",
                    hole=0.4,
                )
            ]
        )

        fig_pie.update_layout(
            height=400,
            margin=dict(t=20, b=60, l=20, r=20),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.05,
                xanchor="center",
                x=0.5,
                font=dict(family="Poppins", size=12),
            ),
            autosize=True,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        pie_html = fig_pie.to_html(
            include_plotlyjs=False,
            div_id="pie_chart",
            config={"responsive": True, "displayModeBar": False},
            full_html=False,
        )
    else:
        pie_html = '<div style="text-align: center; padding: 40px; color: #6b7280;"><p style="font-size: 18px;">✅ No errors were recorded during scraping</p></div>'

    # 3. Timeline chart
    fig_line = px.line(df_timeline, x="Time", y="Items", markers=True)
    fig_line.update_traces(
        line_color="#FF5733",
        line_width=4,
        marker=dict(size=10, color="#FF5733", line=dict(width=2, color="white")),
    )

    fig_line.update_layout(
        height=400,
        margin=dict(t=40, b=60, l=60, r=40),
        showlegend=False,
        autosize=True,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title=dict(
                text="Time Interval",
                font=dict(size=13, color="#6b7280", family="Poppins"),
            ),
            tickfont=dict(size=12, color="#1f2937", family="Poppins"),
            showgrid=True,
            gridwidth=1,
            gridcolor="#f3f4f6",
        ),
        yaxis=dict(
            title=dict(
                text="Items Processed",
                font=dict(size=13, color="#6b7280", family="Poppins"),
            ),
            tickfont=dict(size=12, color="#1f2937", family="Poppins"),
            showgrid=True,
            gridwidth=1,
            gridcolor="#f3f4f6",
        ),
    )

    # 4. Fields coverage chart
    fig_fields = go.Figure()

    fig_fields.add_trace(
        go.Bar(
            name="Complete and Valid",
            y=df_fields["Field"],
            x=df_fields["Complete"],
            orientation="h",
            marker=dict(color="#00BF71"),
            text=df_fields["Complete"],
            textposition="inside",
            textfont=dict(color="white", size=12, family="Poppins"),
            hovertemplate="<b>%{y}</b><br>Complete: %{x}<extra></extra>",
        )
    )

    fig_fields.add_trace(
        go.Bar(
            name="Empty/Not Found",
            y=df_fields["Field"],
            x=df_fields["Empty"],
            orientation="h",
            marker=dict(color="#FF5733"),
            text=df_fields["Empty"],
            textposition="inside",
            textfont=dict(color="white", size=12, family="Poppins"),
            hovertemplate="<b>%{y}</b><br>Empty: %{x}<extra></extra>",
        )
    )

    fig_fields.update_layout(
        barmode="stack",
        height=max(400, len(df_fields) * 40),
        margin=dict(t=20, b=40, l=150, r=40),
        showlegend=True,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(family="Poppins", size=12),
        ),
        xaxis=dict(
            title=dict(
                text="Number of Items",
                font=dict(size=13, color="#6b7280", family="Poppins"),
            ),
            tickfont=dict(size=14, color="#1f2937", family="Poppins"),
            showgrid=True,
            gridwidth=1,
            gridcolor="#f3f4f6",
        ),
        yaxis=dict(
            tickfont=dict(size=12, color="#1f2937", family="Poppins"),
            showgrid=True,
            gridwidth=1,
            gridcolor="#f3f4f6",
        ),
        autosize=True,
    )

    config = {"responsive": True, "displayModeBar": False, "autosizable": True}

    bar_status_html = fig_bar_status.to_html(
        include_plotlyjs="cdn",
        div_id="bar_status_chart",
        config=config,
        full_html=False,
    )

    line_html = fig_line.to_html(
        include_plotlyjs=False, div_id="line_chart", config=config, full_html=False
    )

    fields_html = fig_fields.to_html(
        include_plotlyjs=False, div_id="fields_chart", config=config, full_html=False
    )

    html_template = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Scrapy Report - {datetime.now().strftime('%Y-%m-%d')}</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #ffffff;
                color: #232323;
                padding: 0;
                line-height: 1.6;
            }}

            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 40px 20px;
            }}

            .header {{
                margin-bottom: 40px;
                margin-top: 20px;
            }}

            .header-content {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 10px;
            }}

            .header-text {{
                flex: 1;
            }}

            .header h1 {{
                font-size: 48px;
                font-weight: 700;
                color: #232323;
            }}

            .header .subtitle {{
                color: #6b7280;
                font-size: 18px;
            }}

            .header-logo {{
                flex-shrink: 0;
            }}

            .header-logo img {{
                height: 20px;
                width: auto;
            }}

            .status-banner {{
                border-radius: 16px;
                padding: 32px;
                margin-bottom: 32px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border: 2px solid;
            }}

            .status-banner.success {{
                background: linear-gradient(135deg, #e6f9f0 0%, #ccf3e0 100%);
                border-color: #00BF71;
            }}

            .status-banner.warning {{
                background: linear-gradient(135deg, #fff4e6 0%, #ffe6cc 100%);
                border-color: #F8623D;
            }}

            .status-banner.error {{
                background: linear-gradient(135deg, #ffe8e6 0%, #ffd6d1 100%);
                border-color: #FF5733;
            }}

            .status-left {{
                display: flex;
                align-items: center;
                gap: 20px;
            }}

            .status-icon {{
                font-size: 48px;
                justify-content: center;
                align-items: center;
                display: flex;
            }}

            .status-text h2 {{
                font-size: 24px;
                font-weight: 700;
                color: #232323;
                line-height: 1;
            }}

            .status-text p {{
                font-size: 16px;
                font-weight: 600;
            }}

            .status-text p.success {{ color: #059669; }}
            .status-text p.warning {{ color: #d97706; }}
            .status-text p.error {{ color: #dc2626; }}

            .status-metrics {{
                display: flex;
                gap: 48px;
            }}

            .metric-item {{
                text-align: center;
            }}

            .metric-value {{
                font-size: 36px;
                font-weight: 700;
                color: #232323;
                line-height: 1;
            }}

            .metric-label {{
                font-size: 15px;
                color: #6b7280;
                margin-top: 2px;
                font-weight: 500;
            }}

            .card {{
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}

            .card-title {{
                font-size: 24px;
                font-weight: 500;
                color: #1f2937;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 12px;
                line-height: 1;
            }}

            .card-title svg {{
                flex-shrink: 0;
                display: block;
            }}

            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 24px;
            }}

            .metric-box {{
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }}

            .metric-box .value {{
                font-size: 28px;
                font-weight: 700;
                color: #232323;
                line-height: 1.5;
            }}

            .metric-box .label {{
                font-size: 14px;
                color: #6b7280;
            }}

            .charts-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 24px;
                margin-bottom: 24px;
            }}

            .card > div {{
                width: 100% !important;
                max-width: 100% !important;
            }}

            .plotly-graph-div {{
                width: 100% !important;
                max-width: 100% !important;
            }}

            .js-plotly-plot,
            .plot-container {{
                width: 100% !important;
                max-width: 100% !important;
                margin: 0 !important;
            }}

            .divider {{
                border: 0;
                border-top: 1px solid #e5e7eb;
                margin: 32px 0;
            }}

            .footer {{
                text-align: center;
                color: #9ca3af;
                font-size: 14px;
                margin-top: 32px;
            }}

            @media (max-width: 768px) {{
                .header-content {{
                    flex-direction: column;
                    text-align: center;
                }}

                .status-banner {{
                    flex-direction: column;
                    text-align: center;
                }}

                .status-metrics {{
                    margin-top: 20px;
                    flex-direction: column;
                    gap: 20px;
                }}

                .charts-grid {{
                    grid-template-columns: 1fr;
                }}
            }}

            .two-column-grid {{
                display: grid;
                grid-template-columns: 3fr 1fr;
                gap: 24px;
                margin-bottom: 24px;
            }}

            .large-column {{
                min-width: 0;
            }}

            .small-column {{
                display: flex;
                flex-direction: column;
            }}

            .vertical-metrics {{
                display: flex;
                flex-direction: column;
                gap: 16px;
            }}

            .metric-box-vertical {{
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
            }}

            .metric-box-vertical .value {{
                font-size: 28px;
                font-weight: 700;
                color: #232323;
                line-height: 1.5;
            }}

            .metric-box-vertical .label {{
                font-size: 13px;
                color: #6b7280;
                margin-top: 4px;
            }}

            .retry-table {{
                overflow-x: auto;
            }}

            .retry-table table {{
                font-size: 14px;
            }}

            .retry-table code {{
                font-family: 'Courier New', monospace;
            }}

            @media (max-width: 1024px) {{
                .two-column-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-content">
                    <div class="header-text">
                        <h1>Scrapy Metrics Report</h1>
                        <p class="subtitle"><strong>Spider:</strong> {scrapy_stats['spider_name']} | <strong>Executed:</strong> {datetime.now().strftime('%d %b %Y, %H:%M')}</p>
                    </div>
                    <div class="header-logo">
                        <img src="{logo}" alt="Logo">
                    </div>
                </div>
            </div>

            <div class="status-banner {status_class}">
                <div class="status-left">
                    <div class="status-icon">{icon}</div>
                    <div class="status-text">
                        <h2>Overall Status</h2>
                        <p class="{status_class}">{status_text}</p>
                    </div>
                </div>
                <div class="status-metrics">
                    <div class="metric-item">
                        <div class="metric-value">{scrapy_stats['item_scraped_count']:,}</div>
                        <div class="metric-label">Items Scraped</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{scrapy_stats['success_rate']}%</div>
                        <div class="metric-label">Success Rate</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{scrapy_stats['duration']}</div>
                        <div class="metric-label">Duration</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-title">{svg_icons['performance']} Performance Metrics</div>
                <div class="metrics-grid">
                    <div class="metric-box">
                        <div class="value">{scrapy_stats['response_received_count']:,}</div>
                        <div class="label">Pages Processed</div>
                    </div>
                    <div class="metric-box">
                        <div class="value">{scrapy_stats['items_per_minute']}</div>
                        <div class="label">Items/Minute</div>
                    </div>
                    <div class="metric-box">
                        <div class="value">{scrapy_stats['pages_per_minute']}</div>
                        <div class="label">Pages/Minute</div>
                    </div>
                    <div class="metric-box">
                        <div class="value">{resources['time_per_page_seconds']}s</div>
                        <div class="label">Time/Page</div>
                    </div>
                    <div class="metric-box">
                        <div class="value">{resources['peak_memory_bytes']} MB</div>
                        <div class="label">Peak Memory</div>
                    </div>
                </div>
            </div>

            <div class="charts-grid">
                <div class="card">
                    <div class="card-title">{svg_icons['bar']} HTTP Response Distribution</div>
                    {bar_status_html}
                </div>

                <div class="card">
                    <div class="card-title">{svg_icons['top']} Top 5 Errors</div>
                    {pie_html}
                </div>
            </div>

            <div class="card">
                <div class="card-title">{svg_icons['monitoring']} Scraping Speed (Items per Interval)</div>
                {line_html}
            </div>

            <div class="two-column-grid">
                <div class="card large-column">
                    <div class="card-title">{svg_icons['goat']} Scraped Fields Completeness</div>
                    {fields_html}
                </div>

                <div class="small-column">
                    <div class="card">
                        <div class="card-title">{svg_icons['aditionals']} Additional Metrics</div>
                        <div class="vertical-metrics">
                            <div class="metric-box-vertical">
                                <div class="value">{data.get('retries', {}).get('total', 0)}</div>
                                <div class="label">Retries</div>
                            </div>
                            <div class="metric-box-vertical">
                                <div class="value">{data.get('duplicates', 0)}</div>
                                <div class="label">Duplicates</div>
                            </div>
                            <div class="metric-box-vertical">
                                <div class="value">{data.get('timeouts', 0)}</div>
                                <div class="label">Timeouts</div>
                            </div>
                            <div class="metric-box-vertical">
                                <div class="value">{resources['downloaded_bytes']} MB</div>
                                <div class="label">Downloaded</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-title">{svg_icons['http']} Retry Reasons Breakdown</div>
                <div class="retry-reasons">
                    {_generate_retry_reasons_html(data)}
                </div>
            </div>

            <hr class="divider">

            <div class="footer">
                Report generated by PS Helper Library v1.0
            </div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    return output_path
