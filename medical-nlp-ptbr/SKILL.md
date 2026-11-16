---
name: medical-nlp-ptbr
description: Processar texto clínico em português brasileiro com rigor - extracao estruturada de prontuario, anamnese e receita, negacao e hipotese diagnostica, abreviacoes medicas ambiguas, doses e unidades, transcricao de audio clinico com Whisper, codificacao CID-10/LOINC/DCB, de-identificacao de dados de paciente e avaliacao campo a campo. Use quando o trabalho envolver prontuario, evolucao, anamnese, laudo, receita, atestado, teleconsulta, texto ou audio de paciente, extracao de sintomas, medicamentos, alergias ou exames - clinical text, medical NLP, clinical entity extraction, EHR, prontuario eletronico, Whisper transcription of consultations.
user-invocable: true
---

# NLP clínico em português brasileiro

Em texto clínico, o modelo de linguagem quase nunca falha por não entender português. Ele
falha em quatro pontos específicos, e todos os quatro são invisíveis numa leitura rápida da
saída:

1. **Negação e hipótese** — "nega dor torácica" vira `dor_toracica: true`.
2. **Abreviação ambígua** — `PCR` é proteína C reativa, parada cardiorrespiratória ou reação
   em cadeia da polimerase, e a escolha muda o significado do documento.
3. **Número e unidade** — vírgula decimal, `120x80`, `mg` contra `mcg`, `1.000 mg`.
4. **Sujeito do achado** — "mãe hipertensa" atribuído ao paciente.

E o erro aqui é **assimétrico**: uma dose errada, uma alergia omitida ou uma negação
invertida é um evento de segurança, não um ponto de métrica. Trate esses campos de forma
diferente do resto desde o início.

## Postura obrigatória

- **A saída é rascunho para revisão de um profissional, nunca resultado final.** Nada aqui
  produz diagnóstico ou conduta por conta própria. O sistema estrutura, organiza e transcreve
  o que o profissional disse ou escreveu; a decisão clínica e a responsabilidade continuam
  sendo dele. Desenhe a revisão humana como parte do fluxo, não como aviso no rodapé.
- **Extração é extrativa e atribuível.** Todo campo preenchido carrega o trecho original que
  o originou, e a interface mostra esse trecho. Sem isso o revisor não tem como conferir, e
  na prática ele deixa de conferir.
- **Campo ausente é `null`, jamais um valor plausível.** O schema precisa de
  `nao_informado` explícito em cada campo, e o prompt precisa dizer que deixar vazio é a
  resposta correta. É esse detalhe que evita a maior parte das invenções.
- **Nunca inferir o que não está escrito.** Não completar dose ausente com a dose usual, não
  deduzir diagnóstico a partir de sintoma, não normalizar "dor no peito" para um CID sem
  marcar que foi inferência. Inferência, quando existir, vai em campo separado e sinalizado.
- **Confirme com um clínico** o glossário de abreviações, a definição de cada campo e o
  conjunto de teste. Ambiguidade de definição de campo produz ruído de rótulo, e ruído de
  rótulo é o teto da qualidade — nenhum prompt passa dele.

## Ordem de trabalho

1. **Junte 20-30 documentos reais** (ou trechos, se houver restrição de acesso) e leia. Você
   vai descobrir as abreviações da casa, o estilo de quem digita e os campos que na prática
   nunca vêm preenchidos.
2. **Defina o schema com um clínico**, campo por campo, com a regra de cada caso duvidoso
   escrita: história familiar entra? sintoma negado entra como `false` ou fica fora?
   medicamento em uso prévio e medicamento prescrito hoje são o mesmo campo?
3. **Monte o conjunto de teste anotado** antes de escrever o prompt, marcando quais campos
   são críticos de segurança. Veja `references/avaliacao-e-terminologia.md`.
4. **Construa o glossário do projeto** de abreviações e unidades como arquivo versionado, e
   injete no prompt. Veja `references/abreviacoes-unidades-numeros.md`.
5. **Extraia com saída estruturada validada** (JSON schema ou tool calling, depois Pydantic),
   temperatura 0. A disciplina de aplicação está na skill `llm-app-engineer`.
6. **Meça por campo**, com os campos críticos reportados separadamente e com ênfase em
   recall.
7. **Só então** otimize custo, modelo e latência, remedindo a cada passo.

## Os quatro erros, em resumo

