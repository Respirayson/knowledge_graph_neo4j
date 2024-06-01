import requests
import os
from string import Template
import json
from neo4j import GraphDatabase
import glob
from timeit import default_timer as timer
from dotenv import load_dotenv
from time import sleep


def post_to_server(prompt, data):
    url = "http://localhost:8000/"
    payload = {
        "prompt": prompt,
        "data": data
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.text
    else:
        print("Error:", response.status_code, response.text)

def load_and_send_articles():
    prompt = """
From the Article Brief below, extract the following Entities & relationships described in the mentioned format 
0. ALWAYS FINISH THE OUTPUT. Never send partial responses
1. First, look for these Entity types in the text and generate as comma-separated format similar to entity type.
   `id` property of each entity must be alphanumeric and must be unique among the entities. You will be referring this property to define the relationship between entities. Document must be summarized and stored inside Event entity under `summary` property. You will have to generate as many entities as needed as per the types below:
    Entity Types:
    label:'Event', id:string, name:string; summary:string //Event mentioned in the brief; `id` property is the name of the event, in lowercase, with no capital letters, special characters, spaces or hyphens; Contents of original document must be summarized inside 'summary' property
    label:'Person', id:string, name:string //Person involved in the event; `id` property is the name of the person, in camel-case.
    label:'Organization', id:string, name:string //Organization involved in the event; `id` property is the name of the organization, in camel-case.
    label:'Location', id:string, name:string //Location involved in the event; `id` property is the name of the location, in camel-case.
    label:'Object', id:string, name:string //Object involved in the event; `id` property is the name of the object, in camel-case.
    
2. Next generate each relationships as triples of head, relationship and tail. To refer the head and tail entity, use their respective `id` property. Relationship property should be mentioned within brackets as comma-separated. They should follow these relationship types below. You will have to generate as many relationships as needed as defined below:
    Relationship types:
    person|PARTICIPATED_IN|event
    organization|SPONSORED|event
    person|DIRECTED|event
    location|WAS_SCENE_OF|event
    object|EVIDENCE_IN|event
    organization|HAS_MEMBER|person
    event|LED_TO|event
    person|WITNESSED|event
    organization|ENDORSES_TERRORISM|event
    person|SPOKESPERSON_FOR|organization
    organization|IMPOSES_SANCTIONS_ON|organization
    person|DEFENDS_POLICY_AGAINST|organization
    location|HOSTS_NEGOTIATIONS_BETWEEN|organization_and_organization
    event|CAUSES_POLICY_SHIFT_IN|organization
    organization|ACCUSED_OF_TERRORISM_BY|organization
    person|AUTHORIZES_ACTION_AGAINST|location
    organization|OPERATES_IN|location
    object|TRANSPORTED_TO|location

3. The output should look like:
{
    "entities": [
        {"label":"Event", "id":string, "name":string, "summary":string},
        {"label":"Person", "id":string, "name":string},
        {"label":"Organization", "id":string, "name":string},
        {"label":"Location", "id":string, "name":string},
        {"label":"Object", "id":string, "name":string}
    ],
    "relationships": [
        "personID|PARTICIPATED_IN|eventID",
        "organizationID|SPONSORED|eventID",
        "personID|DIRECTED|eventID",
        "locationID|WAS_SCENE_OF|eventID",
        "objectID|EVIDENCE_IN|eventID",
        "organizationID|HAS_MEMBER|personID",
        "eventID|LED_TO|eventID",
        "personID|WITNESSED|eventID",
        "organizationID|ENDORSES_TERRORISM|eventID",
        "personID|SPOKESPERSON_FOR|organizationID",
        "organizationID|IMPOSES_SANCTIONS_ON|organizationID",
        "personID|DEFENDS_POLICY_AGAINST|organizationID",
        "locationID|HOSTS_NEGOTIATIONS_BETWEEN|organizationID_and_organizationID",
        "eventID|CAUSES_POLICY_SHIFT_IN|organizationID",
        "organizationID|ACCUSED_OF_TERRORISM_BY|organizationID",
        "personID|AUTHORIZES_ACTION_AGAINST|locationID",
        "organizationID|OPERATES_IN|locationID",
        "objectID|TRANSPORTED_TO|locationID"
    ]
}
"""
    results = []
    # Load articles from the JSON file
    with open('articles.json', 'r', encoding='utf-8') as file:
        articles = json.load(file)["articles"]
    
    # Loop through each article and post it to the server
    for article in articles:
        data = post_to_server(prompt, article["data"])
        # data = json.loads(data)
        # with open("test.json", "w") as f:
        #   f.write(json.dumps(data))

        results.append(json.loads(data))
    return results

print(load_and_send_articles())
