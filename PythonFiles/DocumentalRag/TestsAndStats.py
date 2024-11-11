import matplotlib.pyplot as plt
import pandas as pd 
import VectorToolKit as vs

class QueryTester:
    
    def __init__(self):
        self.vs = vs.VectorToolKit()

    def test_queries(self,n, queries, db, top_k=3):
        """
        Test the queries and retrieve information.

        Args:
        - queries: Dictionary with index as key and list of questions as value.
        - top_k: Number of top results to retrieve.

        Returns:
        - Dictionary with index as key and list of tuples containing question and result.
        """
        results = {}
        for index, questions in queries.items():
            query_results = []
            for question in questions:
                result = self.vs.query_selector(n, db, question, top_k)
                query_results.append((question, result))
            results[index] = (query_results, len(query_results))
        return results

    def calculate_statistics(self, query_results):
        """
        Calculate aggregated statistics by manual index.
        
        Args:
            query_results_dict: Dictionary {index: (query_results, count)}
        
        Returns:
            Tuple of (detailed_df, summary_df)
        """
        # Initialize data structure
        data = {
            'Index': [],
            'Query Content': [],
            'Result Content': [],
            'Similarity': [],
            'Response Time': [],
            'Result Position': []
        }
        
        # Collect data per index
        for index, (results, _) in query_results.items():
            query_matches, elapsed_time = results
            
            for (content, result_index, similarity) in query_matches.items():
                data['Index'].append(index)
                data['Query Content'].append(content)
                data['Result Content'].append(result_index)
                data['Similarity'].append(similarity)
                data['Response Time'].append(elapsed_time)

        # Create detailed DataFrame
        detailed_df = pd.DataFrame(data)
        detailed_df = detailed_df.set_index(['Index','Query Content'])
        detailed_df.to_csv("queries_results.csv", index=True)

        detailed_df

    def generate_stats(self, results):
        stats_dict = {}
        for index, (results, n) in results.items():
            query_matches, _ = results
            i=0
            for (_, result_index, _) in query_matches.items():
                if result_index == index:
                    i+=1
            stats_dict[index] = (n,i)
        return stats_dict

    def generate_stats_dataframe(self, results):
        
        
        self.calculate_statistics(results)
        
        
        print("\n----------------------------------------------\n")
        
        
        stats_dict = self.generate_stats(results)
        stats_df = pd.DataFrame(stats_dict)
        stats_df = stats_df.T
        stats_df.columns = ['Total Questions', 'Correct Answers']
        stats_df = stats_df.set_index(['Index','Total Questions'])
        stats_df['Accuracy'] = stats_df['Correct Answers'] / stats_df['Total Questions'] * 100
        
        stats_df.to_csv("query_statistics.csv", index=True)
        
        

        stats_df



