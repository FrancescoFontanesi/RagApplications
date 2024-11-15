from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate
from operator import itemgetter
from sentence_transformers import SentenceTransformer
import logging
import os
from typing import List
from dotenv import load_dotenv
load_dotenv()


class QuestionGenerator:

    def __init__(self, model_name="llama3.1:latest", base_url=f"{os.getenv('OLLAMA_URL')}", embedder="efederici/sentence-BERTino"):
        self.model_name = model_name
        self.base_url = base_url
        self.embedder = SentenceTransformer(embedder)
        self.llm = OllamaLLM(
            model=model_name, base_url=base_url, temperature=0.3)
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

                # Previous questions
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


class RagPipeline:
    def __init__(self, model_name="llama3.2:latest", base_url=f"{os.getenv('OLLAMA_URL')}", embedder="efederici/sentence-BERTino"):
        self.model_name = model_name
        self.base_url = base_url
        self.embedder = SentenceTransformer(embedder)
        self.llm = OllamaLLM(
            model=model_name, base_url=base_url, temperature=0.3)

        self.tetras_rag_prompt = PromptTemplate(
            input_variables=["contexts", "question"],
            template="""Sei un esperto di manuali di utilizzo di TETRAS, specializzato nell'assistenza tecnica e nel supporto agli utenti.

            I seguenti contesti sono ordinati per rilevanza (dal più al meno pertinente, 1 è il più pertinente è 5 il meno pertitente):

            {contexts}

            Domanda dell'utente:
            {question}

            Istruzioni per la risposta:
            - Dai maggior peso alle informazioni dai contesti più rilevanti (primi della lista)
            - Se nessun contesto è fornito, spiega che puoi rispondere solo a domande relative al manuale Tetras
            - Basati esclusivamente sulle informazioni fornite nei contesti
            - Mantieni un tono professionale e tecnico
            - Ogni contesto e clasificato con una posizione che implica quanto esso sia simile alla domanda forinta dall'utente, 1 è il più simile è 5 il meno simile

            Risposta:
            """
        )

    def extract_contexts(self, context_list) -> List[str]:
        contexts = []
        for c in context_list:
            contexts.append(c[0])
        return contexts

    def extract_indecies(self, context_list) -> List[str]:
        indecies = []
        for c in context_list:
            indecies.append(c[1])
        return indecies

    def format_contexts(self, context_list: List[str]) -> str:
        """Format context list with relevance markers"""
        formatted_contexts = []
        for i, ctx in enumerate(context_list, 1):
            formatted_contexts.append(
                f"Contesto classificato con posizione{i}:\n{ctx}\n")
        return "\n".join(formatted_contexts)

    def process_contexts(self, contexts: List[str]) -> List[str]:
        processed_contexts = []
        for c in contexts:
            if c[2] > 0.5:
                processed_contexts.append(c)
        return processed_contexts

    def answer_question(self, results, question):
        contexts = self.process_contexts(results)

        # Instruct the chain
        chain = (
            {"contexts": itemgetter("contexts"),
                "question": itemgetter("question")}
            | self.question_gen_prompt
            | self.llm
        )
        # Extract the indices
        indecies = self.extract_indecies(results)
        contexts = self.extract_contexts(results)
        # Resolve the chain (one for each question)
        answer = chain.invoke({
            "contexts": self.format_contexts(contexts),
            "question": question
        })

        return answer, indecies
