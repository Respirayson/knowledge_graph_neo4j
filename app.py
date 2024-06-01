import streamlit as st
from streamlit_chat import message
from timeit import default_timer as timer

from langchain.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory


import dotenv
import os

dotenv.load_dotenv()

# OpenAI API configuration
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    safety_settings={
        HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DEROGATORY: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_TOXICITY: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_VIOLENCE: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUAL: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_MEDICAL: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    },
    temperature=0.4,
)

# Neo4j configuration
neo4j_url = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")

# Cypher generation prompt
cypher_generation_template = """
You are an expert Neo4j Cypher translator who converts English to Cypher based on the Neo4j Schema provided, following the instructions below:

1. Generate Cypher query compatible ONLY for Neo4j Version 5
2. Do not use EXISTS, SIZE, HAVING keywords in the cypher. Use alias when using the WITH keyword
3. Use only Nodes and relationships mentioned in the schema
4. Always do a case-insensitive and fuzzy search for any properties related sea rch. Eg: to search for a Person, use toLower(person.name) contains 'john'. To search for Events, use toLower(event.summary) contains 'incident' OR toLower(event.name) contains 'incident'. To search for Organizations, use toLower(organization.name) contains 'company'.
5. Never use relationships that are not mentioned in the given schema
6. When asked about events, match the properties using case-insensitive matching and the OR-operator, E.g, to find an 'incident' event, use toLower(event.summary) contains 'incident' OR toLower(event.name) contains 'incident'.

schema: {schema}

Examples:
Question: Which person participated in the most events?
Answer: MATCH (p:Person)-[:PARTICIPATED_IN]->(e:Event) RETURN p.name AS Person, COUNT(DISTINCT e) AS NumberOfEvents ORDER BY NumberOfEvents DESC

Question: Which event had the most people involved?
Answer: MATCH (e:Event)<-[:PARTICIPATED_IN]-(p:Person) RETURN e.name AS Event, COUNT(DISTINCT p) AS NumberOfPeople ORDER BY NumberOfPeople DESC

Question: Which person participated in the most events?
Answer:
MATCH (p:Person)-[:PARTICIPATED_IN]->(e:Event)
RETURN p.name AS Person, COUNT(DISTINCT e) AS NumberOfEvents
ORDER BY NumberOfEvents DESC

Question: Which organization sponsored the most events?
Answer:
MATCH (o:Organization)-[:SPONSORED]->(e:Event)
RETURN o.name AS Organization, COUNT(DISTINCT e) AS NumberOfEvents
ORDER BY NumberOfEvents DESC

Question: Which person directed the most events?
Answer:
MATCH (p:Person)-[:DIRECTED]->(e:Event)
RETURN p.name AS Person, COUNT(DISTINCT e) AS NumberOfEvents
ORDER BY NumberOfEvents DESC

Question: Which location was the scene of the most events?
Answer:
MATCH (l:Location)-[:WAS_SCENE_OF]->(e:Event)
RETURN l.name AS Location, COUNT(DISTINCT e) AS NumberOfEvents
ORDER BY NumberOfEvents DESC

Question: Which object is evidence in the most events?
Answer:
MATCH (o:Object)-[:EVIDENCE_IN]->(e:Event)
RETURN o.name AS Object, COUNT(DISTINCT e) AS NumberOfEvents
ORDER BY NumberOfEvents DESC

Question: Which organization has the most members?
Answer:
MATCH (o:Organization)-[:HAS_MEMBER]->(p:Person)
RETURN o.name AS Organization, COUNT(DISTINCT p) AS NumberOfMembers
ORDER BY NumberOfMembers DESC

Question: Which event led to the most other events?
Answer:
MATCH (e1:Event)-[:LED_TO]->(e2:Event)
RETURN e1.name AS Event, COUNT(DISTINCT e2) AS NumberOfEvents
ORDER BY NumberOfEvents DESC

Question: Which person witnessed the most events?
Answer:
MATCH (p:Person)-[:WITNESSED]->(e:Event)
RETURN p.name AS Person, COUNT(DISTINCT e) AS NumberOfEvents
ORDER BY NumberOfEvents DESC

Question: Which organization endorses terrorism in the most events?
Answer:
MATCH (o:Organization)-[:ENDORSES_TERRORISM]->(e:Event)
RETURN o.name AS Organization, COUNT(DISTINCT e) AS NumberOfEvents
ORDER BY NumberOfEvents DESC

Question: Which person is a spokesperson for the most organizations?
Answer:
MATCH (p:Person)-[:SPOKESPERSON_FOR]->(o:Organization)
RETURN p.name AS Person, COUNT(DISTINCT o) AS NumberOfOrganizations
ORDER BY NumberOfOrganizations DESC

Question: Which organization imposes sanctions on the most organizations?
Answer:
MATCH (o1:Organization)-[:IMPOSES_SANCTIONS_ON]->(o2:Organization)
RETURN o1.name AS Organization, COUNT(DISTINCT o2) AS NumberOfSanctions
ORDER BY NumberOfSanctions DESC

Question: Which person defends policy against the most organizations?
Answer:
MATCH (p:Person)-[:DEFENDS_POLICY_AGAINST]->(o:Organization)
RETURN p.name AS Person, COUNT(DISTINCT o) AS NumberOfOrganizations
ORDER BY NumberOfOrganizations DESC

Question: Which location hosts the most negotiations between organizations?
Answer:
MATCH (l:Location)-[:HOSTS_NEGOTIATIONS_BETWEEN]->(o1:Organization)<-[:HOSTS_NEGOTIATIONS_BETWEEN]-(o2:Organization)
RETURN l.name AS Location, COUNT(DISTINCT o1) AS NumberOfNegotiations
ORDER BY NumberOfNegotiations DESC

Question: Which event caused the most policy shifts in organizations?
Answer:
MATCH (e:Event)-[:CAUSES_POLICY_SHIFT_IN]->(o:Organization)
RETURN e.name AS Event, COUNT(DISTINCT o) AS NumberOfPolicyShifts
ORDER BY NumberOfPolicyShifts DESC

Question: Which organization is accused of terrorism by the most organizations?
Answer:
MATCH (o1:Organization)-[:ACCUSED_OF_TERRORISM_BY]->(o2:Organization)
RETURN o1.name AS Organization, COUNT(DISTINCT o2) AS NumberOfAccusations
ORDER BY NumberOfAccusations DESC

Question: Which person authorizes actions against the most locations?
Answer:
MATCH (p:Person)-[:AUTHORIZES_ACTION_AGAINST]->(l:Location)
RETURN p.name AS Person, COUNT(DISTINCT l) AS NumberOfActions
ORDER BY NumberOfActions DESC

Question: Which organization operates in the most locations?
Answer:
MATCH (o:Organization)-[:OPERATES_IN]->(l:Location)
RETURN o.name AS Organization, COUNT(DISTINCT l) AS NumberOfLocations
ORDER BY NumberOfLocations DESC

Question: Which object is transported to the most locations?
Answer:
MATCH (o:Object)-[:TRANSPORTED_TO]->(l:Location)
RETURN o.name AS Object, COUNT(DISTINCT l) AS NumberOfLocations
ORDER BY NumberOfLocations DESC


Question: {question}
"""

