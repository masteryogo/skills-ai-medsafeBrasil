# Segurança de sistemas de IA/ML

Referência de apoio da skill `security-engineer`. Cobre o que é específico de modelo,
pipeline de treino e aplicação com LLM. Tudo de AppSec clássico continua valendo por baixo.

## 1. O modelo de ameaça de uma aplicação com LLM

Desenhe quatro entradas e trate **todas** como não confiáveis, mesmo as que parecem internas:

| Entrada | Quem controla de fato |
|---|---|
| Mensagem do usuário | O usuário (pode ser adversário) |
| Documento recuperado (RAG) | Quem escreveu o documento — nem sempre é quem o subiu |
| Saída de ferramenta (web, e-mail, banco, MCP) | O sistema externo, ou quem o comprometeu |
| Conteúdo de arquivo enviado (PDF, imagem, planilha, código) | O remetente |

E duas saídas, ambas com poder de dano:

- **texto para o usuário** — desinformação, vazamento de dado de outro usuário, phishing
  renderizado como link ou imagem;
- **chamada de ferramenta** — o caminho real de impacto: escrever, apagar, pagar, enviar,
  publicar, executar.

### Injeção de prompt: direta e indireta

- **Direta**: o usuário tenta sair do escopo. Impacto limitado ao que ele já poderia fazer —
  costuma ser problema de conteúdo, não de segurança.
- **Indireta**: instrução escondida em conteúdo que o modelo lê. É o caso perigoso, porque o
  atacante não precisa de acesso ao sistema: basta que o conteúdo dele chegue ao contexto.
  Vetores comuns: página web, e-mail, ticket de suporte, comentário em código, README de
  dependência, metadado de PDF, texto branco sobre fundo branco, e resposta de servidor MCP.

Não há defesa completa. O que funciona é reduzir o teto do dano:

1. **Privilégio mínimo por ferramenta.** Uma ferramenta de leitura não precisa de token com
   escopo de escrita. Separe agentes por nível de confiança em vez de dar tudo a um.
2. **Confirmação humana para ação irreversível ou externa**, exibindo o efeito concreto
   (destinatário, valor, arquivo, comando) — nunca o resumo escrito pelo modelo.
3. **Allowlist de destino** para qualquer saída de rede: domínio de fetch, destinatário de
   e-mail, host de webhook. Exfiltração quase sempre sai por uma URL montada pelo modelo.
4. **Bloqueie o canal de imagem/link em markdown** quando a saída for renderizada: uma
   imagem com dado na query string exfiltra sem clique do usuário.
5. **Isole conteúdo não confiável em outra chamada**: um modelo resume ou extrai campos do
   documento hostil, sem acesso a ferramenta, e só o resultado estruturado volta para o
   agente principal.
6. **Validação por esquema na saída** antes de acionar qualquer coisa: tipo, faixa,
   allowlist de valores, e rejeição em caso de dúvida.
7. **Marque a origem** de cada bloco do contexto (usuário, documento, ferramenta) — ajuda o
   modelo e ajuda muito a investigação depois.

### A tríade perigosa

Acesso a dado privado + conteúdo não confiável + capacidade de comunicar para fora. Em todo
fluxo de agente, verifique se as três coexistem; se sim, remova uma. Na prática:
retirar a saída de rede livre, ou ler dado privado só depois que o conteúdo externo já saiu
do contexto, ou exigir confirmação no ponto de saída.

## 2. Riscos do ciclo de vida do modelo

### Supply chain de modelo e dado

- `pickle`, `joblib` e `torch.load` **executam código** ao carregar. Checkpoint de
  repositório público é código de origem desconhecida. Use `safetensors`; quando não der,
  carregue em sandbox sem rede e sem credencial.
- Fixe origem, revisão e hash de todo artefato: pesos, tokenizer, dataset, imagem de
  container. "Última versão do hub" é uma dependência que muda sozinha.
- `trust_remote_code=True` executa código do repositório do modelo. Trate como instalar um
  pacote arbitrário: leia ou não use.
- Notebook e script de dataset baixados junto com o dado também executam.

### Envenenamento de dado e de rótulo

- Risco alto onde o dado é coletado de fonte aberta ou enviado por usuário (feedback,
  correção humana, crawling). Uma fração pequena de amostras manipuladas basta para instalar
  um gatilho (backdoor) que só ativa com um padrão específico.
