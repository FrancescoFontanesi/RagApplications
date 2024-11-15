import re
from langdetect import detect
import json
    

def clean_question_dictionary(questions_dict):
    """
    Clean questions dictionary by removing duplicates and English strings.
    """

    cleaned_dict = {}
    
    for index, questions in questions_dict.items():
        # Convert to set to remove duplicates
        unique_questions = set(questions)
        
        # Filter Italian strings
        italian_questions = []
        for question in unique_questions:
            try:
                # Check if question contains mostly Italian words
                if detect(question) == 'it':
                    italian_questions.append(question)
            except:
                # If language detection fails, keep the string
                italian_questions.append(question)
                
        # Only add index if there are questions remaining
        if italian_questions:
            cleaned_dict[index] = italian_questions
            
    return cleaned_dict

# Usage:
with open('questions.json', 'r', encoding='utf-8') as f:
    questions_dict = json.load(f)
    
cleaned_dict = clean_question_dictionary(questions_dict)

# Save cleaned dictionary
with open('cleaned_questionss.json', 'w', encoding='utf-8') as f:
    json.dump(cleaned_dict, f, ensure_ascii=False, indent=4)