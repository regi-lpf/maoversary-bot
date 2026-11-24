# Maoversary — Bot para o X (Twitter)

Bot em Python que publica diariamente no X a citação do *Livro Vermelho* correspondente à data do dia, acompanhada de um card em PNG no estilo de panfleto/cartilha.

## Estrutura

- `bot.py`: sorteia uma citação da lista da data atual (fuso `America/Sao_Paulo`), gera o card PNG e publica no X via API v2 (`tweepy`).
- `data/calendar_quotes.json`: base completa das 427 citações mapeadas por `MM-DD`.
- `.github/workflows/daily_post.yml`: agendamento diário gratuito no GitHub Actions (09:00 de Brasília / 12:00 UTC).

## Teste local (sem publicar)

```bash
pip install -r requirements.txt
python bot.py --dry-run --date 11-24 --out card_teste.png
```

## Como colocar no ar (GitHub Actions)

1. Crie uma conta de aplicativo no [Developer Portal do X](https://developer.x.com/) (o plano gratuito permite publicar posts com mídia).
2. Nas configurações do app no X, ative **User authentication settings** com permissão **Read and Write** e gere:
   - `API Key` e `API Key Secret`
   - `Access Token` e `Access Token Secret`
3. Suba esta pasta para um repositório no GitHub.
4. No repositório, vá em **Settings → Secrets and variables → Actions** e adicione os 4 secrets:
   - `X_API_KEY`
   - `X_API_SECRET`
   - `X_ACCESS_TOKEN`
   - `X_ACCESS_TOKEN_SECRET`
5. Na aba **Actions**, selecione **Maoversary Daily Post** e clique em **Run workflow** para fazer o primeiro teste manual.
