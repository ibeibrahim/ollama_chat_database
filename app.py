from langchain_community.chat_models import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st

def connectDatabase(username, port, host, password, database):
    mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
    st.session_state.db = SQLDatabase.from_uri(mysql_uri)


def runQuery(query):
    return st.session_state.db.run(query) if st.session_state.db else "Please connect to database"


def getDatabaseSchema():
    return st.session_state.db.get_table_info() if st.session_state.db else "Please connect to database"


llm = ChatOllama(model="llama3")
def getQueryFromLLM(question):
    template = """below is the schema of MYSQL database, read the schema carefully about the table and column names. Also take care of table or column name case sensitivity.
        Finally answer user's question in the form of SQL query.

        {schema}

        please only provide the SQL query and nothing else

        for example:
        question: how many waste management company we have in database
        SQL query: SELECT COUNT(*) FROM PERUSAHAAN_LIMBAH;
        question: how many waste management company are from Cimahi in the database ?
        SQL query: SELECT COUNT(*) FROM PERUSAHAAN_LIMBAH WHERE kota_perusahaan_limbah="KOTA CIMAHI";

        your turn :
        question: {question}
        SQL query :
        please only provide the SQL query and nothing else
        """

    prompt = ChatPromptTemplate.from_template(template)

    chain = prompt | llm

    response = chain.invoke({
        "question": question,
        "schema": getDatabaseSchema()
    })
    return response.content

def getResponseForQueryResult(question, query, result):
    template2 = """below is the schema of MYSQL database, read the schema carefully about the table and column names of each table.
    Also look into the conversation if available
    Finally write a response in natural language by looking into the conversation and result.

    {schema}

    Here are some example for you:
    question: how many waste management company we have in database
    SQL query: SELECT COUNT(*) FROM PERUSAHAAN_LIMBAH;
    Result: [(10,)]
    Response: We have 10 waste management companies in the database.

    question: how many waste management company are from Cimahi in the database ?
    SQL query: SELECT COUNT(*) FROM PERUSAHAAN_LIMBAH WHERE kota_perusahaan_limbah="KOTA CIMAHI";
    Result: [(2,)]
    Response: We have 2 waste management companies from Cimahi in the database.

    question: How many vehicles are categorized as "DUMP TRUCK" in the database?
    SQL query: SELECT COUNT(*) FROM transportasi WHERE jenis_kendaraan = 'DUMP TRUCK';
    Result: [(3,)]
    Response: There are 3 vehicles categorized as "DUMP TRUCK" in the database.

    question: How many types of inorganic waste are processed using the "REUSE" method?
    SQL query: SELECT COUNT(*) FROM pengolahan_anorganik WHERE cara_pengolahan = 'REUSE';
    Result: [(4,)]
    Response: There are 4 types of inorganic waste processed using the "REUSE" method in the database.

    question: What are the names of the companies based in "KOTA CIMAHI"?
    SQL query: SELECT nama_perusahaan_limbah FROM perusahaan_limbah WHERE kota_perusahaan_limbah = 'KOTA CIMAHI';
    Result: [('PT. ABC',), ('PT. XYZ',)]
    Response: The companies based in "KOTA CIMAHI" are PT. ABC and PT. XYZ.

    your turn to write response in natural language from the given result :
    question: {question}
    SQL query : {query}
    Result : {result}
    Response :
    """

    prompt2 = ChatPromptTemplate.from_template(template2)
    chain2 = prompt2 | llm
    response = chain2.invoke({
        "question": question,
        "schema": getDatabaseSchema(),
        "query": query,
        "result": result
    })

    return response.content

st.set_page_config(
    page_title="Chat with MYSQL Database",
    page_icon=":bar_chart:",
    layout="centered",
)

question = st.chat_input("Chat with your database")

if "chat" not in st.session_state:
    st.session_state.chat = []

if question:
    if "db" not in st.session_state:
        st.error('Please connect database first.')
    else:
        st.session_state.chat.append({
            "role": "user",
            "content": question
        })

        query = getQueryFromLLM(question)
        print(query)
        result = runQuery(query)
        print(result)
        response = getResponseForQueryResult(question, query, result)
        st.session_state.chat.append({
            "role": "assistant",
            "content": response
        })

for chat in st.session_state.chat:
    st.chat_message(chat['role']).markdown(chat['content'])

with st.sidebar:
    st.title('Connect to database')
    st.text_input(label="Host", key="host", value="localhost")
    st.text_input(label="Port", key="port", value="3306")
    st.text_input(label="Username", key="username", value="root")
    st.text_input(label="Password", key="password", value="", type="password")
    st.text_input(label="Database", key="database", value="manajemensampah")
    connectBtn = st.button("Connect")


if connectBtn:
    connectDatabase(
        username=st.session_state.username,
        port=st.session_state.port,
        host=st.session_state.host,
        password=st.session_state.password,
        database=st.session_state.database,
    )

    st.success("Database connected")