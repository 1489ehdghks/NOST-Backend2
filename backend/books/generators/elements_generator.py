# elements_generator.py
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from config import secret


def generate_elements(user_prompt, language):
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=secret.OPENAI_API_KEY,
        temperature=0.8,
    )

    if language.lower() == "korean":
        examples = [
            {
                "user_prompt": "중세 시대의 판타지 소설 설정을 만들어 주세요.",
                "answer": """
                    Title: 돌의 마음
                    Genre: 중세 로맨스 판타지
                    Theme: 역경을 이겨낸 사랑, 용기, 그리고 구원
                    Tone: 가슴 아프고, 매혹적이며, 긴장감 있는
                    Setting: 엘도리아 왕국은 광활한 초원, 울창한 마법의 숲, 그리고 위엄 있는 성들이 특징인 생동감 넘치는 영역입니다. 이곳은 마법과 신화적 생명체들이 숨쉬는 세계로, 전쟁의 위기 속에서 정치적 긴장감이 도사리고 있습니다.
                    Characters:
                    레이디 이졸드 오브 쏜리지: 강한 의지를 가진 귀족 여성, 가족과 사랑 사이에서 갈등함.
                    용감한 세드릭 경: 과거의 괴로움에 시달리며 이졸드를 사랑하게 되는 기사.
                    마법사 엘라라: 주인공들을 감정적 여정으로 이끄는 신비로운 요정.
                """,
            }
        ]
    else:
        examples = [
            {
                "user_prompt": "Create a medieval fantasy novel setting.",
                "answer": """
                    Title: Hearts of Stone
                    Genre: Medieval Romance Fantasy
                    Theme: Love Against the Odds, Courage, and Redemption
                    Tone: Poignant, Enchanting, and Tense
                    Setting: The Kingdom of Eldoria is a vibrant realm characterized by vast plains, dense enchanted forests, and majestic castles. It is a land ruled by a feudal system where knights uphold honor and courage, and mythical creatures such as fairies, elves, and dragons inhabit hidden corners of the world. The kingdom stands on the brink of war, with political tensions and old rivalries threatening the fragile peace.
                    Characters:
                    Lady Isolde of Thornridge: A noblewoman with a strong will, torn between duty to her family and a desire for true love.
                    Sir Cedric the Brave: A knight burdened by past sorrows, struggling with his growing feelings for Isolde.
                    Elara the Sorceress: A mystical fae who guides Isolde and Cedric on an emotional journey.
                """,
            }
        ]

    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{user_prompt}"),
            ("ai", "{answer}"),
        ]
    )

    example_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=examples,
    )

    elements_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert in novel settings. Create detailed settings for a novel based on the user's input. Follow the structure shown in the examples."
            ),
            example_prompt,
            ("human", "{user_prompt}"),
        ]
    )

    elements_chain = elements_prompt | llm
    elements = elements_chain.invoke({"user_prompt": user_prompt})

    result_text = elements.content.strip()
    logging.debug(f"Generated Elements: {result_text}")

    # 결과 파싱 로직
    try:
        result_lines = result_text.split("\n")
        data = {"title": "", "genre": "", "theme": "",
                "tone": "", "setting": "", "characters": ""}
        current_key = None

        for line in result_lines:
            line = line.strip()
            if line.startswith("Title:"):
                data["title"] = line.split("Title:", 1)[1].strip()
                current_key = "Title"
            elif line.startswith("Genre:"):
                data["genre"] = line.split("Genre:", 1)[1].strip()
                current_key = "Genre"
            elif line.startswith("Theme:"):
                data["theme"] = line.split("Theme:", 1)[1].strip()
                current_key = "Theme"
            elif line.startswith("Tone:"):
                data["tone"] = line.split("Tone:", 1)[1].strip()
                current_key = "Tone"
            elif line.startswith("Setting:"):
                data["setting"] = line.split("Setting:", 1)[1].strip()
                current_key = "Setting"
            elif line.startswith("Characters:"):
                data["characters"] = line.split("Characters:", 1)[1].strip()
                current_key = "Characters"
            elif current_key == "Characters":
                if len(data["characters"]) + len(line) > 200:  # 200자 제한
                    continue
                data["characters"] += " " + line

            data["characters"] = data["characters"].strip()

        return data
    except Exception as e:
        logging.error(f"Error parsing elements response: {e}")
        return {
            "title": "",
            "genre": "",
            "theme": "",
            "tone": "",
            "setting": "",
            "characters": "",
        }
