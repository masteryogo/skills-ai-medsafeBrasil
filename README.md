# Skills de IA — MedSafe Brasil

Sete skills autorais para o [Claude Code](https://claude.com/claude-code), com
foco em pesquisa científica, machine learning, visão computacional, NLP clínico
em português e segurança de aplicações.

## O que é uma skill

Uma skill é um conjunto de instruções que o Claude carrega sozinho quando o
assunto aparece na conversa. Você não precisa invocá-la: basta descrever o
problema. Ela entra, aplica o método e sai.

## Instalação

Copie as pastas desejadas para um dos dois lugares:

```bash
# Para uso pessoal, em todos os seus projetos:
cp -r academic-paper ~/.claude/skills/

# Ou, para compartilhar com o time dentro de um repositório:
cp -r academic-paper /caminho/do/projeto/.claude/skills/
```

Reinicie a sessão do Claude Code. As skills são descobertas na inicialização.

> **Importante:** o nome da pasta precisa ser idêntico ao campo `name:` do
> `SKILL.md`. Renomear a pasta impede o carregamento.

Em Linux e macOS, dê permissão de execução aos scripts:

```bash
chmod +x scientific-research-assistant/scripts/*.py
```

## As skills

| Skill | Para quê | Idioma |
|---|---|---|
| `scientific-research-assistant` | Busca de literatura, apreciação crítica de artigos, identificação da lacuna, desenho de estudo e proposta de pesquisa | EN/PT |
| `academic-paper` | Redação e revisão de manuscritos para CS/ML (NeurIPS, ICML, CVPR, ICLR, MICCAI, ACL), resposta a revisores e submissão | EN/PT |
| `machine-learning-engineer` | ML aplicado: splits sem vazamento, baseline antes de rede neural, métricas honestas e deploy com monitoramento | PT |
| `computer-vision-engineer` | Pipeline de visão do sensor à inferência: câmera, codec, ROI, filtragem temporal, avaliação em vídeo. Cobre rPPG | PT |
| `medical-nlp-ptbr` | Texto clínico em português: extração de prontuário, negação, abreviações, doses, CID-10, de-identificação | PT |
| `llm-app-engineer` | Aplicações LLM em produção: eval sets, RAG medido, streaming, custo, defesa contra prompt injection | EN |
| `security-engineer` | AppSec e segurança de sistemas de IA/ML: modelagem de ameaça, revisão de código, LGPD | PT |

### Pesquisa e escrita formam um par

`scientific-research-assistant` e `academic-paper` cobrem fases diferentes e se
passam a bola explicitamente:

```
buscar → avaliar → achar a lacuna → desenhar o estudo
                                            ↓
                        escrever → revisar → rebater → submeter
```

A primeira termina onde a escrita começa. A segunda devolve o controle quando a
escrita revela um buraco de pesquisa — gap sem citação, revisor alegando falta
de originalidade, número que o estudo nunca foi desenhado para produzir.

## Duas regras que atravessam todas elas

1. **Nenhuma citação, número ou referência inventada.** Faltou dado, fica
   marcado como lacuna explícita. Referência fabricada é pior que campo vazio.
2. **A afirmação não pode ser mais larga que a evidência.** Ganho de 0,3 ponto
   em um dataset não é "supera significativamente".

## Licença

MIT — veja [LICENSE](LICENSE). Use, modifique e redistribua à vontade.
