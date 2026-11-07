
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)

response = llm.invoke(
    "Explain Python lists in 2 simple sentences."
)

print("\nGroq Response:")
print(response.content)
