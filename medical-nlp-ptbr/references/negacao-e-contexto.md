# Negação, incerteza, sujeito e temporalidade

Um achado mencionado no texto não é um achado presente no paciente. Quatro eixos decidem o
significado, e todos os quatro precisam existir no schema. Extrair só "o sintoma foi
mencionado" é o erro mais grave e mais frequente em NLP clínico.

## O schema mínimo

```
achado:
  termo: str                  # como apareceu no texto
  trecho: str                 # span original, para o revisor conferir
  status: presente | ausente | suspeito | nao_informado
  sujeito: paciente | familiar | outro
  temporalidade: atual | pregresso | hipotetico
  gatilho: str | null         # a palavra que determinou status/sujeito/temporalidade
```

Exigir o campo `gatilho` melhora a saída de forma desproporcional: obriga o modelo a apontar
a evidência da decisão, e dá ao revisor (e ao seu conjunto de teste) como auditar o
raciocínio em vez de só o resultado.

## Gatilhos de negação

Frequentes em prontuário brasileiro:

- **Verbo de negação do relato:** `nega`, `negou`, `nega que`, `não refere`, `não relata`,
  `não apresenta`, `não queixa`, `não há`, `não observado`, `não evidenciado`,
  `não identificado`
- **Preposição e substantivo:** `sem`, `ausência de`, `ausente`, `livre de`, `isento de`,
  `nenhum`, `nenhuma`
- **Exclusão diagnóstica:** `descartado`, `descartada`, `afastado`, `afastada`, `excluído`,
  `excluída`, `sem evidência de`, `resultado negativo para`, `negativo para`, `não compatível
  com`
- **Fórmulas de normalidade** (negam tudo de um sistema de uma vez, e por isso são as mais
  perigosas): `sem alterações`, `SA`, `dentro da normalidade`, `DLN`, `nada digno de nota`,
  `NDN`, `exame normal`, `BEG` (bom estado geral), `MVUA sem RA` (murmúrio vesicular
  universalmente audível sem ruídos adicionais), `RCR 2T BNF sem sopros`, `abdome flácido,
  indolor, sem massas`
- **Negação de exame/procedimento:** `não realizado`, `não coletado`, `prejudicado`,
  `não avaliado` — que é `nao_informado`, e não `ausente`. Confundir os dois faz o sistema
  afirmar que algo está normal quando ninguém olhou.

## Gatilhos de incerteza (status `suspeito`)

`hipótese diagnóstica`, `HD`, `HD1`/`HD2`, `suspeita de`, `suspeito de`, `possível`,
`provável`, `aparente`, `a esclarecer`, `a investigar`, `a confirmar`, `não se pode excluir`,
`não podemos afastar`, `sugestivo de`, `compatível com`, `sinais que podem indicar`,
`diagnóstico diferencial`, `d/d`, `aguardando resultado`, `?` colado ao termo
(`pneumonia?`), `versus` entre dois diagnósticos (`ITU vs pielonefrite`).

`compatível com` e `sugestivo de` aparecem muito em laudo de imagem e são regularmente
tratados como confirmação. São incerteza: o laudo descreve, quem confirma é o clínico.

## Gatilhos de sujeito diferente do paciente

`história familiar de`, `HF`, `antecedente familiar`, `mãe`, `pai`, `irmão`, `irmã`, `avó`,
`avô`, `filho`, `filha`, `tio`, `primo`, `cônjuge`, `parceiro`, `contactante`,
`caso na família`, `na família`.

Em pediatria e obstetrícia o eixo se complica: o acompanhante fala do paciente, e em
pré-natal existem dois sujeitos reais (gestante e feto). Defina isso explicitamente no
schema quando o domínio incluir esses casos — `sujeito: gestante | feto` — em vez de deixar
o modelo escolher.

Cuidado também com `SIC` (segundo informações do cliente/colhedor): não muda o sujeito, mas
marca que a informação é relato de terceiro, não observação. Vale um campo `fonte`.

## Gatilhos de temporalidade

- **Pregresso** (pode estar resolvido): `história de`, `HPP`, `antecedente de`, `prévio`,
  `pregresso`, `passado`, `há N anos`, `em 2019`, `submetido a`, `operado de`, `ex-tabagista`
- **Hipotético / condicional** (não é achado nenhum): `se piorar`, `caso apresente`,
  `orientado a retornar se`, `em caso de`, `risco de`, `profilaxia de`, `rastreio para`,
  `prevenção de`, `orientações sobre`, `alertado para sinais de`

A frase "orientada a retornar em caso de febre, dispneia ou dor torácica" contém três
sintomas e nenhum achado. Sem o eixo de temporalidade, o extrator inventa três sintomas no
paciente — e o texto de orientação está no fim de praticamente toda evolução.

## Armadilhas de escopo

O erro raramente é não reconhecer o gatilho; é errar **até onde ele alcança**.

- **Lista sob uma única negação:** "nega febre, tosse e dispneia" — três achados ausentes. O
  extrator costuma marcar o primeiro como ausente e os outros dois como presentes.
- **Negação interrompida:** "nega, no momento, dor torácica" ou "nega — apesar do relato do
  acompanhante — perda de peso". A distância entre gatilho e termo quebra heurística de
  janela fixa.
- **Mudança de polaridade no meio da frase:** "nega febre, **mas** refere calafrios". O `mas`
  encerra o escopo da negação. Vale para `porém`, `entretanto`, `contudo`, `embora`,
  `apesar de`.
- **Dupla negação:** "não se pode excluir ausência de..." — raro, e sempre vale marcar
  `ambiguo` em vez de decidir.
- **Negação parcial:** "sem dor torácica típica" nega o *qualificador*, não o sintoma.
- **Cabeçalho de seção como escopo:** em "ANTECEDENTES FAMILIARES:" tudo abaixo tem sujeito
  familiar até a próxima seção; em "HIPÓTESES DIAGNÓSTICAS:" tudo abaixo é `suspeito`. Passar
  a estrutura de seções para o modelo, e extrair seção por seção, resolve uma classe grande
  de erros de uma vez — e é mais confiável que esperar que ele entenda o documento inteiro
  de uma vez.

## Como implementar

- **Divida o documento em seções antes de extrair** (QP, HMA, HPP, HF, EF, exames, HD, CD) e
  extraia por seção, passando o nome da seção no prompt. Ganho grande, esforço pequeno.
- **Não escreva um sistema de regras tipo NegEx do zero** para um produto novo: use o modelo
  com o schema acima, e reserve as listas de gatilhos deste arquivo para (a) o prompt, (b) o
  conjunto de teste, e (c) um verificador em código que sinaliza discordância entre o gatilho
  achado por regex e o status que o modelo devolveu. Essa discordância é um bom candidato a
  revisão humana.
- **Sature o conjunto de teste com esses casos.** Toda armadilha desta página merece pelo
  menos um caso real: lista sob negação, `mas`, "não realizado", seção de familiares, e a
  frase de orientação no fim da evolução.
- **Relate negação como métrica própria** — falsos positivos em achados negados, contados
  separadamente. Um índice geral de 90% pode esconder inversão em metade das negações.
