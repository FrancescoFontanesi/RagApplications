import DataProcessing as dp 
import TestsAndStats as stats
import LLMToolKit as llm
import logging
import json


    

def main():
    
    QuestionGenerator = llm.QuestionGenerator()
    StatsTool = stats.QueryTester()
    DocumentProcessor = dp.DocumentProcessor()

    dictionary_for_questions, db_list, dbHybrid = {}, [], None
    response = input("Initialize the data? (yes/no): ").strip().lower()
    if response == 'yes':
        dictionary_for_questions, db_list, dbHybrid = DocumentProcessor.process_data()


    response = input("Start test evaluations and stats generation(yes/no): ").strip().lower()
    if response == 'yes':
        questions_dict = {}
        try:
            with open("question.json", "r") as f:
                questions_dict = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            questions_dict = QuestionGenerator.generate_questions_from_chunks(dictionary_for_questions)
            with open("question.json", "w") as f:
                json.dump(questions_dict, f)
        
        logging.info("Loaded question dictionary.")
        

        #TestQueries
        resultsOverlap=[]
        for db in db_list:
            resultsOverlap.append(StatsTool.test_queries(2,questions_dict, db))
        
        
        resultsHybrid = StatsTool.test_queries(1,questions_dict, dbHybrid)
        
        # Calculate statistics
        for idx, result in enumerate(resultsOverlap, 1):
            print(f"Statistics for DB {idx} with overlap {idx*10}%\n\n")
            StatsTool.calculate_statistics(result)
        
        print(f"Statistics for Hybrid DB\n\n")
        StatsTool.calculate_statistics(resultsHybrid)
        


if __name__ == "__main__":
    
    main()