cypher_prompt = PromptTemplate(
    template=cypher_generation_template, input_variables=["schema", "question"]
)

CYPHER_QA_TEMPLATE = """You are an assistant that helps to form nice and human understandable answers.
The information part contains the provided information that you must use to construct an answer.
The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
If the provided information is empty, say that you don't know the answer.
Final answer should be easily readable and structured.
Make sure that you actually output an answer

Information:
{context}

Question: {question}
Helpful Answer:"""

qa_prompt = PromptTemplate(
    input_variables=["context", "question"], template=CYPHER_QA_TEMPLATE
)


def query_graph(user_input):
    graph = Neo4jGraph(url=neo4j_url, username=neo4j_user, password=neo4j_password)
    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        return_intermediate_steps=True,
        cypher_prompt=cypher_prompt,
        qa_prompt=qa_prompt,
    )
    result = chain(user_input)
    return result


st.set_page_config(layout="wide")

if "user_msgs" not in st.session_state:
    st.session_state.user_msgs = []
if "system_msgs" not in st.session_state:
    st.session_state.system_msgs = []

title_col, empty_col, img_col = st.columns([2, 1, 2])

with title_col:
    st.title("Terrorism Assistant")
# with img_col:
#     st.image(
#         "https://dist.neo4j.com/wp-content/uploads/20210423062553/neo4j-social-share-21.png",
#         width=200,
#     )

user_input = st.text_input("Enter your question", key="input")
if user_input:
    with st.spinner("Processing your question..."):
        st.session_state.user_msgs.append(user_input)
        start = timer()

        try:
            result = query_graph(user_input)

            intermediate_steps = result["intermediate_steps"]
            cypher_query = intermediate_steps[0]["query"]
            database_results = intermediate_steps[1]["context"]

            answer = result["result"]
            if answer == "":
                answer = "Oops... Too violent and gemini has blocked me from answering..."
            st.session_state.system_msgs.append(answer)

            st.write(f"Time taken: {timer() - start:.2f}s")

            col1, col2, col3 = st.columns([1, 1, 1])

            # Display the chat history
            with col1:
                if st.session_state["system_msgs"]:
                    for i in range(len(st.session_state["system_msgs"]) - 1, -1, -1):
                        message(
                            st.session_state["system_msgs"][i],
                            key=str(i) + "_assistant",
                        )
                        message(
                            st.session_state["user_msgs"][i],
                            is_user=True,
                            key=str(i) + "_user",
                        )

            with col2:
                if cypher_query:
                    st.text_area(
                        "Last Cypher Query", cypher_query, key="_cypher", height=240
                    )

            with col3:
                if database_results:
                    st.text_area(
                        "Last Database Results",
                        database_results,
                        key="_database",
                        height=240,
                    )
        except Exception as e:
            st.write("Failed to process question. Please try again.")
            print(e)
