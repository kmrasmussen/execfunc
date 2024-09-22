from kasperpylib.redis import *
from kasperpylib.persistence import JsonMappedDict
from small_utils import get_copenhagen_time

todays_history_jmd = JsonMappedDict('todays_history.json')

for message in get_redis_channel_rawtext_yielder('chat_user_text_input'):
    print(message)
    todays_history_jmd.reload()
    todays_history_jmd['todays_history'].append([
      "received_user_text",
      get_copenhagen_time(),
      message
    ])
    todays_history_jmd.save()
    print('saved input')