from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate
from operator import itemgetter


class QuestionGenerator:
    def __init__(self, model_name="llama3.1:70b", base_url="http://192.168.100.149:8537"):
        self.model_name = model_name
        self.base_url = base_url
        self.llm = OllamaLLM(model=model_name, base_url=base_url)
        self.question_gen_prompt = PromptTemplate(
            input_variables=["context", "n_questions"],
            template="""You are an expert at generating insightful questions for vector similarity search testing.
            
            For the following context, generate exactly {n_questions} diverse questions that would be effective 
            for testing information retrieval and understanding. The questions should be clear and focused.

            Context: {context}

            Guidelines for questions:
            - Include both factual and conceptual questions
            - Vary question types (what, how, why, explain)
            - Ensure questions test different aspects of the content
            - Make questions specific enough to have clear answers from the context
            - Avoid overlapping or redundant questions
            - Questions should require understanding of the context

            Generate exactly {n_questions} questions, one per line:"""
        )
        self.chain = (
            {"context": itemgetter("context"), 
            "n_questions": itemgetter("n_questions")} 
            | self.question_gen_prompt 
            | self.llm
        )

    def generate_questions_from_chunks(self, chunk_dict, questions_per_chunk=3):
        questions_dict = {}
        
        for index, chunks in chunk_dict.items():
            chunk_questions = []
            
            for chunk in chunks:
                result = self.chain.invoke({
                    "context": chunk,
                    "n_questions": questions_per_chunk
                })
                
                new_questions = [
                    q.strip() for q in result.split('\n') 
                    if q.strip() and '?' in q
                ]
                
                chunk_questions.extend(new_questions[:questions_per_chunk])
            
            questions_dict[index] = chunk_questions
        
        return questions_dict