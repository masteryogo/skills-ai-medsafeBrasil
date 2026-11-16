# Abreviações, números, unidades e doses

Duas regras estruturam este arquivo:

1. **Abreviação é problema de glossário**, não de modelo. Mantenha um arquivo versionado no
   repositório, injete no prompt, e valide com um clínico da casa — cada serviço tem as suas.
2. **Número e unidade são problema de código.** Normalize e valide faixa em Python depois da
   extração. Pedir ao modelo para "tomar cuidado com a vírgula" não é um controle.

## Abreviações ambíguas — as que causam dano real

Estas exigem desambiguação por contexto e merecem `ambiguo: true` quando o contexto não
resolve:

| Sigla | Leituras possíveis | Como distinguir |
|---|---|---|
| `PCR` | proteína C reativa / parada cardiorrespiratória / reação em cadeia da polimerase | contexto de exame laboratorial com valor e mg/L → proteína; contexto de evolução aguda ou óbito → parada; junto de vírus ou "RT-" → biologia molecular |
| `PA` | pressão arterial / póstero-anterior (radiografia) / pressão assistida | valor `120x80 mmHg` → pressão; junto de "incidência" ou "RX de tórax" → radiologia |
| `IRA` | insuficiência renal aguda / insuficiência respiratória aguda | creatinina e ureia por perto → renal; saturação e ventilação → respiratória |
| `FA` | fibrilação atrial / frasco-ampola / fosfatase alcalina | contexto de ritmo e ECG → arritmia; em prescrição com dose → apresentação; em hemograma/hepatograma → enzima |
| `AVE` / `AVC` | acidente vascular encefálico / cerebral | sinônimos na prática; normalize para um só |
| `DM` | diabetes mellitus / doença de membrana (neonatologia) | contexto etário e de glicemia |
| `HD` | hipótese diagnóstica / hemodiálise | seção do documento resolve quase sempre |
| `TC` | tomografia computadorizada / tempo de coagulação | pedido de imagem contra coagulograma |
| `SD` | síndrome / sem dificuldade / Down | precisa do contexto completo; forte candidato a `ambiguo` |

## Abreviações comuns e sua expansão

**Estrutura do documento:** `QP` queixa principal, `HMA` história da moléstia atual, `HPP`
história patológica pregressa, `HF` história familiar, `EF` exame físico, `HD` hipótese
diagnóstica, `CD` conduta, `SIC` segundo informações do cliente.

**Diagnósticos frequentes:** `HAS` hipertensão arterial sistêmica, `DM2` diabetes mellitus
tipo 2, `IAM` infarto agudo do miocárdio, `ICC` insuficiência cardíaca congestiva, `DPOC`
doença pulmonar obstrutiva crônica, `IVAS` infecção de vias aéreas superiores, `ITU` infecção
do trato urinário, `DRC` doença renal crônica, `TVP` trombose venosa profunda, `TEP`
tromboembolismo pulmonar, `DRGE` doença do refluxo gastroesofágico, `OMA` otite média aguda.

**Exame físico:** `BEG`/`REG`/`MEG` bom/regular/mau estado geral, `LOTE` lúcido e orientado no
tempo e espaço, `MV` murmúrio vesicular, `MVUA` murmúrio vesicular universalmente audível,
`RA` ruídos adicionais, `RCR 2T BNF` ritmo cardíaco regular em 2 tempos com bulhas
normofonéticas, `ACV`/`AC` ausculta cardiovascular, `AR` ausculta respiratória, `ABD` abdome,
`RHA` ruídos hidroaéreos, `MMII`/`MMSS` membros inferiores/superiores, `TEC` tempo de
enchimento capilar, `NDN` nada digno de nota.

**Sinais vitais e exames:** `FC` frequência cardíaca, `FR` frequência respiratória, `TAX`
temperatura axilar, `SatO2`/`SpO2` saturação, `HGT` glicemia capilar, `HMG` hemograma, `Hb`
hemoglobina, `Ht` hematócrito, `Cr` creatinina, `U` ureia, `Na`/`K` sódio/potássio, `TGO`/`TGP`
transaminases, `EAS` elementos anormais e sedimentos (urina), `ECG` eletrocardiograma, `USG`
ultrassonografia, `RNM` ressonância nuclear magnética.

**Prescrição:** `VO` via oral, `IV`/`EV` intravenoso/endovenoso, `IM` intramuscular, `SC`
subcutâneo, `SL` sublingual, `IN` intranasal, `NBZ` nebulização, `cp` comprimido, `cps`
cápsula, `gts` gotas, `amp` ampola, `FA` frasco-ampola, `SOS` se necessário, `ACM` a critério
médico, `MID` mantida infusão diária, `BIC` bomba de infusão contínua, `jejum`, `SNE`/`SNG`
sonda nasoentérica/nasogástrica.

