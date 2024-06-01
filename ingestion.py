import requests
import os
from string import Template
import json
from neo4j import GraphDatabase
import glob
from timeit import default_timer as timer
from dotenv import load_dotenv
from time import sleep

from dotenv import load_dotenv

load_dotenv()

neo4j_url = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")
gds = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password))


def generate_cypher(json_obj):
    e_statements = []
    r_statements = []

    e_label_map = {}

    for i, obj in enumerate(json_obj):
        print(f"Generating cypher for file {i+1} of {len(json_obj)}")

        if "entities" not in obj or "relationships" not in obj:
            print(f"Malformed JSON object at index {i}. Skipping.")
            continue

        for entity in obj["entities"]:
            label = entity["label"]
            id = entity["id"]
            id = id.replace("-", "").replace("_", "")
            properties = {k: v for k, v in entity.items() if k not in ["label", "id"]}

            cypher = f'MERGE (n:{label} {{id: "{id}"}})'
            if properties:
                props_str = ", ".join(
                    [f'n.{key} = "{val}"' for key, val in properties.items()]
                )
                cypher += f" ON CREATE SET {props_str}"
            e_statements.append(cypher)
            e_label_map[id] = label

        for rs in obj["relationships"]:
            src_id, rs_type, tgt_id = rs.split("|")
            src_id = src_id.replace("-", "").replace("_", "")
            tgt_id = tgt_id.replace("-", "").replace("_", "")

            src_label = e_label_map[src_id]
            tgt_label = e_label_map[tgt_id]

            cypher = f'MERGE (a:{src_label} {{id: "{src_id}"}}) MERGE (b:{tgt_label} {{id: "{tgt_id}"}}) MERGE (a)-[:{rs_type}]->(b)'
            r_statements.append(cypher)

    with open("cyphers.txt", "w") as outfile:
        outfile.write("\n".join(e_statements + r_statements))

    return e_statements + r_statements

def ingestion_pipeline(arr):
    # Generate and execute cypher statements
    cypher_statements = generate_cypher(arr)
    for i, stmt in enumerate(cypher_statements):
        print(f"Executing cypher statement {i+1} of {len(cypher_statements)}")
        try:
            gds.execute_query(stmt)
        except Exception as e:
            with open("failed_statements.txt", "w") as f:
                f.write(f"{stmt} - Exception: {e}\n")
    gds.close()


with open("entity_relations.json", "r", encoding="utf-8") as f:
    arr = json.load(f)["data"]
    ingestion_pipeline(arr)