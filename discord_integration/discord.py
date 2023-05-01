"""
    Upload Log Data to Discord
    All webhook URLs should be in environmental variables listed below:


"""
import os
import requests
import time

DATUM_CHANNEL_WEBHOOK = os.environ.get("CONTROL_CENTRE_DATUM_WEBHOOK")

def upload_log_file(log_text):
    """
        Upload log file to discord
    """
    def _send(text):
        data = {
            "content" : text,
            "username" : "Wallace"
        }
        result = requests.post(DATUM_CHANNEL_WEBHOOK, json = data, timeout=3)
        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            return False
        print("Sent", text)

    # Split log into 15_000 character chunks
    log_chunks = [log_text[i:i+1_900] for i in range(0, len(log_text), 1_900)]

    _send(f"I have the following log to report :saluting_face: ({len(log_text)} characters total, {len(log_chunks)} chunks):")

    for chunk in log_chunks:
        time.sleep(1)
        _send(f"```{chunk}```")
    return True
