import requests
import os
import datetime
from scrapy import signals


class EstelaSlackAlerts:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    @classmethod
    def from_crawler(cls, crawler):
        webhook_url = crawler.settings.get('SLACK_WEBHOOK_URL')
        if not webhook_url:
            return None

        ext = cls(webhook_url)
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        return ext

    def spider_opened(self, spider):
        self.start_time = datetime.datetime.now()

    def spider_closed(self, spider, reason):
        stats = spider.crawler.stats.get_stats()

        # --- 1. Basic Metrics ---
        items = stats.get('item_scraped_count', 0)
        items_expected = getattr(spider, "ITEMS_EXPECTED", 0)
        responses = stats.get('downloader/response_count', 0)

        # --- 2. Network & Error Breakdown ---
        status_200 = stats.get('downloader/response_status_count/200', 0)
        err_403 = stats.get('downloader/response_status_count/403', 0)
        err_407 = stats.get('downloader/response_status_count/407', 0)
        err_429 = stats.get('downloader/response_status_count/429', 0)
        err_500 = stats.get('downloader/response_status_count/500', 0)
        err_503 = stats.get('downloader/response_status_count/503', 0)
        tunnel_errors = stats.get('downloader/exception_type_count/twisted.internet.error.TimeoutError', 0)
        log_errors = stats.get('log_count/ERROR', 0)

        server_errors = err_500 + err_503

        # --- 3. Rates Calculation ---
        http_success_rate = (status_200 / responses * 100) if responses > 0 else 0.0
        goal_achievement = (items / items_expected * 100) if items_expected > 0 else None

        # Efficiency Factor
        req_per_item = responses / items if items > 0 else float('inf')
        if req_per_item <= 3:
            efficiency_factor = 1.0
        elif req_per_item <= 4:
            efficiency_factor = 0.95
        elif req_per_item <= 5:
            efficiency_factor = 0.90
        elif req_per_item <= 7:
            efficiency_factor = 0.80
        else:
            efficiency_factor = 0.65

        # Overall Success Rate
        if goal_achievement is not None:
            success_rate = ((goal_achievement * 0.7) + (http_success_rate * 0.3)) * efficiency_factor
        else:
            success_rate = http_success_rate * efficiency_factor

        success_rate = min(100.0, max(0.0, success_rate))

        # --- 4. Alert Triggers ---
        low_yield = items_expected > 0 and items < items_expected
        zero_items = items == 0
        bad_exit = reason not in ['finished', 'closespider_itemcount']
        high_error_rate = log_errors > (responses * 0.5) if responses > 0 else False
        network_issues = (err_403 + err_407 + err_429 + tunnel_errors + server_errors) > 10

        if any([low_yield, zero_items, bad_exit, high_error_rate, network_issues]):

            # Duration Calculation
            finish_time = datetime.datetime.now()
            if hasattr(self, 'start_time'):
                duration_td = finish_time - self.start_time
                duration = str(duration_td).split('.')[0]
            else:
                duration = "N/A"

            # Build Anomalies List
            alert_reasons = []
            if zero_items:
                alert_reasons.append("• *Critical:* No items were extracted.")
            elif low_yield:
                alert_reasons.append(f"• *Low Yield:* Only {items}/{items_expected} items scraped.")
            if bad_exit:
                alert_reasons.append(f"• *Abnormal Exit:* Reason `{reason}`.")
            if network_issues:
                alert_reasons.append("• *Network Degradation:* High number of proxy bans or timeouts.")
            if high_error_rate and not zero_items:
                alert_reasons.append(f"• *High Error Rate:* {log_errors} general errors detected.")

            anomalies_text = "\n".join(alert_reasons)
            goal_text = f"{round(goal_achievement, 2)}%" if goal_achievement is not None else "N/A"

            # --- 5. Estela Environment Variables & URL Builder ---
            estela_spider_job = os.getenv("ESTELA_SPIDER_JOB")

            job_id = "N/A"
            spider_id = "N/A"
            project_id = "N/A"
            job_url = None

            if estela_spider_job:
                parts = estela_spider_job.split(".")
                if len(parts) == 3:
                    project_id = parts[0]  # El largo (507eb994...)
                    spider_id = parts[1]   # El ID de la araña (20)
                    job_id = parts[2]      # El Job (14313)
                else:
                    job_id = parts[0]

            if project_id != "N/A" and spider_id != "N/A" and job_id != "N/A":
                base_url = "https://hetzner-staging.bitmaker.dev"
                job_url = f"{base_url}/projects/{project_id}/spiders/{spider_id}/jobs/{job_id}"

            # --- 6. Dynamic Network Fields ---
            network_fields = [
                {"type": "mrkdwn", "text": f"*200 (OK):*\n{status_200}"}
            ]

            if tunnel_errors > 0:
                network_fields.append({"type": "mrkdwn", "text": f"*Tunnel (Timeouts):*\n{tunnel_errors}"})
            if err_403 > 0:
                network_fields.append({"type": "mrkdwn", "text": f"*403 (Forbidden):*\n{err_403}"})
            if err_407 > 0:
                network_fields.append({"type": "mrkdwn", "text": f"*407 (Proxy Auth):*\n{err_407}"})
            if err_429 > 0:
                network_fields.append({"type": "mrkdwn", "text": f"*429 (Rate Limit):*\n{err_429}"})
            if server_errors > 0:
                network_fields.append({"type": "mrkdwn", "text": f"*50x (Server Errors):*\n{server_errors}"})
            if log_errors > 0:
                network_fields.append({"type": "mrkdwn", "text": f"*Log Errors:*\n{log_errors}"})

            # Alignment Spacer
            if len(network_fields) % 2 != 0:
                network_fields.append({"type": "mrkdwn", "text": " "})

            network_title = "🌐 *Network & Errors Breakdown*" if len(network_fields) > 2 else "🌐 *Network Traffic*"

            # --- 7. Construct Final Slack Blocks ---
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "Spider Quality Alert", "emoji": True}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Spider:* `{spider.name}`\n*Anomalies Detected:*\n{anomalies_text}"}
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "📊 *Key Performance Indicators*"},
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Success Rate:*\n{round(success_rate, 2)}%"},
                        {"type": "mrkdwn", "text": f"*HTTP Success:*\n{round(http_success_rate, 2)}%"},
                        {"type": "mrkdwn", "text": f"*Goal Achieved:*\n{goal_text}"},
                        {"type": "mrkdwn", "text": f"*Duration:*\n{duration}"}
                    ]
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": network_title},
                    "fields": network_fields
                }
            ]

            # Add Button if Estela URL is available
            if job_url:
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🖥️ Ver Job en Estela",
                                "emoji": True
                            },
                            "url": job_url,
                            "style": "primary"
                        }
                    ]
                })

            # Add Footer
            blocks.append({
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"Estela Job ID: {job_id} | Production Monitoring"}]
            })

            payload = {
                "attachments": [
                    {
                        "color": "#D32F2F",
                        "fallback": f"Alert: {spider.name}",
                        "blocks": blocks
                    }
                ]
            }

            try:
                requests.post(self.webhook_url, json=payload, timeout=10)
            except Exception as e:
                spider.logger.error(f"Failed to send Slack alert: {e}")
        else:
            spider.logger.info("Health Check: OK. No Slack alert triggered.")
