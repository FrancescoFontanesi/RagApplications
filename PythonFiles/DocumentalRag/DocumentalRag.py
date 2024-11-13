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
            with open("questions.json", "r") as f:
                questions_dict = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            questions_dict = QuestionGenerator.generate_questions_from_chunks(dictionary_for_questions)
            with open("questions.json", "w") as f:
                json.dump(questions_dict, f)
        
        logging.info("Loaded question dictionary.")
        

        #TestQueries
        resultsOverlap = []
        for db in db_list:
            result = {}
            try:
                with open(f"{db_list.index(db) + 1}.json", "r") as f:
                    result = json.load(f)
                logging.info("Loaded results overlap from file.")
            except (FileNotFoundError, json.JSONDecodeError):
                logging.debug(f"Testing queries on DB with overlap {db_list.index(db) * 10}%")
                result = StatsTool.test_queries(2, questions_dict, db, (db_list.index(db)+1) )
            resultsOverlap.append(result)
        
        # Calculate statistics
        for idx, result in enumerate(resultsOverlap, 1):
                logging.debug(f"Calculating statistics for DB {idx} with overlap {idx * 10}%")
                print(f"Statistics for DB {idx} with overlap {idx * 10}%\n\n")
                StatsTool.generate_stats_dataframe(result,f"{idx * 10}%")
        
        logging.debug("Testing queries on Hybrid DB")
        resultsHybrid = StatsTool.test_queries(1, questions_dict, dbHybrid, id="Hybrid")        
        
        logging.debug("Calculating statistics for Hybrid DB")
        print(f"Statistics for Hybrid DB\n\n")
        StatsTool.generate_stats_dataframe(resultsHybrid, id="Hybrid")


if __name__ == "__main__":
    
    main()