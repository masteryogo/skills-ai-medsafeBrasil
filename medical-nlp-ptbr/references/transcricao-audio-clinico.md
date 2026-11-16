# Transcrição de áudio clínico em português

O Whisper transcreve português conversacional muito bem e erra exatamente onde dói: **nome de
medicamento e número**. A frase inteira sai fluente e plausível com a dose errada, o que é
pior do que sair truncada — ninguém desconfia.

Consequência de projeto: a transcrição é insumo, não resultado. Todo campo crítico derivado
de áudio passa por confirmação explícita do profissional antes de virar documento.

## Configuração do faster-whisper

```python
from faster_whisper import WhisperModel

model = WhisperModel("large-v3", device="cuda", compute_type="float16")
# CPU: device="cpu", compute_type="int8"

segments, info = model.transcribe(
    caminho_audio,
    language="pt",                    # sempre explícito, nunca autodetectar
    vad_filter=True,                  # corta silêncio: reduz alucinação
    vad_parameters=dict(min_silence_duration_ms=500),
    beam_size=5,
    condition_on_previous_text=False,  # evita loop de repetição
    word_timestamps=True,             # habilita confiança por palavra
    initial_prompt=PROMPT_DOMINIO,
    temperature=0,
)
```

Pontos que importam:

- **`language="pt"` sempre.** Autodetecção erra em áudio curto, ruidoso ou que começa com
  hesitação, e uma detecção errada produz transcrição em espanhol com aparência correta.
- **Modelo grande para uso clínico.** A diferença entre `small` e `large-v3` concentra-se
  justamente em jargão e nome próprio. Se o custo do modelo grande for proibitivo em produção,
  meça a queda em nome de medicamento e número especificamente antes de descer de tamanho — a
  WER geral engana.
- **`condition_on_previous_text=False`.** Com o condicionamento ligado, o Whisper entra em
  loop repetindo a última frase quando encontra silêncio ou ruído, e o loop pode consumir
  minutos de transcrição inventada.
- **VAD ligado.** Alucinação em trecho sem fala é um comportamento conhecido do Whisper — ele
  preenche silêncio com frases plausíveis, incluindo textos genéricos aprendidos no treino.
  Cortar o silêncio antes é a defesa mais eficaz.
- **`word_timestamps=True`** entrega `probability` por palavra, que é a base do fluxo de
  revisão descrito abaixo.

## `initial_prompt` de domínio

O `initial_prompt` condiciona o vocabulário e o estilo de formatação. Use-o para injetar os
termos do seu domínio e um exemplo do formato desejado:

```python
PROMPT_DOMINIO = (
    "Consulta médica em português do Brasil. Termos frequentes: dipirona, "
    "amoxicilina, losartana, metformina, omeprazol, levotiroxina, sinvastatina, "
    "hidroclorotiazida, pressão arterial, frequência cardíaca, saturação, "
    "hipertensão arterial sistêmica, diabetes mellitus. "
    "Exemplo de formato: A pressão está 120 por 80. Dipirona 500 mg de 6 em 6 horas."
)
```

Regras de uso:

- **Liste os medicamentos e termos que realmente aparecem no seu serviço**, extraídos da sua
  base de prescrições — não uma lista genérica. Ganho concreto em nome próprio.
- **Não passe uma lista longa demais.** O `initial_prompt` consome janela de contexto do
  modelo de áudio; algumas dezenas de termos, os mais frequentes e os mais confundidos.
- **Inclua um exemplo de número no formato que você quer.** Isso influencia se o Whisper
  escreve "120 por 80" ou "120x80", e reduz trabalho de normalização depois.
- **Cuidado com viés induzido:** termos no prompt aumentam a chance de o modelo ouvi-los
  mesmo quando não foram ditos. Se você listar `losartana`, `lorazepam` dito no áudio pode
  virar `losartana`. Mantenha a lista curta e teste o efeito nos dois sentidos.

