from sentence_transformers import SentenceTransformer
import time




class VectorToolKit:
    def __init__(self, model_name="efederici/sentence-BERTino"):
        self.model = SentenceTransformer(model_name)
    
    def double_precision_recall(self, db, query_text, top_k=3):
        query_embedding = self.model.encode(query_text)
        start_time = time.time()
        
        engine = db._engine
        
        with engine.connect() as connection:
            results = connection.execute("""
            WITH ranked_matches AS (
            SELECT 
                sc.small_chunk_id,
                sc.large_chunk_id,
                lc.content as context,
                lc.index as document_index,
                1 - (sc.embedding <=> :query_embedding) as similarity
            FROM 
                small_chunks sc
                JOIN document lc ON sc.large_chunk_id = lc.chunk_id
            ORDER BY 
                similarity ASC
            LIMIT :top_k
            )
            SELECT 
            context,
            document_index,
            similarity
            FROM ranked_matches
            """, {'query_embedding': query_embedding.tolist(), 'top_k': top_k}).fetchall()
        elapsed_time = time.time() - start_time
        results_with_percentage = [(' '.join(context.split()[:15] + "..."), index, similarity * 100) for context, index, similarity in results]
        return results_with_percentage, elapsed_time

    def query_similar_entities_with_similarity(self, db, query_text, top_k=3):
        query_embedding = self.model.encode(query_text)
        start_time = time.time()
        
        engine = db._engine
        
        with engine.connect() as connection:
            results = connection.execute("SELECT content, index, 1 - (embedding <=> :query_embedding) AS similarity FROM documents ORDER BY embedding <=> :query_embedding LIMIT :top_k;", {'query_embedding': query_embedding.tolist(), 'top_k': top_k}).fetchall()
        elapsed_time = time.time() - start_time
        results_with_percentage = [(' '.join(content.split()[:15] + "..."), index, similarity * 100) for content, index, similarity in results]
        return results_with_percentage, elapsed_time
    
    def query_selector(self, i, db, query_text, top_k):
        if i == 1:
            return self.double_precision_recall(db, query_text, top_k)
        elif i == 2:
            return self.query_similar_entities_with_similarity(db, query_text, top_k)
        else:
            return "Invalid query selector"