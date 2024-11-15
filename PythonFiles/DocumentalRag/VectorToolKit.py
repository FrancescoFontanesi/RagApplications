from sentence_transformers import SentenceTransformer
import time






class VectorToolKit:
    """
    A toolkit for performing vector similarity searches in PostgreSQL using pgvector.
    
    This class provides methods to encode text into vectors and perform similarity searches
    using different schemas (hybrid and overlap) in a PostgreSQL database with pgvector extension.

    Attributes:
        model (SentenceTransformer): The sentence transformer model used for text encoding
    """

    def __init__(self, model_name="efederici/sentence-BERTino"):
        self.model = SentenceTransformer(model_name)
    
    def double_precision_recall(self, conn, query_text, top_k=5):
        
        """
        Perform similarity search using hybrid schema with double precision chunks.

        Args:
            conn: Psycopg connection object
            query_text (str): Text to search for
            top_k (int): Number of results to return, defaults to 5

        Returns:
            List[Tuple[str, str, float]]: List of tuples containing:
                - context: The matched text
                - document_index: Index of the context
                - similarity: Cosine similarity score (0-1)
        """
        
        query_embedding = self.model.encode(query_text)        
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
        results_with_percentage = results
        return results_with_percentage

    def query_similar_entities_with_similarity(self, conn, query_text, top_k=5):
        
        """
        Perform similarity search using overlap schema.

        Args:
            conn: Psycopg connection object
            query_text (str): Text to search for
            top_k (int): Number of results to return, defaults to 5

        Returns:
            List[Tuple[str, str, float]]: List of tuples containing:
                - content: The matched text
                - index: Index of the context
                - similarity: Cosine similarity score (0-1)
        """
        
        query_embedding = self.model.encode(query_text)
        
        query = "SELECT content, index, 1 - (embedding <=> %s::vector) AS similarity FROM documents ORDER BY similarity DESC LIMIT %s;"
        
        with conn.cursor() as cur:
            cur.execute(query, (query_embedding.tolist(), top_k))
            results = cur.fetchall()
        results_triplets = [(row[0], row[1], row[2]) for row in results]
        return results_triplets 
    
    def query_selector(self, i, db, query_text, top_k):
        """
            Select and execute the appropriate query method based on schema type.

            This method acts as a router between different vector similarity search implementations:
            - i=1: Uses hybrid schema (double precision) with joined view
            - i=2: Uses overlap schema with direct document table query

            Args:
                i (int): Schema type selector
                    1 = Hybrid schema (uses double_precision_recall)
                    2 = Overlap schema (uses query_similar_entities_with_similarity)
                db: PostgreSQL connection object
                query_text (str): Text to search for similar documents
                top_k (int): Number of results to return

            Returns:
                Union[List[Tuple[str, str, float]], str]: Either:
                    - List of tuples containing (text, index, similarity) for valid schema types
                    - Error message string for invalid schema type
        """
        if i == 1:
            return self.double_precision_recall(db, query_text, top_k)
        elif i == 2:
            return self.query_similar_entities_with_similarity(db, query_text, top_k)
        else:
            return "Invalid query selector"