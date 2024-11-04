import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from config import secret


def generate_prologue(elements):
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=secret.OPENAI_API_KEY,
        max_tokens=500,
        temperature=0.9,
    )

    examples = [
        {
            "setting": """
                "title": "The Royal Heart's Resolve",
                "genre": "Medieval Romance",
                "theme": "Love, Courage, and Resilience",
                "tone": "Romantic, Heartwarming, and Inspirational",
                "setting": "Kingdom of Avaloria, Medieval Europe",
                "characters": "Princess Elara: A kind-hearted and strong-willed princess..."
            """,
            "answer": """
                Prologue:
                The grand ballroom of the Ashford Manor was ablaze with candlelight...
            """,
        },
        # 추가 예시들...
    ]

    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{setting}"),
            ("ai", "{answer}"),
        ]
    )

    example_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=examples,
    )

    prologue_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are an expert in fiction.
                You create only the prologue for your novel using the setting(Title, Genre, Theme, Tone, Setting, Characters) you've been given.
                Prologue is a monologue or dialog that serves to set the scene and set the tone before the main story begins.
                The novel is told from the point of view of one of the Characters.
                Just tell me the answer to the input. Don't give interactive answers.
                If there are no setting(Title, Genre, Theme, Tone, Setting, Characters) in the input, give a blank answer.
                """,
            ),
            example_prompt,
            ("human", "{setting}"),
        ]
    )

    prologue_chain = prologue_prompt | llm

    prologue = prologue_chain.invoke({"setting": elements})
    result_text = prologue.content.strip()

    try:
        return {"prologue": result_text}
    except Exception as e:
        logging.error(f"Error generating prologue with input {elements}: {e}")
        return {"prologue": ""}
