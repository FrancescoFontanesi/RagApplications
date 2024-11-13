import matplotlib.pyplot as plt
import pandas as pd 
import VectorToolKit as vs
import json
import numpy as np
from IPython.display import display


class QueryTester:
    
    def __init__(self):
        self.vs = vs.VectorToolKit()

    def test_queries(self,n, queries, db, id, top_k=3):
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
        
        with open(f"{id}.json", 'w') as json_file:
                json.dump(results, json_file, indent=4)
        return results
        
            
    def calculate_statistics(self, results, id):
    
        rows = []

        # Parse the JSON
        for index, questions_data in results.items():
            questions = questions_data[0]  # List of questions

            index_added = False

            for question_data in questions:
                question_text = question_data[0]  # Question text
                results, elapsed_time = question_data[1]  # Retrieved results and elapsed time

                for i, (content_text, content_index, similarity) in enumerate(results):
                    rows.append({
                            "Index": index if not index_added else "",  # Only show index once per group
                            "Question": question_text if i == 0 else "",  # Only show question text once per retrieval
                            "Elapsed Time": elapsed_time if i == 0 else "",  # Only show elapsed time once per question
                            "Content": content_text,
                            "Content Index": content_index,
                            "Cosine Similarity": str(similarity) + "%"
                        })
            index_added = True

        # Create a DataFrame from the rows
        df = pd.DataFrame(rows)
        
        df.set_index(['Index','Question'], inplace=True)
                
        df.to_excel(f"questions_retrieved_{id}.xlsx", index=True)
        
        display(df)
        

    # Export to Excel
    def generate_stats(self, results, id):
        # Initialize a list to store each index’s statistics
        index_stats = []

        # Iterate over each index in the data
        for index, questions_data in results.items():
            questions = questions_data[0]  # List of questions
            total_questions = questions_data[1]  # Total number of questions

            # Initialize counters for first-result and top-3 occurrences
            first_result_count = 0
            top_3_result_count = 0

            # Analyze each question's results
            for question_data in questions:
                results = question_data[1][0]  # Retrieved results for this question

                # Check if the index is in the first result
                if results[0][1] == index:
                    first_result_count += 1

                # Check if the index is within the top 3 results
                top_3_result_count += int(any(result[1] == index for result in results[:3]))
            # Calculate precision for first result and top 3 results
            precision_first_result = first_result_count / total_questions if total_questions > 0 else 0
            precision_top_3_result = top_3_result_count / total_questions if total_questions > 0 else 0

            # Store statistics for this index
            index_stats.append({
                "Index": index,
                "Total Questions": total_questions,
                "First Result Count": first_result_count,
                "Top 3 Result Count": top_3_result_count,
                "Precision (First Result)": str(np.round(precision_first_result,2) * 100)+ "%",
                "Precision (Top 3 Results)": str(np.round(precision_top_3_result,2) * 100) + "%"
            })

        # Convert index statistics to a DataFrame
        df_stats = pd.DataFrame(index_stats)
        
        df_stats.set_index('Index', inplace=True)
        
        
        # Calculate totals
        total_row = {
            'Total Questions': df_stats['Total Questions'].sum(),
            'First Result Count': df_stats['First Result Count'].sum(),
            'Top 3 Result Count': df_stats['Top 3 Result Count'].sum(),
            'Precision (First Result)': f"{(df_stats['First Result Count'].sum() / df_stats['Total Questions'].sum() * 100):.2f}%",
            'Precision (Top 3 Results)': f"{(df_stats['Top 3 Result Count'].sum() / df_stats['Total Questions'].sum() * 100):.2f}%"
        }

        # Add totals row
        df_stats.loc['TOTAL'] = total_row

        # Export to Excel
        df_stats.to_excel(f"question_retrived_statistics_{id}.xlsx", index=True)

        display(df_stats)

    def generate_stats_dataframe(self, results, id):
        
        
        self.calculate_statistics(results, id)
        
        
        print("\n----------------------------------------------\n")
        
        
        self.generate_stats(results, id)



