import sqlite3
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


class SearchEngine:
	def __init__(self, db_path='database/net_surfer.db'):
		self.sqlite3_conn = sqlite3.connect(db_path)
		self.stop_words = set(stopwords.words('english'))

	def search_word(self, word):
		cursor = self.sqlite3_conn.cursor()

		# SQL query to get the 5 most frequent page_urls for the given word
		query = """
            SELECT page_url, SUM(frequency) as total_frequency
            FROM word_frequencies
            WHERE word = ?
            GROUP BY page_url
            ORDER BY total_frequency DESC
            LIMIT 5;
            """

		# Execute the query with the word as a parameter
		cursor.execute(query, (word,))
		return cursor.fetchall()

	def tokenize_search_text(self, text):
		words = [word.lower() for word in word_tokenize(text) if word.isalnum() and word.lower() not in self.stop_words]
		return words

	def search(self, search_text):
		words = self.tokenize_search_text(search_text)

		if not words:
			return []

		results = {}

		for word in words:
			word_results = self.search_word(word)
			for url, frequency in word_results:
				if url in results:
					results[url] += frequency
				else:
					results[url] = frequency

		sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

		return sorted_results[:5]  # Return top 5 results