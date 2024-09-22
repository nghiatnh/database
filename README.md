# Database Project

## Overview

This project is a simple database designed to store and retrieve data efficiently. It supports basic CRUD (Create, Read, Update, Delete) operations and serves as a learning tool for understanding the fundamentals of database management systems.

## How to Run

Refer to the [example.ipynb](example.ipynb) for instructions on running this project.

Here is an example of the query language:

```python
recs = executor.execute("""
SELECT id AS user_id, name, age, height FROM users;
""")
print(recs)
```
```
# 4 records found
====================================================
‖ user_id    ‖ name       ‖ age        ‖ height    ‖
====================================================
| 1          | Alice      | 25         | 147       |
----------------------------------------------------
| 2          | Bob        | 30         | 157       |
----------------------------------------------------
| 3          | Cindy      | 35         | 167       |
----------------------------------------------------
| 4          | David      | 40         | 177       |
----------------------------------------------------
```

## Features

- Basic CRUD operations.
- Indexing for efficient data retrieval.
- Transaction support.
- Concurrent read-write capability: supports multiple readers and a single writer.
- Simple query language. See the [GRAMMAR](GRAMMAR.md) for more details.

## Limitations and Areas for Improvement

- Some checks may be missing in the project.

- The query language is very simple and lacks essential features, such as verifying if a table exists and supporting the not-equal operator. Improvements are needed in these areas.

## Contributing

Contributions to this project are welcome. If you have ideas for enhancements or new features, feel free to open an issue or submit a pull request.

## Acknowledgments

I would like to thank the following authors:

- James Smith, for his book [Build Your Own Database From Scratch In Go](https://build-your-own.org/database/), which provided the foundational knowledge and inspiration for this project.
- The query language is inspired by my [compiler project](https://github.com/nghiatnh/compiler). I also acknowledge all the contributors to that project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact
For any questions or inquiries, please contact the project maintainer at nghiatnh02@gmail.com.
