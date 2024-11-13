from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate
from operator import itemgetter
import logging
import os




class QuestionGenerator:
    def __init__(self, model_name="llama3.1:latest", base_url=f"{os.getenv("OLLAMA_URL")}"):
        self.model_name = model_name
        self.base_url = base_url
        self.llm = OllamaLLM(model=model_name, base_url=base_url, temperature=0.3)
        self.question_gen_prompt = PromptTemplate(
            input_variables=["context", "n_questions", "questions"],
            template="""You are an expert at generating insightful questions for vector similarity search testing.
            
            For the following context, generate exactly {n_questions} diverse italian questions that would be effective 
            for testing information retrieval and understanding. The questions should be clear and focused.
            
            This is the Context:
            Context: 
            {context}
            
            
            These are the previous questions, you must generate new questions that are different from these:
            Questions:
            {questions}
            
            Guidelines for questions:
            - Include both factual and conceptual questions
            - Ensure questions test different aspects of the content
            - Make questions specific enough to have clear answers from the context
            - Avoid overlapping or redundant questions
            - Questions should require understanding of the context

            Generate exactly {n_questions} questions, one per line and not enumerated:"""
        )
        self.chain = (
            {"context": itemgetter("context"), 
            "n_questions": itemgetter("n_questions"),
            "questions": itemgetter("questions")}
            | self.question_gen_prompt 
            | self.llm
        )
        
    def add_strings_to_lines(self, strings):
        return '\n'.join([f"{' '.join(line)}" for line in strings])

    def generate_questions_from_chunks(self, chunk_dict, questions_per_chunk=3):
        questions_dict = {}
        
        logging.basicConfig(level=logging.INFO)

        
        for index, chunks in chunk_dict.items():
            logging.info(f"Generating questions for index {index}")
            chunk_questions = []
            
            # Create a new chain instance for each chunk
            chain = (
                {"context": itemgetter("context"), 
                "n_questions": itemgetter("n_questions"),
                "questions": itemgetter("questions")}
                | self.question_gen_prompt 
                | self.llm
            )
            
            """response = input("Start? (yes/no): ").strip().lower()
            if response != 'no':"""
            for chunk in chunks:
                """response = input("Start? (yes/no): ").strip().lower()
                if response != 'no':"""
                    # Create a new chain instance for each chunk
                chain = (
                    {"context": itemgetter("context"), 
                    "n_questions": itemgetter("n_questions"),
                    "questions": itemgetter("questions")}
                    | self.question_gen_prompt 
                    | self.llm
                )
                
                #Previous questions
                print("Previous questions:")
                for q in chunk_questions:
                    print(q)
                result = chain.invoke({
                    "context": chunk,
                    "n_questions": questions_per_chunk,
                    "questions": self.add_strings_to_lines(chunk_questions)
                })
                
                new_questions = [
                    q.strip() for q in result.split('\n') 
                    if q.strip() and '?' in q
                ]
                chunk_questions.extend(new_questions[:questions_per_chunk])
                
                # Print the generated questions before continuing
                print("Generated questions:")
                for question in new_questions:
                    print(question)
            
            questions_dict[index] = chunk_questions
        
        return questions_dict