## Confiança por palavra e roteamento para revisão

Com `word_timestamps=True`, cada palavra vem com `probability`. Use isso em vez de tratar a
transcrição como bloco homogêneo:

1. Marque como suspeitas as palavras abaixo de um limiar calibrado no seu áudio (comece em
   torno de 0,5-0,6 e ajuste medindo).
2. **Trate número e nome de medicamento como sempre suspeitos**, independente da
   probabilidade. É o ponto onde o modelo é confiante e errado.
3. Na interface, destaque o trecho suspeito e ofereça o áudio daquele intervalo — o
   `word_timestamps` dá o recorte exato. Revisar 8 segundos é aceitável; reouvir 20 minutos
   não é, e na prática ninguém faz.
4. Bloqueie a geração do documento final enquanto campo crítico derivado de trecho suspeito
   não estiver confirmado.

## Áudio de WhatsApp e Telegram

- Chega em **OPUS/OGG com bitrate baixo e mono**, gravado em ambiente não controlado. A
  qualidade é sensivelmente pior que a de uma gravação de teleconsulta, e a WER sobe.
  Meça separadamente por canal; um limiar calibrado em áudio de consulta não vale para áudio
  de WhatsApp.
- **Não reencode em formato com perdas** de novo. Converta direto para PCM 16 kHz mono
  (`ffmpeg -i entrada.ogg -ar 16000 -ac 1 -c:a pcm_s16le saida.wav`), que é o que o Whisper
  consome internamente.
- **Normalize o volume** (`loudnorm` ou `dynaudnorm`) quando os áudios variarem muito de
  nível; áudio muito baixo degrada mais que áudio ruidoso.
- **Imponha limite de duração** e trate o áudio longo em pedaços com sobreposição pequena,
  costurando pelos timestamps. Áudio de 30 minutos num handler de webhook estoura o timeout
  do provedor muito antes de terminar.
- **Idempotência por id da mensagem**: o provedor reenvia, e transcrever duas vezes custa
  dinheiro e pode gerar dois documentos.

## Múltiplos falantes

Teleconsulta tem pelo menos dois falantes, e atribuir a fala errada inverte o sentido
clínico — "sinto dor no peito" dito pelo paciente contra dito pelo médico repetindo a queixa
são coisas diferentes para a extração.

- O Whisper **não faz diarização**. Precisa de uma etapa separada (`pyannote.audio`, ou
  `whisperx`, que também alinha as palavras) e os dois resultados são combinados por
  timestamp.
- Diarização em áudio de baixa qualidade com sobreposição de fala erra bastante. Se o produto
  permitir, **grave canais separados** ou peça fala alternada — resolve na origem o que é
  caro resolver depois.
- Quando a atribuição for incerta, marque `falante: indeterminado` em vez de escolher. Para a
  extração, um trecho de falante indeterminado deve ir para revisão, não para o campo.

## O que medir

A WER global é a métrica menos útil aqui. Meça, no **seu** áudio, com um conjunto de
referência transcrito por humano:

1. **WER global** — só como linha de base e para comparar configurações.
2. **Taxa de erro em número** — a fração de números na referência que saíram errados ou
   ausentes. É a métrica que decide se o produto pode confiar em dose e sinal vital.
3. **Taxa de erro em nome de medicamento** — idem, medida contra a lista de princípios ativos.
   Conte erro que troca o fármaco por outro real separadamente: é o pior caso e o menos
   visível.
4. **Taxa de alucinação** — trechos transcritos onde não havia fala. Meça em áudios com
   silêncio e ruído propositais.
5. **Erro por canal e por condição** — WhatsApp contra consulta, com e sem ruído de fundo, um
   e dois falantes. É o que diz onde o produto funciona.

Documente a métrica por condição e declare as condições de uso suportadas. Um número único de
WER, medido em áudio limpo, é o tipo de resultado que passa em demonstração e falha em
produção.
