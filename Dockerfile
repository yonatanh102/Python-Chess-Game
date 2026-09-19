
FROM python:3.13-slim

# (Cython) and (Tkinter)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    tk \
    tcl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir cython setuptools pytest

RUN python setup.py build_ext --inplace

CMD ["python", "Gui.py"]