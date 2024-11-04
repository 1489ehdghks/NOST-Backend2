import logging
import re
import time
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationSummaryBufferMemory
from .ai_translation import translate_text
from config import secret


def generate_summary(chapter_num, summary, elements, prologue, language):
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=secret.OPENAI_API_KEY,
        temperature=1.2
    )

    memory = ConversationSummaryBufferMemory(
        llm=llm, max_token_limit=20000, memory_key="chat_history", return_messages=True
    )

    stages = [
        "writes Expositions that introduce the characters and setting of your novel and where events take place.",
        "writes Development which a series of events leads to conflict between characters.",
        "writes crises, where a reversal of events occurs, a new situation emerges, and the protagonist ultimately fails.",
        "writes a climax in which a solution to a new situation is realized, the protagonist implements it, and the conflict shifts.",
        "writes endings where the protagonist wraps up the case, all conflicts are resolved, and the story ends.",
    ]

    current_stage, next_stage = None, None

    for i in range(5):
        if (chapter_num-1)//6 == i:
            current_stage = stages[i]
            next_stage = stages[i+1] if chapter_num % 6 == 0 and i + \
                1 < len(stages) else stages[i]

    example_prompts = [
        {
            "summary": "Write a concise summary of the first chapter where the protagonist meets a mysterious informant.",
            "answer": """
                James Worthington prowled the fog-drenched streets of Victorian London. A note directed him to a secluded meeting. As he approached, a man in a long, dark coat emerged from the mist. The informant's voice was urgent: "They're watching, detective." He handed over a ledger filled with cryptic entries, urging James to uncover the truth before disappearing into the fog.
            """
        },
        {
            "summary": "Write a concise summary of the chapter where the protagonist faces their first major obstacle.",
            "answer": """
                James's investigation led him to Lord Blackwood's mansion. Disguised as a social call, he navigated the grand halls to find crucial evidence. As he rifled through drawers, Lord Blackwood entered. "What are you doing here, Worthington?" A tense exchange ensued, and James narrowly escaped, realizing Blackwood was onto him.
            """
        },
        {
            "summary": "Write a concise summary of the chapter where the protagonist discovers a shocking secret.",
            "answer": """
                In an abandoned library, James found letters from his late father, revealing a link to a criminal syndicate. The final letter detailed his father's regret and attempt to escape the syndicate. This revelation shook James, fueling his determination to bring the truth to light.
            """
        },
        {
            "summary": "Write a concise summary of the chapter where the protagonist forms an unexpected alliance.",
            "answer": """
                In a seedy tavern, James met Lila, a master thief. Initially tense, they formed an uneasy alliance. Lila's underworld knowledge and James's quest for truth aligned, and they planned to infiltrate the syndicate's stronghold together.
            """
        }
    ]

    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{summary}"),
            ("ai", "{answer}"),
        ]
    )

    example_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=example_prompts,
    )

    summary_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an experienced novelist who {{current_stage}}.
                Write a concise, character-focused summary of the next events in the story.
                Focus on the actions, decisions, and emotions of the characters.
                Avoid generic descriptions of suspense or tension.
                Ensure the summary flows smoothly from the prologue and adds new developments.
                """,
            ),
            example_prompt,
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{prompt}"),
        ]
    )

    recommend_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""
                You are an experienced novelist who {{next_stage}}.
                Based on the current summary prompt, provide three compelling recommendations for the next part of the summary.
                Be extremely contextual and realistic with your recommendations.
                Each recommendation should have 'Title': 'Description'. For example: 'James discovers a hidden clue': 'James finds a hidden compartment in the desk, revealing a map that leads to a secret location.'
                Limit the length of each description to 1-2 sentences.
                """,
            ),
            example_prompt,
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{current_story}"),
        ]
    ) if chapter_num <= 29 else None

    def load_memory():
        return memory.load_memory_variables({})["chat_history"]

    def parse_recommendations(recommendation_text):
        recommendations = []
        try:
            rec_lines = recommendation_text.split("\n")
            title, description = None, None
            for line in rec_lines:
                if line.startswith("Title:"):
                    if title and description:
                        recommendations.append(
                            {"Title": title, "Description": description}
                        )
                    title = line.split("Title:", 1)[1].strip()
                    description = None
                elif line.startswith("Description:"):
                    description = line.split("Description:", 1)[1].strip()
                    if title and description:
                        recommendations.append(
                            {"Title": title, "Description": description}
                        )
                        title, description = None, None
                if len(recommendations) == 3:
                    break
        except Exception as e:
            logging.error(f"Error parsing recommendations: {e}")

        return recommendations

    def generate_recommendations(chat_history, current_story, next_stage, language):
        if not recommend_template:
            return None

        formatted_recommendation_prompt = recommend_template.format(
            chat_history=chat_history,
            current_story=current_story,
            next_stage=next_stage,
        )
        logging.debug(f"Formatted Recommendation Prompt: {
                      formatted_recommendation_prompt}")

        try:
            translations = {}
            for attempt in range(3):
                recommendation_result = llm.invoke(
                    formatted_recommendation_prompt)
                logging.debug(f"Recommendation Result: {
                              recommendation_result.content}")

                if recommendation_result.content:
                    recommendations = parse_recommendations(
                        recommendation_result.content)
                    if recommendations:
                        translated_recommendations = []
                        for rec in recommendations:
                            title = rec["Title"]
                            description = rec["Description"]

                            # 번역 결과를 캐싱하여 동일한 텍스트는 한 번만 번역
                            if title not in translations:
                                translations[title] = translate_text(
                                    title, language)
                            if description not in translations:
                                translations[description] = translate_text(
                                    description, language)

                            translated_recommendations.append({
                                "Title": translations[title],
                                "Description": translations[description],
                            })
                        return translated_recommendations

                logging.warning(f"Recommendation attempt {
                                attempt + 1} failed, retrying...")
                time.sleep(1 * (attempt + 1))  # 백오프 전략 적용

        except Exception as e:
            logging.error(f"Error during recommendation generation: {e}")
            time.sleep(1 * (attempt + 1))
        return None

    def remove_recommendation_paths(final_summary):
        pattern = re.compile(r"Recommended summary paths:.*$", re.DOTALL)
        cleaned_story = re.sub(pattern, "", final_summary).strip()
        return cleaned_story

    chat_history = load_memory()
    prompt = f"""
    Story Elements: {elements}
    Prologue: {prologue}
    Story Prompt: {summary}
    Previous Story: {chat_history}
    Write a concise, realistic, and engaging summary of the next events in the story. Highlight both hope and despair in the narrative. Make it provocative and creative.
    Ensure the summary continues smoothly from the prologue, without repeating information.
    Focus on new developments, character arcs, and plot progression.
    """
    formatted_final_prompt = summary_template.format(
        chat_history=chat_history, prompt=prompt, current_stage=current_stage
    )
    logging.debug(f"Formatted Final Prompt: {formatted_final_prompt}")
    result = llm.invoke(formatted_final_prompt)
    logging.debug(f"Summary Result: {result.content}")
    memory.save_context({"input": prompt}, {"output": result.content})

    cleaned_story = remove_recommendation_paths(result.content)
    cleaned_story = translate_text(cleaned_story, language)
    recommendations = generate_recommendations(
        chat_history, result.content, next_stage, language
    )
    return {"final_summary": cleaned_story, "recommendations": recommendations}
