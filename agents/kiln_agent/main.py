# agents/kiln_agent/main.py

import os
import json
import threading

from flask import Flask, request, jsonify
from google.cloud import pubsub_v1
import sys
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from envs.kiln_env import KilnEnv


app = Flask(__name__)

# ─── Environment & Pub/Sub Clients ────────────────────────────────────────────
env = KilnEnv()

PROJECT_ID = os.getenv("PROJECT_ID")
# Topics & subscriptions
PUB_TOPIC     = f"projects/{PROJECT_ID}/topics/kiln-to-cooler-forecast"
SUB_SUBSCRIPTION = f"projects/{PROJECT_ID}/subscriptions/cooler-to-kiln-feedback"

publisher  = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

# ─── Subscriber Callback ───────────────────────────────────────────────────────
def handle_cooler_feedback(message: pubsub_v1.subscriber.message.Message):
    """
    Called whenever CoolerAgent publishes a message
    to the 'cooler-to-kiln-feedback' topic.
    """
    data = json.loads(message.data.decode("utf-8"))
    # e.g. data = {"exit_temp_setpoint": 610.0}
    
    # Use feedback to adjust policy / trigger new action
    obs = env.reset()
    obs, reward, done, info = env.step([0.0, 0.0])  # replace with your logic
    
    # Optionally publish a new forecast downstream
    forecast = json.dumps({
        "next_temp_setpoint": obs[0],
        "fuel_rate":          obs[1]
    })
    publisher.publish(PUB_TOPIC, forecast.encode("utf-8"))
    
    message.ack()


def start_subscriber():
    """
    Launch the Pub/Sub subscriber in a daemon thread.
    """
    subscriber.subscribe(SUB_SUBSCRIPTION, callback=handle_cooler_feedback)
    # The subscriber object runs indefinitely in its own threads
    # so we just keep this function alive.
    threading.Event().wait()


# ─── Flask Endpoints ───────────────────────────────────────────────────────────
@app.route("/recommend_setpoint", methods=["POST"])
def recommend_setpoint():
    """
    HTTP endpoint to get an on-demand recommendation.
    """
    payload = request.get_json(force=True)
    # you can fetch real sensor_data from payload if provided
    obs = env.reset()
    obs, reward, done, info = env.step(env.action_space.sample())
    return jsonify({
        "recommended_setpoint": obs[0],
        "fuel_rate": obs[1],
        "clinker_rate": obs[3],
        "reward": reward
    })


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


# ─── Application Entrypoint ──────────────────────────────────────────────────
if __name__ == "__main__":
    # 1) Start subscriber in background
    threading.Thread(target=start_subscriber, daemon=True).start()
    
    # 2) Launch Flask server (foreground)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)