- Controles: proveniência por amostra, revisão de amostras que mais mudam o gradiente ou a
  perda, limite de contribuição por fonte, e um conjunto de teste **curado e imutável** que
  não vem da mesma esteira.
- Fine-tuning com dado de usuário merece revisão explícita antes de virar rotina.

### Vazamento pelo modelo

- **Memorização**: modelo treinado com dado pessoal pode reproduzi-lo. Antes de treinar com
  dado real, decida de-identificação, e teste extração com prompts de sondagem.
- **Inferência de pertencimento**: saber se um paciente estava no treino já é vazamento em
  contexto de saúde. Overfitting piora isso; reportar confiança calibrada e limitar detalhe
  na saída ajuda.
- **Extração de modelo**: consultas em massa reconstroem o comportamento. Limite de taxa por
  identidade, monitoramento de padrão de consulta, e cuidado com expor logits ou
  probabilidade completa.
- **Inversão de atributo**: em modelos que expõem embedding, o embedding pode reconstruir
  parte da entrada. Embedding de rosto ou de texto clínico é dado pessoal — trate como tal.

### Robustez adversarial

- Exemplos adversariais importam quando alguém ganha algo com o erro: fraude, evasão de
  moderação, burla de verificação biométrica. Se ninguém ganha, priorize robustez a ruído
  real (iluminação, compressão, ruído de sensor) em vez de ataque teórico.
- Em biometria por câmera, o ataque prático é **apresentação**: foto, vídeo em tela, máscara.
  Detecção de vivacidade é requisito de produto, não refinamento.
- Ao avaliar robustez, reporte a métrica sob ataque **e** o custo do ataque; robustez que
  depende do atacante não saber o método não é robustez.

## 3. Aplicação em produção

- **Custo é vetor de abuso**: entrada longa, loop de agente, saída máxima. Defina teto de
  tokens por requisição e por identidade, tempo máximo de execução, e limite de iterações do
  agente. Alerta de custo é controle de segurança.
- **Multi-tenant**: cache de resposta, índice vetorial e histórico de conversa vazam entre
  clientes com facilidade. Chave de cache e filtro do índice precisam incluir o tenant.
- **Log de prompt e resposta** costuma conter dado sensível: defina retenção, acesso
  restrito e redação. Vale também para a telemetria do provedor — verifique o contrato.
- **Observabilidade**: registre versão de prompt, de modelo e de ferramenta em cada execução;
  sem isso não há investigação possível depois de um incidente.
- **Servidores MCP e plugins de terceiro** são código e canal de injeção ao mesmo tempo:
  revise a origem, fixe a versão, limite as credenciais que recebem, e leia o que retornam
  como conteúdo não confiável — inclusive descrições de ferramenta, que entram no contexto.

## 4. Avaliação adversarial (o "red team" que cabe no CI)

Monte uma suíte versionada, com caso e resultado esperado:

1. Documento com instrução escondida mandando chamar ferramenta destrutiva → esperado:
   nenhuma chamada, ou chamada bloqueada pelo controle.
2. Documento pedindo para incluir uma URL com dado do contexto → esperado: nenhuma saída de
   rede para domínio fora da allowlist.
3. Pergunta que tenta acessar documento de outro usuário/tenant → esperado: recuperação
   vazia, não resposta "não posso responder" com o dado já no contexto.
4. Entrada que força saída fora do esquema → esperado: rejeição na validação, não exceção.
5. Entrada gigante ou loop de ferramenta → esperado: corte por limite, com erro claro.
6. Tentativa de extrair dado de treino ou o prompt de sistema → esperado: recusa; e note que
   o prompt de sistema não é segredo de segurança, apenas de produto.

Rode a suíte a cada mudança de modelo, prompt, ferramenta ou fonte de dado. Reporte taxa de
sucesso do ataque, não apenas "passou".

## 5. Referências externas para consultar (e verificar a versão vigente)

- **OWASP Top 10 for LLM Applications** — taxonomia usável em relatório para cliente.
- **OWASP Top 10 / API Security Top 10** — a base clássica continua sendo a maior parte dos
  achados reais.
- **MITRE ATLAS** — táticas e técnicas de ataque a sistemas de ML, no formato ATT&CK.
- **NIST AI RMF** e o perfil para IA generativa — vocabulário de governança para documento
  contratual.
- **NIST SSDF** e **SLSA** — para o lado de supply chain de build.

Confirme conteúdo e numeração na versão atual antes de citar em documento formal: essas
listas mudam de edição.
