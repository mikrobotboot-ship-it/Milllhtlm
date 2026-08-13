# MikroBot JARVIS PRO V2
IA, pesquisa web, revisão/correção RouterOS, teste de internet, perfis de câmeras, WhatsApp Cloud API, telemetria e auto-governança leve.

## Codespaces
./INSTALL.sh

## IA
Use OPENAI_API_KEY via secret/environment. O modelo padrão é gpt-5.6-luna e usa Responses API; web search é habilitado em pesquisa e revisão RouterOS.

## Segurança
Scripts são analisados e corrigidos em modo de revisão. O robô não executa alterações de rede automaticamente. Faça backup e use Safe Mode/dry-run quando suportado.

## WhatsApp
Use somente a API oficial e um webhook HTTPS público. Tokens ficam em variáveis de ambiente/Secrets.
