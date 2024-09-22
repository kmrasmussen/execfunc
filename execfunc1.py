import os
import json
import jsonschema
import pytz
from datetime import datetime
from kasperpylib.persistence import JsonMappedDict
from kasperpylib.telegram import send_to_chat
from kasperpylib.llm_apis import get_openrouter_completion
from time import sleep
from small_utils import get_copenhagen_time, is_notification_appropriate_time, get_copenhagen_time_between_3am_and_4am, get_copenhagen_datetime

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_LM = 'anthropic/claude-3.5-sonnet'

def send_to_telegram(text):
    print('sending to telegram:', text)
    send_to_chat(os.getenv('EXECFUNC_DEV1_TELEGRAM_TOKEN'), 1806003945, text)

def send_ntfy(text):
    #requests.post("https://ntfy.sh/execfunc",
    #    data=text.encode(encoding='utf-8'))
    send_to_telegram(text)

def parse_and_validate(text, schema):
    try:
        data = json.loads(text)
        jsonschema.validate(data, schema)
        return data
    except json.decoder.JSONDecodeError as e:
        print("Invalid JSON:", e)
        return None
    except jsonschema.exceptions.ValidationError as e:
        print("Validation error:", e)
        return None

def get_copenhagen_time():
    copenhagen_tz = pytz.timezone('Europe/Copenhagen')
    current_time = datetime.now(copenhagen_tz)
    formatted_time = current_time.strftime("%-I:%M%p")
    return formatted_time.lower()

def get_todays_history(todays_history_jmd):
    todays_history_jmd.reload()
    if 'todays_history' not in todays_history_jmd:
        return None
    else:
        return todays_history_jmd['todays_history']

def get_prompt(prompt_path, few_shots_path, todays_history_jmd, todo_jmd, habits_jmd):
    pre_prompt_template = open(prompt_path, 'r').read()
    #print('prepromttemplate begin')
    #print(pre_prompt_template)
    #print('prepromttemplate END')
    few_shots_prompt = open(few_shots_path, 'r').read()
    todo_jmd.reload()
    habits_jmd.reload()
    pre_prompt = pre_prompt_template.format(
        datetime_copenhagen=get_copenhagen_datetime(),
        todo=str(todo_jmd['todo']), 
        habits=str(habits_jmd['habits']), 
        fewshots=few_shots_prompt)

    timeline_prompt = f"""
    ## Timeline today
    The current time is {get_copenhagen_time()}

    This is today's history for which actions we performed and the inputs we got from user:
    ---
    {get_todays_history(todays_history_jmd)}
    ---

    Please reply in JSON for the action to be performed at {get_copenhagen_time()}
    You should not include for example "```json" for markdown blocks, we will directly try to parse your output as JSON so make sure there is nothing else.
    """

    prompt = pre_prompt + timeline_prompt
    #print('prompt:', prompt)
    return prompt

