import argparse
import time
import os

import vision
from vimbot import Vimbot

from flask import Flask, request
from typing import Literal, Union, List
from PIL import Image
import json


def main(website: Union[Literal['todoist'], Literal['google']], objective: str, completion_condition: str = "When the object seems complete"):
    print("Initializing the Vimbot driver...")

    init_functions = {
        'todoist': initTodoist,
        'google': initGoogle
    }

    # Call the appropriate function
    if website in init_functions:
        driver = init_functions[website]() 
    else:
        raise ValueError(f"Invalid website: {website}")

    input("Press Enter to continue...")
    history: List[str] = []
    result = None
    while True:
        time.sleep(1)
        print("Capturing the screen...")
        screenshot = driver.capture()
        print("Getting actions for the given objective...")
        action = vision.get_actions(screenshot, objective, completion_condition, history)
        perform_action_result = driver.perform_action(action)
        if perform_action_result:
            result = perform_action_result
            break
    return result

# Opens todoist and performs login
def initTodoistFresh(): 
    driver = Vimbot()
    driver.navigate("https://app.todoist.com/auth/login")
    driver.page.type('input[type="email"]', os.getenv("TODOIST_USER")) # type: ignore
    driver.page.type('input[type="password"]', os.getenv("TODOIST_PASSWORD")) # type: ignore
    driver.page.click('button[type="submit"]')
    driver.page.wait_for_selector('button[aria-controls="sidebar"]')
    return driver

def initTodoist(): 
    driver = Vimbot()
    driver.navigate("https://app.todoist.com")
    driver.page.wait_for_selector('button[aria-controls="sidebar"]')
    driver.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    return driver


def initGoogle():
    driver = Vimbot()
    driver.navigate("https://www.google.com")
    return driver


app = Flask(__name__)

@app.route("/ping", methods=["POST"])
def ping():
    # dummy function to test the Flask server
    print("Received request to ping the Vimbot")
    # return some dummy response as json
    return {"status": "success"}

@app.route("/run", methods=["POST"])
def run():
    data = request.get_json()
    prompt = data.get("prompt")
    completion_condition = data.get("completion_condition")
    # website = data.get("website")

    print(f"Received request to run the Vimbot with prompt: {prompt} and completion_condition: {completion_condition}")
    result = main("google", prompt, completion_condition)
    # if result is a json, return it as is, otherwise return it as a string
    if isinstance(result, dict):
        return result
    else:
        return {"result": result}

def classicMode():
    # The classic mode of the Vimbot
    print("Starting the Vimbot in classic mode...")
    objective = input("Please enter your objective: ")
    result = main("google", objective)
    if isinstance(result, dict):
        return result
    else:
        return {"result": result}


if __name__ == "__main__":
    # if classic mode is supplied, then run classicMode otherwise run the server
    parser = argparse.ArgumentParser()
    parser.add_argument("--classic", action="store_true")
    args = parser.parse_args()
    if args.classic:
        classicMode()
    else:
        print("Starting the Flask server...")
        app.run(host="0.0.0.0", port=8000)