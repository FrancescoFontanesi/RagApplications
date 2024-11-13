import fitz  # PyMuPDF
import re
from langchain.text_splitter import TokenTextSplitter
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import psycopg
from psycopg.rows import dict_row
import logging
from sqlalchemy import text
import FlexibleChunker as fc 
import numpy as np

  

class DocumentProcessor:
    def __init__(self, model_name="efederici/sentence-BERTino"):
        self.model = SentenceTransformer(model_name)
        self.document_path=r"D:\RagApplications\Documenti\ManualeTETRAS_modificato2.pdf"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    

    def extract_subtitles_and_text(self, start_page=0):
        document = fitz.open(self.document_path)
        subtitles_dict = {}
        pattern = re.compile(r'\d+\.\d+')
        current_subtitle = None
        current_subtitle_name = None
        current_text = ""

        for page_num in range(start_page, len(document)):
            page = document.load_page(page_num)
            text = page.get_text("text")
            lines = text.split('\n')

            for i, line in enumerate(lines):
                if pattern.match(line.strip()):
                    if current_subtitle:
                        subtitles_dict[current_subtitle] = (current_subtitle_name.replace(".", ""), re.sub(r'\d+', '', current_text).strip())
                    current_subtitle = line.strip().split()[0]
                    if len(line.strip().split()) > 1:
                        current_subtitle_name = ' '.join(line.strip().split()[1:])
                    else:
                        current_subtitle_name = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    current_text = ""
                elif line.strip() != current_subtitle_name:
                    current_text += " " + line.strip()

            if current_subtitle:
                subtitles_dict[current_subtitle] = (current_subtitle_name.replace(".", ""), re.sub(r'\d+', '', current_text).strip())
                
        subtitles_dict.pop("4.2", None)
        return subtitles_dict


    def chunk_text(self, text, chunk_size=768,overlap_size=70): 
        semantic_splitter = TokenTextSplitter(
        chunk_size=chunk_size,    # Number of characters per chunk
        chunk_overlap=overlap_size   # Overlap to preserve context
        )
        chunks = semantic_splitter.split_text(text)
    
        return chunks



    def generate_chunked_dictionaries(self, data_dict, chunk_size=768, overlap_percentage=[0.1, 0.2, 0.3]):
        
        dictList = []
        for overlap in overlap_percentage:
            overlap = int(chunk_size * overlap)
            chunked_subtitles_dict = data_dict.copy()
            for subtitle, text in data_dict.items():
                if len(text[1]) <= int(chunk_size*3.5):
                    chunked_subtitles_dict[subtitle] = [text[1]]
                else:
                    chunked_subtitles_dict[subtitle] = self.chunk_text(text[1], overlap_size=overlap)
            dictList.append(chunked_subtitles_dict)
        return dictList
        

    def generate_chunked_dictionary_ii(self, data_dict):
        chunked_subtitles_dict = data_dict.copy()
        for subtitle, text in data_dict.items():
            document = self.chunk_text(text[1], chunk_size=768, overlap_size=0)
            chunked_subtitles_dict[subtitle] = (document,[self.chunk_text(large_chunk,128, 28) for large_chunk in document])
        return chunked_subtitles_dict
    
    def generate_question_dictionary(self, data_dict, chunk_size : int = 350):

        chunker = fc.FlexibleChunker(target_chunk_size=chunk_size)

        dict_for_questions = {}

        for subtitle, text in data_dict.items():
            dict_for_questions[subtitle] = chunker.chunk_text(text[1])

        for subtitle, text in dict_for_questions.items():
            if len(self.tokenizer.encode(text[-1])) < 100 and len(text) > 1:
                text[-2] += " " + text[-1]
                text.pop(-1)
        return dict_for_questions
    
    def register_vector_type(self, conn):
        """Register vector type for psycopg3 connection"""
        try:
            with conn.cursor() as cur:
                # Check if vector type exists
                cur.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_type 
                    WHERE typname = 'vector'
                );
                """)
                vector_exists = cur.fetchone()[0]
                
                if not vector_exists:
                    raise Exception("Vector type not found in database. Make sure pgvector extension is installed.")
                
                # Register the vector type
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                
        except Exception as e:
            logging.error(f"Error registering vector type: {e}")
            raise


    def get_connection_to_sql_database(self, host="localhost", data_base_name="database", username="postgres", password="postgres", port="5432"):
        g_uri = f"postgresql://{username}:{password}@{host}:{port}/{data_base_name}"
        return psycopg.connect(g_uri)

    def create_tables(self, conn):
        """Create necessary database tables using psycopg3"""
        try:
                with conn.cursor() as cur:
                    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'documents') THEN
                CREATE TABLE documents (
                    id BIGINT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                    content TEXT NOT NULL,
                    index TEXT NOT NULL,
                    embedding VECTOR(768) NOT NULL
                );
                CREATE INDEX document_embedding_idx ON documents
                USING disk_ann (embedding);
            END IF;
        END $$;
        """)
                conn.commit()
        except Exception as e:
            logging.error(f"Error creating tables: {e}")
            raise

    def create_tables_ii(self, conn):
        """Create tables using psycopg3"""
        try:
                with conn.cursor() as cur:
                    cur.execute("""
                    CREATE EXTENSION IF NOT EXISTS vector_scale CASCADE;
                    
                    CREATE TABLE IF NOT EXISTS document (
                        chunk_id SERIAL PRIMARY KEY,
                        content TEXT,
                        index TEXT
                    );

                    CREATE TABLE IF NOT EXISTS small_chunks (
                        small_chunk_id SERIAL PRIMARY KEY,
                        large_chunk_id INTEGER REFERENCES document(chunk_id),
                        embedding vector(786)
                    );

                    CREATE INDEX IF NOT EXISTS document_embedding_idx 
                    ON small_chunks USING diskann (embedding);
                    """)
                conn.commit()
        except Exception as e:
            logging.error(f"Error creating tables: {e}")
            raise

    def insert_data(self, conn, data_dict):
        """Insert data using psycopg3"""
        try:
                with conn.cursor() as cur:
                    for index, chunks in data_dict.items():
                        embeddings = self.model.encode(chunks)
                        
                        for chunk, embedding in zip(chunks, embeddings):
                            
                            # Insert into document table
                            cur.execute("""INSERT INTO documents (content, index, embedding) 
                                        VALUES (%s, %s, %s)
                                        """, (chunk, index, embedding.tolist()))
                conn.commit()
        except Exception as e:
            logging.error(f"Error inserting data: {e}")
            raise

    def insert_data_ii(self, conn, chunked_dict):
        """Insert data using psycopg3"""
        try:
            with conn.cursor() as cur:
                for index, (large_chunks, small_chunks_list) in chunked_dict.items():
                    # Process each large chunk and its small chunks
                    for large_chunk, small_chunks in zip(large_chunks, small_chunks_list):
                        # Insert main document chunk
                        cur.execute("""
                        INSERT INTO document (content, index)
                        VALUES (%s, %s)
                        RETURNING chunk_id
                        """, (large_chunk, index))
                        
                        parent_chunk_id = cur.fetchone()[0]
                        
                        # Create embeddings for small chunks
                        small_embeddings = self.model.encode(small_chunks)
                        
                        # Insert small chunks with their embeddings
                        for small_chunk, embedding in zip(small_chunks, small_embeddings):
                            cur.execute("""
                            INSERT INTO small_chunks (large_chunk_id, embedding)
                            VALUES (%s, %s)
                            """, (parent_chunk_id, embedding.tolist()))
                            
            conn.commit()
        except Exception as e:
            logging.error(f"Error inserting data: {e}")
            raise
        
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                CREATE OR REPLACE VIEW joined_view AS
                SELECT 
                    sc.small_chunk_id,
                    sc.large_chunk_id,
                    lc.content as context,
                    lc.index as document_index,
                    sc.embedding
                FROM 
                    small_chunks sc
                JOIN document lc ON sc.large_chunk_id = lc.chunk_id;
                """)
                conn.commit()
        except Exception as e:
            logging.error(f"Error creating view: {e}")
            raise

    def process_data(self):
        
        logging.basicConfig(level=logging.INFO)
        
        question_dict, dbs_chunking, db_hybrid = {}, [], None

        
        logging.info("Starting data processing...")

        subtitles_dict = self.extract_subtitles_and_text()
        logging.info("Extracted subtitles and text.")

        response = input("Do you want to generate the chunked dictionary for the questions? (yes/no): ").strip().lower()
        if response == 'yes':
            question_dict = self.generate_question_dictionary(subtitles_dict, chunk_size=350)
            logging.info("Generated question dictionary.")
            
        
        response = input("Do you want to generate the chunked dictionary? (yes/no): ").strip().lower()
        if response == 'yes':
            dict_list = self.generate_chunked_dictionaries(subtitles_dict)
            logging.info("Generated chunked dictionaries.")


        response = input("Do you want to generate the hybrid chunked dictionary? (yes/no): ").strip().lower()
        if response == 'yes':
            hybrid_dict = self.generate_chunked_dictionary_ii(subtitles_dict)
            logging.info("Generated hybrid chunked dictionary.")
        
        
        db1 = self.get_connection_to_sql_database(host="localhost", data_base_name="DBTestChunking1", username="postgres", password="578366")
        db2 = self.get_connection_to_sql_database(host="localhost", data_base_name="DBTestChunking2", username="postgres", password="578366")
        db3 = self.get_connection_to_sql_database(host="localhost", data_base_name="DBTestChunking3", username="postgres", password="578366")
        db_hybrid = self.get_connection_to_sql_database(host="localhost", data_base_name="DBTestHybrid", username="postgres", password="578366")
        logging.info("Connected to SQL databases.")

        dbs_chunking = [db1, db2, db3]
        response = input("Do you want to add the data to the overlap dbs? (yes/no): ").strip().lower()
        if response == 'yes':
            for db, data_dict in zip(dbs_chunking, dict_list):
                self.insert_data(db, data_dict)
                logging.info(f"Inserted data into database: {db}")
        
        response = input("Do you want to add the data to the hybrid db? (yes/no): ").strip().lower()
        if response == 'yes':
            self.insert_data_ii(db_hybrid, hybrid_dict)
            logging.info("Inserted hybrid data into database.")

        logging.info("Data processing completed.")
        
        return question_dict, dbs_chunking, db_hybrid