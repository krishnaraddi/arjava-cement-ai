import os
import json
import threading
import sys
from flask import Flask, request, jsonify
from google.cloud import pubsub_v1
from envs.mix_env import MixEnv
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

app = Flask(__name__)
env = MixEnv()

PROJECT = os.getenv["PROJECT_ID"]

# Pub/Sub names
PUB_TOPIC        = f"projects/{PROJECT}/topics/mix-to-kiln-chemistry"  
SUB_SUBSCRIPTION = f"projects/{PROJECT}/subscriptions/ops-agent-sub"  # subscribed to ops-schedule

publisher  = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()


def handle_ops_schedule(message: pubsub_v1.subscriber.message.Message):
    schedule = json.loads(message.data.decode("utf-8"))
    # e.g. {"downtime_window": [...], "line": "kiln-line-1"}
    
    # Run mix tuning logic
    obs, reward, done, info = env.step([0.0])
    ratio = obs[0]
    
    out_msg = json.dumps({
        "CaO_SiO2": ratio,
        "moisture": obs[1]
    })
    publisher.publish(PUB_TOPIC, out_msg.encode("utf-8"))
    message.ack()


def start_subscriber():
    subscriber.subscribe(SUB_SUBSCRIPTION, callback=handle_ops_schedule)
    threading.Event().wait()


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


@app.route("/tune_mix", methods=["POST"])
def tune_mix():
    data = request.get_json(force=True)
    obs, reward, done, info = env.step(env.action_space.sample())
    return jsonify({
        "recommended_ratio": obs[0],
        "moisture": obs[1],
        "reward": reward
    })


if __name__ == "__main__":
    threading.Thread(target=start_subscriber, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)