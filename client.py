__author__ = 'Admin'
import requests
from urllib.request import Request, urlopen
import urllib.parse
import json

BASE_URL = "http://127.0.0.1:5000/"
LOGIN_GET_URL = BASE_URL + 'login?username={username}&password={password}'
LOGIN_POST_URL = BASE_URL + 'login'
REGISTER_URL = BASE_URL + 'register?username={username}&password={password}&email={email}&first_name={first_name}&' \
                          'last_name={last_name}'
USERS_URL = BASE_URL + 'users'
GET_MAIL = BASE_URL + 'email/{username}'
GET_FRIENDS = BASE_URL + 'friends/{friend_type}/{username}'


def login_get(username="admin", password="admin"):
    req = Request(LOGIN_GET_URL.format(username=username, password=password))
    response = json.loads(urlopen(req).read())
    message = response['message']
    print(message)
    if 'access_token' in response:
        return response['access_token']
    else:
        raise Exception("failed to login")


def login_post(username="admin", password="admin"):
    data = urllib.parse.urlencode({'username': username, 'password': password})
    req = Request(LOGIN_POST_URL, data=data.encode('UTF-8'))
    try:
        response = json.loads(urlopen(req).read())
        message = response['message']
        print(message)

        if 'access_token' in response:
            return response['access_token']
        else:
            raise Exception("failed to login")
    except:
        print('exception')


def get_mail(username, token):
    req = Request(GET_MAIL.format(username=username))
    req.add_header('Authorization', 'Bearer ' + token)
    response = json.loads(urlopen(req).read())
    return response


def put_mail(username, email, token):
    data = {'email': email}
    headers = {'Authorization':'Bearer ' + token}
    response = requests.put(GET_MAIL.format(username=username), data=data, headers=headers)
    return response


def register(username, password, email, first_name, last_name):
    req = Request(REGISTER_URL.format(username=username, password=password, email=email, first_name=first_name,
                                      last_name=last_name))
    response = json.loads(urlopen(req).read())
    message = response['message']
    print(message)
    if 'access_token' in response:
        return response['access_token']
    else:
        raise Exception("failed to register")


def get_friends(username, friend_type, token):
    req = Request(GET_FRIENDS.format(username=username, friend_type=friend_type))
    req.add_header('Authorization', 'Bearer ' + token)
    response = json.loads(urlopen(req).read())
    return response

def add_friend(username, new_friend, token):
    data = {'friend': new_friend}
    headers = {'Authorization':'Bearer ' + token}
    response = requests.put(GET_FRIENDS.format(username=username), data=data, headers=headers)
    return response, response.content

def get_users(token):
    req = Request(USERS_URL)
    req.add_header('Authorization', 'Bearer ' + token)
    response = json.loads(urlopen(req).read())
    return response