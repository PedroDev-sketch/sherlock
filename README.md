# Sherlock

Hunt down social media accounts by username across social networks.

## Rodando o web local

```bash
cd web
python manage.py runserver
# Acesse http://localhost:8000
```

> **Pré-requisito:** instale as dependências uma vez:
> ```bash
> pip install -e .          # instala sherlock_project (CLI)
> cd web && pip install -r requirements.txt
> ```

## Rodando os testes do web

```bash
cd web
pytest
```

Com relatório de cobertura:

```bash
cd web
pytest --cov=apps --cov-report=term-missing
```
