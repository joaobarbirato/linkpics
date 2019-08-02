
## Requires
- [Python 3.6.8](https://docs.python.org/3.6/)
- [Virtual Python Environment builder](https://pypi.org/project/virtualenv/)
- [NLTK Data](https://www.nltk.org/data.html)
- [CBLAS Framework](https://www.netlib.org/blas/#_cblas)

## Setup
### 1. clone
```bash
$ git clone https://github.com/joaobarbirato/linkpics
$ cd linkpics
```

### 2. Build a Python 3.6 virtual environment
```bash
virtualenv venv/ -p python3.6
source venv/bin/activate
```

### 3. Install requirements

- Make sure you have [CMake](https://cmake.org/) properly installed. 

```bash
pip3.6 install -r requirements.txt
```

### 4. Install TreeTagger
- Instructions can be found at the TreeTagger
[documentation](https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/)
- Extract it to `app/src/PLN/TreeTagger`