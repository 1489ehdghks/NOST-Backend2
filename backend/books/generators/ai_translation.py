from langchain_openai import ChatOpenAI
from config import secret
import logging


def translate_text(content, language):
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=secret.OPENAI_API_KEY,
        temperature=0.7,
    )

    # Prepare the prompt for translation
    def prepare_input_text(text):
        if language.lower() == "korean":
            return text
        else:
            return f"Translate the following text to {language}: {text}"

    # Handle dictionary inputs
    if isinstance(content, dict):
        translated_content = {}
        for key, value in content.items():
            if isinstance(value, str):
                translated_content[key] = translate_text(value, language)
            else:
                translated_content[key] = str(value)
        return translated_content

    # Handle string inputs
    elif isinstance(content, str):
        translation_prompt = prepare_input_text(content)

        try:
            # Prepare the input for the model
            response = llm.invoke(
                {"messages": [{"role": "user", "content": translation_prompt}]}
            )

            # Ensure the response is a list and has the expected structure
            if isinstance(response, list) and len(response) > 0 and hasattr(response[0], 'content'):
                translated_text = response[0].content.strip()
            else:
                logging.warning(f"AI model did not return a valid response for input: {
                                translation_prompt}")
                return content

            return translated_text if translated_text else content

        except Exception as e:
            logging.error(f"Error during translation for input: '{
                          content}'. Error: {e}")
            return content

    else:
        logging.error(f"Invalid input type for translation: {
                      type(content)}. Input data: {content}")
        return str(content)