Guarde este conteúdo como um arquivo de dados do projeto (YAML ou JSON), não como texto no
prompt de cada handler, e mande o modelo devolver a forma expandida que escolheu para cada
sigla encontrada. Isso torna o erro de desambiguação visível na saída em vez de silencioso.

## Números em português brasileiro

- **Vírgula é separador decimal:** `7,5 mg` significa 7,5 e não 75. Ponto é separador de
  milhar: `1.000 mg` é mil miligramas, não 1. Um parser configurado em locale inglês
  transforma `1.000` em `1,0` — erro de fator mil em dose.
- **Pressão arterial usa `x`:** `120x80 mmHg`, lido "cento e vinte por oitenta". Também
  aparece como `120/80`, `120 x 80`, `PA 12x8` (em centímetros de mercúrio informal). Aceite
  as variantes e normalize para dois inteiros em mmHg, tratando `12x8` como `120x80`
  explicitamente sinalizado como convertido.
- **Números escritos como palavra** aparecem muito em transcrição de áudio: "trinta e sete e
  meio", "cento e vinte por oitenta", "meio comprimido", "um e meio". Converta em código, com
  teste unitário, e nunca aceite o resultado sem validação de faixa.
- **Intervalo e aproximação:** `2-3 dias`, `há ~1 semana`, `>38°C`, `<90%`. Guarde o operador,
  não descarte para um número só.
- **Unidade colada ou ausente:** `500mg`, `500 mg`, `0,5g`, e o pior caso — `Dipirona 1` sem
  unidade nenhuma. Sem unidade explícita o campo é `nao_informado`, jamais um palpite.

## Doses, vias e frequências

Normalize para campos separados e nunca para uma string única:

```
medicamento:
  principio_ativo: str          # normalizado pela DCB quando possível
  nome_comercial: str | null
  dose_valor: float | null
  dose_unidade: mg|mcg|g|mL|UI|gts|cp | null
  via: VO|IV|IM|SC|SL|IN|NBZ|topica | null
  frequencia_texto: str | null  # como apareceu
  intervalo_horas: float | null # normalizado
  duracao_dias: int | null
  se_necessario: bool
  trecho: str
```

**Conversões e armadilhas de unidade:**

- `mcg`, `µg` e `mg` — fator mil. `0,5 mg` = `500 mcg`. Levotiroxina, fentanil e adrenalina
  são prescritos em mcg e a confusão é clinicamente séria. Guarde a unidade original e a
  normalizada, ambas.
- `UI` (unidade internacional) não converte para massa. Insulina, heparina e vitamina D usam
  UI; qualquer conversão automática está errada.
- `mL` de solução não é dose de fármaco sem a concentração (`Dipirona 500 mg/mL, 20 gts`).
  Se a concentração não está no texto, a dose em massa é `nao_informado`.
- `mg/kg/dia` em pediatria depende do peso: extraia a fórmula, não um número absoluto, e
  marque que depende de peso.
- `gts` (gotas) depende do equipo e do medicamento — mantenha como texto, não converta.

**Frequência:** `6/6h`, `8/8h`, `12/12h`, `1x ao dia`, `2x/dia`, `3xdia`, `de 8 em 8 horas`,
`1 cp pela manhã`, `à noite`, `em jejum`, `SOS`, `ACM`, `dose única`, `agora`, `contínuo`.
Normalize `N/Nh` para `intervalo_horas = N` e `Mx ao dia` para `24/M`, guardando sempre o
texto original. `SOS` e `ACM` não são intervalos — vão para `se_necessario` e para observação.

## Validação de faixa

Depois de normalizar, valide e **sinalize em vez de aceitar**. Um valor fora de faixa é quase
sempre erro de extração ou de transcrição, não uma medida real:

| Campo | Faixa plausível |
|---|---|
| FC | 30-220 bpm |
| FR | 8-60 irpm |
| PA sistólica / diastólica | 60-250 / 30-150 mmHg, e sistólica > diastólica |
| Temperatura axilar | 34-42 °C |
| SpO2 | 50-100% |
| Peso adulto / pediátrico | 30-300 kg / 0,5-100 kg |
| Glicemia capilar | 20-600 mg/dL |
| Dose oral por tomada | acima de 4 g de qualquer fármaco merece revisão |

Registre a violação num campo `alertas` da saída e leve o documento para revisão humana em
vez de rejeitá-lo em silêncio. `PA 1200x80` é claramente erro de digitação; o sistema deve
dizer isso, e não escolher sozinho o que o clínico quis dizer.
