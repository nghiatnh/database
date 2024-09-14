# Database Project

## Overview

This project is a simple database designed to store and retrieve data efficiently. It supports basic CRUD (Create, Read, Update, Delete) operations and is intended as a learning tool for understanding the basics of database management systems.

## How to Run

See the [example.ipynb](example.ipynb) to learn how to run this project.

This is an example of the query language:

```python
recs = executor.execute("""
DELETE FROM users INDEX BY name >= 'David' AND name <= 'David';
SELECT id AS user_id, name, age, height FROM users INDEX BY name >= 'Bob' AND name <= 'Dob' FILTER age <= 40 LIMIT 10;
""")
print(Record.format_records(recs))
```
```
# 1 records found
====================================================
‖ user_id    ‖ name       ‖ age        ‖ height    ‖
====================================================
| 3          | Cindy      | 35         | 167       |
----------------------------------------------------
```

## Features

- Basic CRUD operations
- Indexing for efficient data retrieval
- Transaction support
- Simple query language. See the [GRAMMAR](GRAMMAR.md) for more details.

## Limitations and Areas for Improvement

- The source bookuses Go Lang to code this project, so it implements concurrency. I also need to do that. I found that Python is challenging for parallel processing, so I will revisit this in the future with Go Lang and concurrent read-write capabilities.

- There may be some missing checks in my project.

- The query language is very simple. t lacks important features like checking if a table exists, dropping tables, etc. I need to improve it.

## Contributing

Contributions to this project are welcome. If you have ideas for improvements or new features, feel free to open an issue or submit a pull request.

## Acknowledgments

I would like to thank the following authors:

- James Smith, for his book [Build Your Own Database From Scratch In Go](https://build-your-own.org/database/), which provided the foundational knowledge and inspiration for this project.
- The query language is inspired by my [compiler project](https://github.com/nghiatnh/compiler). I also acknowledge all the contributors to that project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.