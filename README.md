# Python Web Crawler

This is a simple Python web crawler that uses the `requests` library to fetch web pages and `sqlite3` to store the crawled data.

## Features

- Fetch web pages using `requests`
- Store crawled data in an SQLite database
- Handle basic error scenarios

## Requirements

- Python 3.x
- `requests` library
- `sqlite3` (part of the Python Standard Library)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/fou3fou3/net-surfer
    cd net-surfer
    ```

2. Install the required libraries:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Initialize the SQLite database:
    ```bash
    touch database/net_surfer.db
    ```

2. Start the crawler:
    ```bash
    python crawler.py
    ```

## File Structure
python-web-crawler/
├── crawler.py # Main crawler script
├── init_db.py # Script to initialize the SQLite database
├── README.md # This README file
└── requirements.txt # Requirements file for pip


## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MPLV2 License. See the [LICENSE](LICENSE) file for details.



