import os
import json
import threading
import sys  
from flask import Flask, request, jsonify
from google.cloud import pubsub_v1
from envs.cooler_env import CoolerEnv
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from envs.cooler_env import CoolerEnv

app = Flask(__name__)
env = CoolerEnv()

PROJECT = os.getenv("PROJECT_ID")

# Pub/Sub names (create these in Cloud Console or via gcloud)
PUB_TOPIC        = f"projects/{PROJECT}/topics/cooler-to-kiln-feedback"
SUB_SUBSCRIPTION = f"projects/{PROJECT}/subscriptions/cooler-sub"  # subscribed to kiln-to-cooler-forecast

publisher  = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()


def handle_kiln_forecast(message: pubsub_v1.subscriber.message.Message):
    payload = json.loads(message.data.decode("utf-8"))
    # e.g. {"exit_temp_setpoint": 875.0}
    
    # Use env.step or your actual policy logic
    obs, reward, done, info = env.step([0.0])  # single-action array
    fan_speed = obs[1]
    
    # Publish feedback downstream
    out_msg = json.dumps({
        "optimized_fan_speed": fan_speed,
        "exit_temp": obs[0]
    })
    publisher.publish(PUB_TOPIC, out_msg.encode("utf-8"))
    message.ack()


def start_subscriber():
    subscriber.subscribe(SUB_SUBSCRIPTION, callback=handle_kiln_forecast)
    threading.Event().wait()  # keep thread alive


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


@app.route("/adjust_fan", methods=["POST"])
def adjust_fan():
    data = request.get_json(force=True)
    # You might take incoming sensor data from data["sensor"]
    obs, reward, done, info = env.step(env.action_space.sample())
    return jsonify({
        "recommended_fan_speed": obs[1],
        "exit_temp": obs[0],
        "reward": reward
    })


if __name__ == "__main__":
    threading.Thread(target=start_subscriber, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)