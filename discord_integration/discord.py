"""
    Upload Log Data to Discord
    All webhook URLs should be in environmental variables listed below:


"""
import os
import requests

DATUM_CHANNEL_WEBHOOK = os.environ.get("CONTROL_CENTRE_DATUM_WEBHOOK")

def upload_log_file(log_text):
    """
        Upload log file to discord
    """
    data = {
        "content" : f"I have the following log to report :salute:!```{log_text}```",
        "username" : "Log Dumper"
        #"embeds" : [
        #    {
        #        "description": f"{log_text}",
        #        "title": "Log Output"
        #    }
        #]
    }

    print(DATUM_CHANNEL_WEBHOOK)
    result = requests.post(DATUM_CHANNEL_WEBHOOK, json = data, timeout=3)
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        return False
    return True
