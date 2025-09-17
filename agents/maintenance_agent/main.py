import os
import json
import threading
import time

from flask import Flask
from google.cloud import pubsub_v1, bigquery
import sys
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#from envs.multi_env import MaintenanceEnv 
app = Flask(__name__)

PROJECT = os.getenv["PROJECT_ID"]
publisher  = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()
bq_client  = bigquery.Client()

PUB_TOPIC        = f"projects/{PROJECT}/topics/maint-alerts"
SUB_SUBSCRIPTION = f"projects/{PROJECT}/subscriptions/ops-agent-sub"  # for ops-schedule

def handle_ops_schedule(message: pubsub_v1.subscriber.message.Message):
    schedule = json.loads(message.data.decode("utf-8"))
    # Optionally adjust monitoring window or logic
    print("Received new ops-schedule:", schedule)
    message.ack()

def start_subscriber():
    subscriber.subscribe(SUB_SUBSCRIPTION, callback=handle_ops_schedule)
    threading.Event().wait()

def monitor_assets_loop():
    while True:
        # Example BQ query (replace with your table)
        query = """
        SELECT asset_id, vibration, temperature
        FROM `my-project.dataset.asset_metrics`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
        """
        for row in bq_client.query(query):
            risk = 0.7 * row.vibration + 0.3 * row.temperature
            if risk > 50:
                alert = json.dumps({
                    "asset_id": row.asset_id,
                    "risk_score": risk
                })
                publisher.publish(PUB_TOPIC, alert.encode("utf-8"))
        time.sleep(300)

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    # 1) Pub/Sub subscriber
    threading.Thread(target=start_subscriber, daemon=True).start()
    # 2) Asset monitor thread
    threading.Thread(target=monitor_assets_loop, daemon=True).start()
    # 3) Flask
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)