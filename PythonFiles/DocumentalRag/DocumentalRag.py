import DataProcessing as dp 
import TestsAndStats as stats
import LLMToolKit as llm
import logging
import json
import os


    

def main():
    
    QuestionGenerator = llm.QuestionGenerator()
    StatsTool = stats.QueryTester()
    DocumentProcessor = dp.DocumentProcessor()

    dictionary_for_questions, db_list, dbHybrid = {}, [], []
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
        
        response = input("Start testing queries on Overlap DBs? (yes/no): ").strip().lower()
        if response == 'yes':
            logging.debug("Testing queries on Overlap DBs")
            # TestQueries
            resultsOverlap = []
            for db in db_list:
                result = {}
                try:
                    with open(f"Overlap_{(db_list.index(db) * 5)}%.json", "r") as f:
                        result = json.load(f)
                    logging.info("Loaded results overlap from file.")
                except (FileNotFoundError, json.JSONDecodeError):
                    logging.debug(f"Testing queries on DB -> {(db_list.index(db) * 5)}%")
                    result = StatsTool.test_queries(2, questions_dict, db, f"Overlap_{(db_list.index(db) * 5)}%" )
                resultsOverlap.append(result)
                
                # Calculate statistics
            for idx, result in enumerate(resultsOverlap, 0):
                logging.debug(f"Calculating statistics for DB with overlap {idx * 5}%")
                StatsTool.generate_stats_dataframe(result, f"{idx * 5}%")
        
        
        response = input("Start testing queries on Hybrid DBs? (yes/no): ").strip().lower()
        if response == 'yes':
            logging.debug("Testing queries on Hybrid DBs")
            resultsHybrid = []
            for db in dbHybrid:
                result = {}
                try:
                    with open(f"Hybrid_{((dbHybrid.index(db)+1) * 64)}.json", "r") as f:
                        result = json.load(f)
                    logging.info("Loaded results overlap from file.")
                except (FileNotFoundError, json.JSONDecodeError):
                    logging.debug(f"Testing queries on DB -> {((dbHybrid.index(db)+1) * 64)}")
                    result = StatsTool.test_queries(1, questions_dict, db, f"Hybrid_{((dbHybrid.index(db)+1) * 64)}" )
                resultsHybrid.append(result)
            
            for idx, result in enumerate(resultsHybrid, 1):
                    logging.debug(f"Calculating statistics for Hybrid DB with size {idx * 64}")
                    StatsTool.generate_stats_dataframe(result,f"Hybrid_{idx*64}%")
                
        logging.info("All tests completed.")
        response = input("Wipe the databases? (yes/no): ").strip().lower()
        if response == 'yes':
            DocumentProcessor.wipe_databases(db_list,dbHybrid)
            logging.info("Databases wiped.")
        
        
def main_v2(path : str):
    
    QuestionGenerator = llm.QuestionGenerator()
    StatsTool = stats.QueryTester()
    # Convert the path to a usable format
    response = input("Initialize the document processor with the provided path? (yes/no): ").strip().lower()
    if response == 'yes':
        path = os.path.normpath(path)
        logging.info(f"Normalized path: {path}")

        DocumentProcessor = dp.DocumentProcessor(document_path=path)
        logging.info("Initialized DocumentProcessor with the provided document path.")

        normal, hybrid = DocumentProcessor.chunk_document_plain()
        logging.info("Document chunked into normal and hybrid formats.")


        response = input("Connect and initialized sql databases?").strip().lower()
        if response == 'yes':
            dbn = DocumentProcessor.get_connection_to_sql_database(host="localhost", data_base_name="DBTestDocument", username="postgres", password="578366")
            dbh = DocumentProcessor.get_connection_to_sql_database(host="localhost", data_base_name="DBTestDocumentHybrid", username="postgres", password="578366")
            logging.info("Connected to SQL databases.")

            DocumentProcessor.create_tables(dbn)
            logging.info("Created tables in normal database.")

            DocumentProcessor.create_tables_ii(dbh)
            logging.info("Created tables in hybrid database.")

            DocumentProcessor.insert_data(dbn, normal)
            logging.info("Inserted data into normal database.")

            DocumentProcessor.insert_data_ii(dbh, hybrid)
            logging.info("Inserted data into hybrid database.")
    else:
        logging.info("Document processor initialization skipped.")
    
    

    

if __name__ == "__main__":
    version = input("Select action(Tetras, Document): ").strip()
    if version == 'Tetras':
        main()
    elif version == 'Document':
        path = input("Please enter the path to the document: ").strip()
        main_v2(path)
        
    else:
        print("Invalid selection. Exiting.")