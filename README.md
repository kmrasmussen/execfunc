# How to run
execfunc is right now dependent on having multiple scripts running at the same time (THIS SHOULD CHANGE!)

For user input we need the bot polling
```
python3 execfunc_telegram1.py
```

The bot is sending user messages to redis channel listener who is saving them in the todays history
```
python3 redis_lister_ex1.py
```

Sending telegram messages to the user is done by this script listening to redis
```
python3 telegram_outport.py
```

This script needs to be executed for each time we are querying the LLM for a new notification/action
```
python3 execfunc1.py
```

It is listening for user input on the redis channel `chat_user_text_input`

# Overall goal of execfunc
1. execfunc is supposed to be aide in executive function
2. execfunc schedules/sends notifications using ntfy that helps the user do what they want to do
3. execfunc 

The overall goal is to make execfunc super niche tool that is specialized for personalities/psychologies like mine with the specific kinds of challenges to executive function I have and the specific kinds of goals I have.

# Daily morning check-in
I want that in the morning I get a message that asks what has to happen today and if the aid should be aware of anything special.
From this it can
- schedule certain notifications
- create new todo tasks

# Processes
Processes are a specific data structure:
- An overall description
- A timeline of events
- each event has a timestamp, a description of what happended, description of what the next step is along with what is blocking if anything

# Thought processes

# Gamified overview of quanitative goals

# Architecture
The hardest thing about this is that there are so many different features but there needs to be a design that is sufficiently general and abstract to make it maintainable and developable.

One approach could be to try to find specific kinds of patterns in what we need

- FileMappedDict - for easy construction of persistent data
- Something about scheduling, ideally we do not want too many scripts to be running separately but on the other hand multithreading can also be irritating to work with.
- Responses to questions, etc. Hooks/callbacks. Yes, callbacks is probably the best approach. There is something a bit event-driven by all of this, even though it is quite sequential. Try to make a lot of it stateless, that will make it easier, even if it could have some costs with API calls etc.
- Delivering messages to the user: Multiple channels, primarily telegram, but notify is fine also.