**Negação, hipótese, sujeito e tempo.** O gatilho quase sempre está numa janela curta em
volta do achado: *nega*, *sem*, *ausência de*, *descartado*, *NDN*, *hipótese diagnóstica*,
*a esclarecer*, *não se pode excluir*, *história familiar de*, *há 10 anos*, *se piorar*.
Cada categoria pede um campo próprio no schema — `presente` / `ausente` / `suspeito` /
`nao_informado`, mais `sujeito` (paciente ou familiar) e `temporalidade` (atual, pregresso,
hipotético). Um booleano simples não representa prontuário e é a origem do erro mais grave e
mais comum. Listas de gatilhos e o desenho do schema estão em
`references/negacao-e-contexto.md`.

**Abreviação.** Não confie no modelo para desambiguar sozinho. Passe o glossário do projeto no
prompt, force a saída a registrar a forma expandida escolhida, e mande sinalizar
`ambiguo: true` quando o contexto não resolver — em vez de escolher em silêncio.

**Número e unidade.** Normalize em código, não no prompt: vírgula decimal, ponto de milhar,
`120x80 mmHg`, `mg`/`mcg`/`g`/`UI`, `6/6h`, `VO`/`IV`/`SC`/`SL`, `mg/kg/dia`. Depois valide
faixa plausível e rejeite o improvável em vez de aceitar calado. Detalhes e tabelas em
`references/abreviacoes-unidades-numeros.md`.

**Áudio.** Whisper em consulta em português erra justamente nome de medicamento e número, que
são os campos que importam. Configuração, `initial_prompt`, uso das probabilidades por
palavra e o que medir estão em `references/transcricao-audio-clinico.md`.

## Privacidade e conformidade

Dado de saúde é dado pessoal sensível na LGPD (art. 11) — a base legal, a minimização e o
prazo de retenção precisam estar decididos e escritos, não implícitos. Pontos práticos:

- **Minimize antes de sair da sua infraestrutura.** Se a tarefa não precisa do nome, do CPF ou
  do CNS, remova ou mascare antes de chamar o provedor de LLM ou de transcrição. Registre no
  repositório a decisão e os termos de tratamento e retenção do provedor.
- **De-identificação em português é imperfeita.** Nome, CPF, CNS, RG, endereço, telefone,
  data de nascimento, nome da mãe e número de prontuário são os alvos; nomes brasileiros
  colidem com palavras comuns, então nenhum de-identificador é completo. Nunca afirme que o
  texto está anonimizado — diga o que foi removido e com que taxa medida.
- **Trilha de auditoria**: quem gerou, quem revisou, quando, e qual versão do prompt e do
  modelo produziram cada documento.
- **Prazo de guarda do prontuário** e regras de teleconsulta seguem normas do CFM e do
  Ministério da Saúde (guarda de prontuário pela Res. CFM 1.821/2007, telemedicina pela Res.
  CFM 2.314/2022, RNDS em FHIR para interoperabilidade). Regulação muda: confirme a vigência
  na fonte antes de tratar qualquer prazo ou exigência como definitivo, e não deduza norma de
  memória.

## Como reportar resultado

Métrica por campo, campos críticos em separado, e o que ainda quebra:

> Extração de receita, conjunto ouro de 42 documentos revisados por médica. Campos gerais:
> 89% de acerto exato após normalização. Campos críticos — princípio ativo 100%, dose 93%
> (3 erros, todos de vírgula decimal na transcrição), via 100%, frequência 90% (`ACM` e `SOS`
> não estavam no glossário). Negação: 2 falsos positivos em 18 achados negados, ambos com
> "nega" separado do sintoma por oração intercalada. Nenhum medicamento inventado.

Diga com clareza quando não está pronto para uso clínico e o que falta. Em campo crítico,
recall alto com revisão humana é preferível a precisão alta com omissão silenciosa: um campo
a mais para o revisor descartar custa segundos, um campo omitido ele não tem como perceber.

## Arquivos de referência

- `references/negacao-e-contexto.md` — gatilhos de negação, incerteza, sujeito e
  temporalidade em português, desenho do schema e armadilhas de escopo.
- `references/abreviacoes-unidades-numeros.md` — glossário de abreviações com as
  ambiguidades reais, normalização de números, doses, vias e frequências, validação de faixa.
- `references/transcricao-audio-clinico.md` — faster-whisper em consulta em português,
  `initial_prompt`, alucinação em silêncio, confiança por palavra, áudio de WhatsApp,
  diarização e o que medir.
- `references/avaliacao-e-terminologia.md` — conjunto ouro, métrica por campo, campos
  críticos, concordância entre anotadores, e codificação CID-10 / LOINC / DCB / TUSS.
