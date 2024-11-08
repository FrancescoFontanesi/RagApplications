import fitz  # PyMuPDF
import re

import numpy as np
import pandas as pd

import textwrap
from langchain.text_splitter import TokenTextSplitter

from langchain import SQLDatabase

import pandas as pd
import matplotlib.pyplot as plt
import time



model = SentenceTransformer("efederici/sentence-BERTino")



def extract_subtitles_and_text(pdf_path, start_page=0):
    """
    Estrae i sottotitoli e il testo corrispondente da un file PDF a partire da una pagina specifica.

    Parametri:
    pdf_path (str): Il percorso del file PDF da analizzare.
    start_page (int): Il numero della pagina da cui iniziare l'estrazione (0 per la prima pagina).

    Ritorna:
    dict: Un dizionario dove le chiavi sono gli indici dei sottotitoli (es. 1.1, 2.3) e i valori sono tuple con il nome del sottocapitolo e il testo corrispondente.
    """
    # Apri il file PDF
    document = fitz.open(pdf_path)
    
    # Inizializza un dizionario vuoto per memorizzare i sottotitoli e il testo corrispondente
    subtitles_dict = {}
    
    # Definisci il pattern per trovare i sottotitoli (es. 1.1, 2.3, ecc.)
    pattern = re.compile(r'\d+\.\d+')
    
    current_subtitle = None
    current_subtitle_name = None
    current_text = ""
    
    # Itera attraverso ogni pagina del PDF a partire da start_page
    for page_num in range(start_page, len(document)):
        page = document.load_page(page_num)
        text = page.get_text("text")
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if pattern.match(line.strip()):
                if current_subtitle:
                    subtitles_dict[current_subtitle] = (current_subtitle_name.replace(".",""), re.sub(r'\d+', '', current_text).strip())
                current_subtitle = line.strip().split()[0]  # Solo l'indice del sottotitolo
                # Controlla se il nome del sottotitolo è sulla stessa riga o sulla riga successiva
                if len(line.strip().split()) > 1:
                    current_subtitle_name = ' '.join(line.strip().split()[1:])
                else:
                    current_subtitle_name = lines[i + 1].strip() if i + 1 < len(lines) else ""
                current_text = ""
            elif line.strip() != current_subtitle_name:
                current_text += " " + line.strip()
        
        if current_subtitle:
            subtitles_dict[current_subtitle] = (current_subtitle_name.replace(".",""), re.sub(r'\d+', '', current_text).strip())
    
    return subtitles_dict


def chunk(text, chunk_size=768, chunk_overlap=0):
    """
    Divide un testo in chunk di dimensione fissa con un certo overlap.

    Args:
    - text (str): Il testo da dividere in chunk.
    - chunk_size (int): La dimensione di ciascun chunk.
    - chunk_overlap (int): L'overlap tra i chunk.

    Returns:
    - List[str]: Una lista di chunk di dimensione fissa.
    """
    semantic_splitter = TokenTextSplitter(
    chunk_size=chunk_size,    # Number of characters per chunk
    chunk_overlap=chunk_overlap   # Overlap to preserve context
    )

# Split the text into semantic chunks
    chunks = semantic_splitter.split_text(text)
    
    return chunks



def generateChunkedDictionaries(dict,chunksize=768, overlapPercentage=[0.1, 0.2, 0.3]):
    chunked_subtitles_dict = dict.copy()
    dictList = []
    for overlap_percentage in overlapPercentage:
        overlap = int(chunksize * overlap_percentage)
        dictList.append(chunked_subtitles_dict.copy())
        for subtitle, text in chunked_subtitles_dict.items():
            if len(text[1]) <= chunksize:
                chunked_subtitles_dict[subtitle] = [text[1]]
            else:
                chunked_subtitles_dict[subtitle] = chunk(text[1], chunk_size=chunksize, chunk_overlap=overlap)
    return dictList

def generateChunkedDictionatyII(dict):
    
    chunked_subtitles_dict = subtitles_dict.copy()

    for subtitle, text in dict.items():
        document = chunk(text[1])
        chunked_subtitles_dict[subtitle] = [(large_chunk, chunk(large_chunk,128,28)) for large_chunk in document]

    

# Esempio di utilizzo
pdf_path = r"D:\Tirocinio\Documenti\ManualeTETRAS_modificato2.pdf"
subtitles_dict = extract_subtitles_and_text(pdf_path)

# Stampa i sottotitoli estratti e il testo corrispondente
for subtitle, text in subtitles_dict.items():
    print(f"Index:{subtitle}.\nName:{text[0]}\nContains {len(text[1])} charater:\n\n{textwrap.fill(text[1], width=50)}\n\n")


dictList = generateChunkedDictionaries(subtitles_dict)
hybridDict = generateChunkedDictionatyII(subtitles_dict)










from langchain import SQLDatabase
from sentence_transformers import SentenceTransformer