def perform_action(completion_parsed, todays_history_jmd, todo_jmd, habits_jmd):
    if completion_parsed is None:
        print("Invalid completion")
        exit()
    action = completion_parsed['action']
    arguments = completion_parsed['arguments']
    print('action', action)
    print('arguments', arguments)
    if action == 'make_notification':
        send_ntfy(arguments['notification_sentence'])
        todays_history_jmd['todays_history'].append(('make_notification', get_copenhagen_time(), arguments['notification_sentence']))
        todays_history_jmd.save()
    elif completion_parsed['action'] == 'ask_potential_todo':
        ask_arguments = completion_parsed['arguments']
        print("ask arguments:", ask_arguments)
        send_ntfy(ask_arguments['potential_todo_question'])
        todays_history_jmd['todays_history'].append((action, get_copenhagen_time(), arguments['potential_todo_question']))
        todays_history_jmd.save()
    elif completion_parsed['action'] == 'update_todo_status':
        try:
            todo_jmd['todo'][arguments['snakecase_id']]['status'] = arguments['new_status']
            todo_jmd.save()
            todays_history_jmd['todays_history'].append((action, get_copenhagen_time(), arguments['snakecase_id'], arguments['new_status']))
            todays_history_jmd.save()
            send_ntfy(f"Updated todo status for {arguments['snakecase_id']} to {arguments['new_status']}")
        except Exception as e:
            print("Error:", e)
            send_ntfy("Error when trying to update todo status")
    elif completion_parsed['action'] == 'update_habit_status':
        try:
            habits_jmd['habits'][arguments['snakecase_id']]['status'] = arguments['new_habit_status']
            habits_jmd.save()
            todays_history_jmd['todays_history'].append((action, get_copenhagen_time(), arguments['snakecase_id'], arguments['new_habit_status']))
            todays_history_jmd.save()
            send_ntfy(f"Updated todo status for {arguments['snakecase_id']} to {arguments['new_habit_status']}")
        except Exception as e:
            print("Error:", e)
            send_ntfy("Error when trying to update todo status")
    elif completion_parsed['action'] == 'create_todo_item':
        try:
            new_id = arguments['snakecase_id']
            new_content = arguments['todo_item_name']
            todo_jmd.reload()
            todo_jmd['todo'][new_id] = {
                'content': new_content,
                'status': 'todo'
            }
            todo_jmd.save()
            todays_history_jmd['todays_history'].append((action, get_copenhagen_time(), new_id, new_content))
            todays_history_jmd.save()
            send_ntfy(f"Created new todo item {new_id} with content: {new_content}"),
        except Exception as e:
            print("Error:", e)
            send_ntfy("Error when trying to create new todo item")
    elif completion_parsed['action'] == 'create_habit_item':
        try:
            new_id = arguments['snakecase_id']
            new_content = arguments['habit_name']
            new_description = arguments['habit_details']
            habits_jmd.reload()
            habits_jmd['habits'][new_id] = {
                'content': new_content,
                'details': new_description,
                'status_for_today': "-"
            }
            habits_jmd.save()
            todays_history_jmd['todays_history'].append((action, get_copenhagen_time(), new_content, new_description))
            todays_history_jmd.save()
            send_ntfy(f"Created new habit item {new_id} with content: {new_content}")
        except Exception as e:
            print("Error:", e)
            send_ntfy("Error when trying to create new habit item")
    else:
        print('got other action:', completion_parsed)
        send_ntfy('tried to perform non-implemented action')

def generate_and_perform_action(prompt_path, fewshots_path, todays_history_jmd, todo_jmd, my_habits_jmd):
    prompt = get_prompt(prompt_path, fewshots_path, todays_history_jmd, todo_jmd, my_habits_jmd)
    completion_text = get_openrouter_completion([{"role": "user", "content": prompt}], OPENROUTER_LM, OPENROUTER_API_KEY)
    print('completion_text:', completion_text)
    completion_parsed = parse_and_validate(completion_text, schema)
    print('completion parsed', completion_parsed)
    if isinstance(completion_parsed, list):
        print("Processing a list of actions")
        for action_object in completion_parsed:
            perform_action(action_object, todays_history_jmd, todo_jmd, my_habits_jmd)
    elif isinstance(completion_parsed, dict):
        print("Processing a single action")
        perform_action(completion_parsed, todays_history_jmd, todo_jmd, my_habits_jmd)

sleep_time_seconds = 300
my_prompt_path = 'prompts/prompt1.md'
my_fewshots_path = 'prompts/few_shots.md'
my_todays_history_path = './persistent/todays_history.json'
my_todo_path = './persistent/todo.json'
my_habits_path = './persistent/habits.json'
my_schema_path = 'schemas/schema3.json'

my_todays_history_jmd = JsonMappedDict(my_todays_history_path)
if 'todays_history' not in my_todays_history_jmd:
    my_todays_history_jmd['todays_history'] = []
    my_todays_history_jmd.save()

my_todo_jmd = JsonMappedDict(my_todo_path)
my_habits_jmd = JsonMappedDict(my_habits_path)

with open(my_schema_path, 'r') as f:
    schema = json.load(f)

# every 5 minutes generate and perform action
while True:
    # if copenhagen time is between 3am and 4am
    if get_copenhagen_time_between_3am_and_4am():
        my_todays_history_jmd.reload()
        my_todays_history_jmd['todays_history'] = []
        my_todays_history_jmd.save()

    if is_notification_appropriate_time():
        print('generating and performing action', datetime.now())
        generate_and_perform_action(my_prompt_path, my_fewshots_path, my_todays_history_jmd, my_todo_jmd, my_habits_jmd)
        print('sleeping for', sleep_time_seconds, 'seconds...')
        sleep(sleep_time_seconds)
    else:
        print('not appropriate time for notification', datetime.now())
        sleep(sleep_time_seconds)