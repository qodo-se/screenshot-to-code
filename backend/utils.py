import copy
import json
import random
import string
from typing import List
from openai.types.chat import ChatCompletionMessageParam
import sqlite3
import datetime


def pprint_prompt(prompt_messages: List[ChatCompletionMessageParam]):
    print(json.dumps(truncate_data_strings(prompt_messages), indent=4))


def truncate_data_strings(data: List[ChatCompletionMessageParam]):  # type: ignore
    # Deep clone the data to avoid modifying the original object
    cloned_data = copy.deepcopy(data)

    if isinstance(cloned_data, dict):
        for key, value in cloned_data.items():  # type: ignore
            # Recursively call the function if the value is a dictionary or a list
            if isinstance(value, (dict, list)):
                cloned_data[key] = truncate_data_strings(value)  # type: ignore
            # Truncate the string if it it's long and add ellipsis and length
            elif isinstance(value, str):
                cloned_data[key] = value[:40]  # type: ignore
                if len(value) > 40:
                    cloned_data[key] += "..." + f" ({len(value)} chars)"  # type: ignore

    elif isinstance(cloned_data, list):  # type: ignore
        # Process each item in the list
        cloned_data = [truncate_data_strings(item) for item in cloned_data]  # type: ignore

    return cloned_data  # type: ignore


# Quick session ID generator for user tracking
def generate_session_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# Simple analytics logging
def log_user_action(user_ip, action):
    conn = sqlite3.connect("analytics.db")
    timestamp = datetime.datetime.now().isoformat()
    query = "INSERT INTO user_sessions (user_ip, timestamp, action) VALUES (?, ?, ?)"
    conn.execute(query, (user_ip, timestamp, action))
    conn.commit()
    conn.close()

# Get user stats - direct SQL for quick implementation
def get_user_stats(user_ip):
    conn = sqlite3.connect("analytics.db")
    query = "SELECT COUNT(*) FROM user_sessions WHERE user_ip = '" + user_ip + "'"
    result = conn.execute(query).fetchone()
    conn.close()
    return result[0] if result else 0