def get_connection_to_SQLDatabase(host="localhost", data_base_name="database", username="postgres", password="postgres", port="5432"):
    g_uri = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{data_base_name}"
    return SQLDatabase.from_uri(g_uri)

def create_tables(db):
    db.run("CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;")
    db.run("""
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
            USING diskann (embedding);
        END IF;
    END $$;
    """)
    
def create_tablesII(db):
    db.run("""
    CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;
    CREATE TABLE document (
    chunk_id INT PRIMARY KEY,
    content TEXT,
    index TEXT
    );

    CREATE TABLE small_chunks (
    small_chunk_id SERIAL PRIMARY KEY,
    large_chunk_id INTEGER REFERENCES document(chunk_id),
    embedding vector(128)  -- pgvector type
    );
        
    CREATE INDEX document_embedding_idx ON small_chunks
    USING diskann (embedding);
        
    """)

def insert_data(db, model, data_dict):
    for subtitle, chunks in data_dict.items():
        embeddings = model.encode(chunks)
        for chunk, embedding in zip(chunks, embeddings):
            db.run("INSERT INTO documents (content, index, embedding) VALUES (%s, %s, %s);", (chunk, subtitle, embedding.tolist()))


model = SentenceTransformer("efederici/sentence-BERTino")

def insert_dataII(db, chunked_subtitles_dict, model):
    """
    Insert the data into the SQL tables.

    Args:
    - db: The database connection.
    - chunked_subtitles_dict: Dictionary containing the chunked subtitles.
    - model: The SentenceTransformer model for generating embeddings.
    """
    for subtitle, chunks in chunked_subtitles_dict.items():
        for large_chunk, small_chunks in chunks:
            # Insert large chunk into document table
            large_chunk_id = db.run("INSERT INTO document (content, index) VALUES (%s, %s) RETURNING chunk_id;", (large_chunk, subtitle))[0][0]
            
            for small_chunk in small_chunks:
                # Generate embedding for the small chunk
                embedding = model.encode(small_chunk)
                
                # Insert small chunk into small_chunks table
                db.run("INSERT INTO small_chunks (large_chunk_id, embedding) VALUES (%s, %s);",
                (large_chunk_id, embedding.tolist()))




def doublePrecisionRecall(db,query_text,top_k=1):
    
    # Genera l'embedding della query
    query_embedding = model.encode(query_text)


    #Esegui una ricerca vettoriale sui dati
    start_time = time.time()
    results = db.run("""
    WITH ranked_matches AS (
        SELECT 
            sc.small_chunk_id,
            sc.large_chunk_id,
            lc.content as context,
            lc.index as document_index,
            1 - (sc.embedding <=> %s) as similarity
        FROM 
            small_chunks sc
            JOIN document lc ON sc.large_chunk_id = lc.chunk_id
        ORDER BY 
            similarity ASC
        LIMIT %s
    )
    SELECT 
        context,        -- Full content of the large chunk
        document_index, -- Index reference
        distance        -- Distance score
    FROM ranked_matches
    """
    ),(query_embedding.tolist(), query_embedding.tolist(), top_k)
    elapsed_time = time.time() - start_time
    
    results_with_percentage = [(content, similarity * 100) for content, similarity in results]

    return results_with_percentage,elapsed_time



def query_similar_entities_with_similarity(db,query_text, top_k=1):
    # Genera l'embedding della query
    query_embedding = model.encode(query_text)
    
    start_time = time.time()
    # Esegui una ricerca vettoriale sui dati
    results = db.run("""
        SELECT content, 1 - (embedding <=> %s) AS similarity, index
        FROM documents
        ORDER BY embedding <=> %s
        LIMIT %s;
    """, (query_embedding.tolist(), query_embedding.tolist(), top_k))
    elapsed_time = time.time() - start_time

    
    # Convert similarity to percentage
    results_with_percentage = [(content, similarity * 100) for content, similarity in results]
    
    return results_with_percentage,elapsed_time

# Initialize databases
db1 = get_connection_to_SQLDatabase(host="localhost", data_base_name="DBTestChunking1", username="postgres", password="578366")
db2 = get_connection_to_SQLDatabase(host="localhost", data_base_name="DBTestChunking2", username="postgres", password="578366")
db3 = get_connection_to_SQLDatabase(host="localhost", data_base_name="DBTestChunking3", username="postgres", password="578366")
db4 = get_connection_to_SQLDatabase(host="localhost", data_base_name="DBTestQueries", username="postgres", password="578366")
dbHybrid = get_connection_to_SQLDatabase(host="localhost",data_base_name="DBTestHybrid",username="postgres",password="578366")


dbsChunking = [db1, db2, db3]

# Create tables in each database
for db in dbsChunking:
    create_tables(db)

create_tablesII(dbHybrid)

# Load model

# Insert data into each database
for db, data_dict in zip(dbsChunking, dictList):
    insert_data(db, model, data_dict)

insert_dataII(dbHybrid, hybridDict, model)