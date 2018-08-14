import boto3
from boto3.dynamodb.conditions import Key, Attr

def connect_peope_food(session,user_credentials_table_name='user_id_name',user_emotions_table_name='user_emotion'):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_emotions_table = dynamodb.Table(user_emotions_table_name)
    user_id = session['user']['userId'].split('.')[3]
    Items = (user_emotions_table.query(
        KeyConditionExpression=Key('ID').eq(user_id))['Items']
    )
    food = []
    
    for item in Items:
        if item['EntityType'] == 'Food':
            food.append((item['EntityName'], item['Sentiment']))
    
    food = sorted(food, key=lambda x: x[1], reverse=True)[:3]
    print("food is asdf: ", food)
    top_matches = {}
    
    for item in (user_emotions_table.scan(FilterExpression=((Attr('Sentiment').gt('0.7') & (
            Attr('EntityName').eq(food[0][0]) or Attr('EntityName').eq(food[1][0]) or Attr('EntityName').eq(food[2][0]))))))['Items']:
        if item['ID'] != user_id:
            if item['ID'] in top_matches:
                top_matches[item['ID']] = top_matches['ID'] + item['Sentiment']
            else:
                top_matches[item['ID']] = item['Sentiment']

    top_matches = sorted(top_matches.items(), key=lambda x: x[1])[:3]
    user_credentials_table = dynamodb.Table(user_credentials_table_name)
    name_ph_no="Here are few matches. "
    for match in top_matches:
        res = user_credentials_table.query(KeyConditionExpression=Key('ID').eq(match[0]))['Items'][0]
        if res['CanShare']:
            name_ph_no=name_ph_no+" Name: "+res['Name']+ ",Phone No:, " +", ".join(str(res['PhNo'])) + ". "
    return name_ph_no

def connect_peope_place(session, user_credentials_table_name='user_id_name', user_emotions_table_name='user_emotion'):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    user_emotions_table = dynamodb.Table(user_emotions_table_name)
    user_id = session['user']['userId'].split('.')[3]
    Items = (user_emotions_table.query(
        KeyConditionExpression=Key('ID').eq(user_id))['Items']
    )
    place = []

    for item in Items:
        if item['EntityType'] == 'Place':
            place.append((item['EntityName'], item['Sentiment']))

        place = sorted(place, key=lambda x: x[1], reverse=True)[:3]
    top_matches = {}

    for item in (user_emotions_table.scan(FilterExpression=((Attr('Sentiment').gt('0.7') & (
            Attr('EntityName').eq(place[0][0]) or Attr('EntityName').eq(place[1][0]) or Attr('EntityName').eq(
        place[2][0]))))))['Items']:
        if item['ID'] != user_id:
            if item['ID'] in top_matches:
                top_matches[item['ID']] = top_matches['ID'] + item['Sentiment']
            else:
                top_matches[item['ID']] = item['Sentiment']

    top_matches = sorted(top_matches.items(), key=lambda x: x[1])[:3]
    user_credentials_table = dynamodb.Table(user_credentials_table_name)
    name_ph_no="Here are few matches. "
    for match in top_matches:
        res = user_credentials_table.query(KeyConditionExpression=Key('ID').eq(match[0]))['Items'][0]
        if res['CanShare']:
            name_ph_no=name_ph_no+" Name: "+res['Name']+ ",Phone No:, " +", ".join(str(res['PhNo'])) + ". "
    return name_ph_no
