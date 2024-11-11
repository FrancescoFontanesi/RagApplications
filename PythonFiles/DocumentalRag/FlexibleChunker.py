from typing import List
from transformers import AutoTokenizer
from blingfire import text_to_sentences


class FlexibleChunker:
    
    def __init__(self, target_chunk_size: int = 500, model_name: str = "efederici/sentence-BERTino"):
        self.target_chunk_size = target_chunk_size
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def split_into_sentences(self, text: str) -> List[str]:
        
        return text_to_sentences(text).split('\n')

    def chunk_text(self, text: str) -> List[str]:
        sentences = self.split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_token_count = 0
        sentence_token_counts = [self.count_tokens(sentence) for sentence in sentences]
        
        for sentence, sentence_token_count in zip(sentences, sentence_token_counts):
            if current_token_count + sentence_token_count > self.target_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_token_count = sentence_token_count
            else:
                current_chunk.append(sentence)
                current_token_count += sentence_token_count
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks

    def chunk_with_overlap(self, text: str, overlap_size: int = 50) -> List[str]:
        sentences = self.split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_token_count = 0
        sentence_token_counts = [self.count_tokens(sentence) for sentence in sentences]
        
        for sentence, sentence_token_count in zip(sentences, sentence_token_counts):
            if current_token_count + sentence_token_count > self.target_chunk_size and current_chunk:
                overlap_token_count = 0
                overlap_sentences = []
                
                for s, s_token_count in zip(reversed(current_chunk), reversed(sentence_token_counts[:len(current_chunk)])):
                    if overlap_token_count + s_token_count <= overlap_size:
                        overlap_sentences.insert(0, s)
                        overlap_token_count += s_token_count
                    else:
                        break
                
                chunks.append(' '.join(current_chunk))
                current_chunk = overlap_sentences + [sentence]
                current_token_count = sum(self.count_tokens(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_token_count += sentence_token_count
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks
