from sentence_transformers import SentenceTransformer
import time






class VectorToolKit:
    def __init__(self, model_name="efederici/sentence-BERTino"):
        self.model = SentenceTransformer(model_name)
    
    def double_precision_recall(self, conn, query_text, top_k=3):
        query_embedding = self.model.encode(query_text)
        start_time = time.time()
        
        query = """
           SELECT 
                context,
                document_index,
                1 - (embedding <=> %s::vector) as similarity
            FROM joined_view
            ORDER BY similarity DESC
            LIMIT %s;
            """
        
        with conn.cursor() as cur:
            cur.execute(query, (query_embedding.tolist(), top_k))
            results = cur.fetchall()
        elapsed_time = time.time() - start_time
        results_with_percentage = results
        return results_with_percentage, elapsed_time

    def query_similar_entities_with_similarity(self, conn, query_text, top_k=3):
        query_embedding = self.model.encode(query_text)
        start_time = time.time()
        
        query = "SELECT content, index, 1 - (embedding <=> %s::vector) AS similarity FROM documents ORDER BY similarity DESC LIMIT %s;"
        
        with conn.cursor() as cur:
            cur.execute(query, (query_embedding.tolist(), top_k))
            results = cur.fetchall()
        elapsed_time = time.time() - start_time
        results_triplets = [(row[0], row[1], row[2]*100) for row in results]
        return results_triplets, elapsed_time
    def query_selector(self, i, db, query_text, top_k):
        if i == 1:
            return self.double_precision_recall(db, query_text, top_k)
        elif i == 2:
            return self.query_similar_entities_with_similarity(db, query_text, top_k)
        else:
            return "Invalid query selector"