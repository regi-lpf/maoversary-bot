# Maoversary — Bot para o X (Twitter)

Bot em Python que publica diariamente no X a citação do *Livro Vermelho* correspondente à data do dia, acompanhada de um card em PNG no estilo de panfleto/cartilha.

## Estrutura

- `bot.py`: sorteia uma citação da lista da data atual (fuso `America/Sao_Paulo`), gera o card PNG e publica no X via API v2 (`tweepy`).
- `data/calendar_quotes.json`: base completa das 427 citações mapeadas por `MM-DD`.
- `.github/workflows/daily_post.yml`: agendamento diário gratuito no GitHub Actions (09:00 de Brasília / 12:00 UTC).
