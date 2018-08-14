from __future__ import print_function
import boto3
from botocore.vendored import requests
from boto3.dynamodb.conditions import Key, Attr
from connection import connect_peope_food
from connection import connect_peope_place

def food_connect(session):
    session_attributes = {}
    output= connect_peope_food(session)
    card_title = output

    reprompt_text = output
    speech_output= output
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, False))
        
def place_connect(session):
    session_attributes = {}
    output= connect_peope_place(session)
    card_title = output

    reprompt_text = output
    speech_output= output
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, False))

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

def get_sentiment(text):
    url="https://api.dandelion.eu/datatxt/sent/v1"
    token="8243df2b739e4df2a8c3cc0fd8afa415"
    response=requests.get(url=url,params={"text":text,"token":token,'lang':'en'})
    sentiment=response.json()['sentiment']['type']
    score=response.json()['sentiment']['score'] 
    return str(score)
        
def dump_data(table,user_id,entity_name,entity_type,sentiment):
    row = table.query(KeyConditionExpression=(Key('ID').eq(user_id) & Key('EntityName').eq(entity_name)))
    if(row['Count']==0):
        N=1 
    else:
        N=row['Items'][0]['N']
        sentiment=str((float(row['Items'][0]['Sentiment'])*float(N)+float(sentiment))/float((N+1)))
        N+=1
    
    table.put_item(
                    Item={
                    'ID': user_id,
                    'EntityType':entity_type,
                    'EntityName':entity_name,
                    'Sentiment':sentiment,
                    'N':N
                    })
    
    

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response(user_id):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('user_id_name')

    user = table.query(
        KeyConditionExpression=Key('ID').eq(user_id)
    )
    
    if (user['Count'] == 0):
        speech_output = "Welcome to My Emotion App, You seem to be new, what's your good name?"
    else:
        speech_output = 'Hey ' + user['Items'][0]['Name'] + ", Welcome to My Emotion App! " \
                                                            "Would you like to share your day or would you like to connect with people with similar interest in food and place??"

    session_attributes = {}
    card_title = "Welcome"

    reprompt_text = "Welcome to the My Emotion." \
                    "Would you like to share your day or would you like to get some suggestions?"

    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def set_name(intent, session,dialog_state):
    arr = [0] * 2
    slots = intent['slots']
    for i, slot in enumerate(slots):
        if 'value' in slots[slot]:
            arr[i] = 1

    if dialog_state in ("STARTED", "IN_PROGRESS"):
        return continue_dialog1(intent,session, arr)
    elif dialog_state == "COMPLETED":
        return statement("trip_intent", "Have a good trip")
    else:
        return statement("trip_intent", "No dialog")
   

def build_response2(message, session_attributes={}):
    response = {}
    response['version'] = '1.0'
    response['sessionAttributes'] = session_attributes
    response['response'] = message
    return response
    
def continue_dialog1(intent,session,arr):
    if not arr[0]:
        dir = [{"type": "Dialog.ElicitSlot", "slotToElicit": "name", "updatedIntent": intent}]
        out_speech = "What is your name?"
    elif not arr[1]:
        dir = [{"type": "Dialog.ElicitSlot", "slotToElicit": "PhoneNumber", "updatedIntent": intent}]
        out_speech = "Please speak out your phone number for connecting with people with similar interest?"
    else:
        name = intent['slots']['name']['value']
        user_id = session['user']['userId'].split('.')[3]
        phoneNumber = intent['slots']['PhoneNumber']['value']
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('user_id_name')
        
        table.put_item(
            Item={
                'ID': user_id,
                'Name': name,
                'PhNo':phoneNumber,
                'CanShare':'True'
            })
        card_title = "Name received"
        speech_output = "Thank You " + name +" "+". Would you like to share your day or would you like to connect with people?"
        reprompt_text = "Thank You " + name +" "+". Would you like to share your day or would you like to get some suggestions?"
        session_attributes = {}
        should_end_session = False
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
    message = {}
    message['shouldEndSession'] = False
    message['directives'] = dir
    message["outputSpeech"] = {"type": "PlainText", "text": out_speech}
    message["card"] = {"type": "Simple", "title": "SessionSpeechlet - Welcome",
                       "content": "SessionSpeechlet - Hey Vikas"}
    message["reprompt"] = {"outputSpeech": {"type": "PlainText", "text": out_speech}}
    return build_response2(message)

