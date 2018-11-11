# Cali

Cali is a fast & simple blog tool powered by Python 3.

## Features

- Python 3
- Blazing fast generating
- Jekyll Themes are suppored(\*)

## Installation

``` bash
$ pip install -r requirements.txt
```

## Quick Start

**Setup your blog**

``` bash
# Clone a Jekyll Theme and replace all '-' to '_' in _config.yml and templates
$ git clone --depth=1 git@github.com:thisiswangle/thisiswangle.github.io.git -b src blog
$ cd blog
```

**Start the server**

``` bash
$ python -m http.server
```

**Create a new post**

``` bash
$ wget https://gist.githubusercontent.com/thisiswangle/8bfd5f6fa91e6128e693345216555435/raw/84b54fc1cd23463e7445ea137012bd208f4636a4/new.py%25E3%2580%2580 -O new.py
python new.py
```

**Generate static files**

``` bash
$ python cali.py
```

## Live Demo

- [Le's Blog](https://thisiswangle.com)

## License

None