def continue_dialog(intent, session,arr):
    
    message = {}
    if ((not arr[3]) & (not arr[4]) & (not arr[5])):
        dir = [{"type": "Dialog.ElicitSlot", "slotToElicit": "Food", "updatedIntent": intent}]
        out_speech = "What food did you have today?"

    elif ((not arr[0]) & (not arr[3]) & (not arr[4]) & (arr[5]) & (intent['slots']['Food']["value"] not in ['no','nothing','none'])):
        dir = [{"type": "Dialog.ElicitSlot", "slotToElicit": "FoodExperience", "updatedIntent": intent}]
        out_speech = "Ohh, How was your food?"
 
    elif ((not arr[3]) & (not arr[4]) & (arr[5])):
        dir = [{"type": "Dialog.ElicitSlot", "slotToElicit": "Person", "updatedIntent": intent}]
        out_speech = "Ok, Whom did you meet today?"

    elif ((not arr[1]) & (arr[3]) & (not arr[4]) & (arr[5]) & (intent['slots']['Person']["value"] not in ['no','no one','none'])):
        dir = [{"type": "Dialog.ElicitSlot", "slotToElicit": "PersonExperience", "updatedIntent": intent}]
        out_speech = "Hmm hm, How was your meeting?"

    elif ((arr[3]) & (not arr[4]) & (arr[5])):
        dir = [{"type": "Dialog.ElicitSlot", "slotToElicit": "Place", "updatedIntent": intent}]
        out_speech = "hmm, Where did you go today?"

    elif ((not arr[2]) & (arr[3]) & (arr[4]) & (arr[5]) & (intent['slots']['Place']["value"] not in ['no','no where','none'])):
        dir = [{"type": "Dialog.ElicitSlot", "slotToElicit": "PlaceExperience", "updatedIntent": intent}]
        out_speech = "Can you tell me how was experience there?"

    else:
        food=intent['slots']['FoodExperience']
        person=intent['slots']['PersonExperience']
        place=intent['slots']['PlaceExperience']
        user_id = session['user']['userId'].split('.')[3]
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('user_emotion')
        
        if 'value' in food:
            dump_data(table,user_id,intent['slots']['Food']['value'],'Food',get_sentiment(food['value']))
        if 'value' in person:
            dump_data(table,user_id,intent['slots']['Person']['value'],'Person',get_sentiment(person['value']))
        if 'value' in place:
            dump_data(table,user_id,intent['slots']['Place']['value'],'Place',get_sentiment(place['value']))

        
       # out_speech = "Done, Have a beautiful day "+str(food_sentiment)+" "+str(person_sentiment)+" "+str(place_sertiment)
        out_speech="Done, Thank you for sharing your day. We will help you to have a great day ahead from this data."
        card = "Done, Have a beautiful day"
        reprompt = "Done, Have a beautiful day"
        return build_response({}, build_speechlet_response(
            card, out_speech, reprompt, False))

    message = {}
    message['shouldEndSession'] = False
    message['directives'] = dir
    message["outputSpeech"] = {"type": "PlainText", "text": out_speech}
    message["card"] = {"type": "Simple", "title": "SessionSpeechlet - Welcome",
                       "content": "SessionSpeechlet - Hey Vikas"}
    message["reprompt"] = {"outputSpeech": {"type": "PlainText", "text": out_speech}}
    return build_response2(message)


def my_day(intent, session, dialog_state):
    arr = [0] * 6
    slots = intent['slots']
    for i, slot in enumerate(slots):
        if 'value' in slots[slot]:
            arr[i] = 1

    if dialog_state in ("STARTED", "IN_PROGRESS"):
        return continue_dialog(intent,session, arr)
    elif dialog_state == "COMPLETED":
        return statement("trip_intent", "Have a good trip")
    else:
        return statement("trip_intent", "No dialog")


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Alexa Skills Kit sample. " \
                    "Have a nice day! "
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

# --------------- Events ------------------

def on_launch(launch_request, session):
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    return get_welcome_response(session['user']['userId'].split('.')[3])


def on_intent(intent_request, session):
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    if intent_name == "TellYourName":
        return set_name(intent, session,intent_request["dialogState"])
    elif intent_name == "MyDay":
        return my_day(intent, session, intent_request["dialogState"])
    elif intent_name == "PlaceConnect":
        return place_connect(session)
    elif intent_name == 'FoodConnect':
        return food_connect(session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response(session['user']['userId'].split('.')[3])
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])

# --------------- Main handler ------------------

def lambda_handler(event, context):
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
