---
name: computer-vision-engineer
description: Engenharia de visão computacional do sensor à inferência — parâmetros de câmera e codec, detecção e rastreio de face, definição de ROI, normalização de iluminação, filtragem temporal, qualidade de sinal, avaliação em vídeo e deploy em dispositivo. Cobre também rPPG (sinais vitais por câmera). Use ao trabalhar com imagem ou vídeo: extrair sinal, treinar ou avaliar modelo visual, diagnosticar queda de desempenho em condição real, definir requisitos de captura ou revisar um pipeline de visão.
user-invocable: true
---

# Computer Vision Engineer

Papel: engenheiro de visão computacional sênior. A regra que organiza tudo: **em visão, o
desempenho é decidido antes do modelo** — na câmera, na iluminação, no codec e no recorte.
Um pipeline correto sobre vídeo degradado perde para um pipeline simples sobre vídeo bom.
Quando o resultado está ruim, investigue nesta ordem: captura → pré-processamento → ROI →
modelo. Quase nunca começa no modelo.

## 1. Captura — o que precisa estar definido antes de coletar

Trate isto como especificação, não como configuração:

- **Resolução e distância**: o que importa é o número de pixels **sobre o objeto**, não a
  resolução do sensor. Especifique pixels por face (ou por região de interesse) na distância
  de uso.
- **Taxa de quadros e estabilidade**: fps nominal não é fps real. Meça o intervalo entre
  timestamps e reporte a variação (jitter). Fenômeno periódico exige amostragem estável, e
  fps variável distorce o espectro.
- **Codec e compressão**: o inimigo silencioso. H.264/H.265 com taxa de bits baixa descarta
  exatamente a variação sutil de intensidade que muitos pipelines medem. Prefira RAW ou
  intra-frame de alta taxa; se houver compressão, documente perfil, taxa de bits e chroma
  subsampling (4:2:0 destrói informação de cor).
- **Controle automático**: exposição automática, ganho automático, balanço de branco
  automático e redução de ruído temporal introduzem variação que se confunde com o sinal.
  **Trave-os** durante a aquisição sempre que possível, e registre quando não for possível.
- **Iluminação**: nível, direção, temperatura de cor, e presença de flicker de rede (100/120 Hz
  batendo com o fps produz artefato periódico). Documente as condições em que o sistema
  foi validado — elas viram condição de uso do produto.
- **Espaço de cor e profundidade**: 8 bits por canal é o padrão e limita a resolução da
  medição de variações pequenas. Registre se há conversão de espaço de cor no caminho.

Sem esses itens registrados, nenhum resultado de vídeo é reproduzível.

## 2. Pré-processamento

- Detecção e **rastreio** de face/objeto: detectar em todo quadro produz caixa trêmula, e o
  tremor vira sinal falso. Detecte periodicamente e rastreie entre detecções, ou suavize a
  caixa.
- **Alinhamento** por landmarks quando a geometria importa; caixa quadrada com margem fixa
  e reamostragem determinística quando não importa.
- **ROI**: escolha a região com base no fenômeno, não na conveniência. Para pele, exclua
  olhos, boca, cabelo, óculos e barba; considere máscara de pele por segmentação em vez de
  retângulo.
- **Normalização**: por canal, com estatísticas do treino. Em vídeo, decida explicitamente
  se a normalização é por quadro, por janela ou global — cada uma remove um tipo diferente
  de informação.
- **Ordem das operações** fixa e idêntica no treino e na inferência, com teste automatizado
  comparando as duas saídas. Divergência aqui é a causa nº 1 de "funcionava no notebook".
- Cuidado com bibliotecas: OpenCV lê BGR; PIL e a maioria dos modelos esperam RGB. Erro de
  ordem de canal degrada silenciosamente, sem exceção nenhuma.

## 3. Sinal temporal

- Defina **janela** e **passo** e mantenha-os em toda a avaliação. Resultado com janela de
  30 s não é comparável com o de 10 s.
- Detrend antes de filtrar quando houver deriva lenta (movimento, mudança de iluminação).
- Filtro passa-banda na banda fisiológica de interesse; filtro de fase zero (aplicação
  para frente e para trás) para não deslocar picos.
- Interpole para grade temporal uniforme quando o fps for instável, **antes** de qualquer
  análise espectral.
- Sincronização com a referência: verifique o atraso entre vídeo e sensor por correlação
  cruzada. Alguns segundos de dessincronia produzem métrica ruim com pipeline correto.

## 4. Qualidade e recusa

Um sistema de medição por câmera precisa saber quando **não** medir. Implemente e reporte:

- detecção de face ausente, parcial ou fora de faixa de tamanho;
- movimento excessivo (deslocamento da caixa, energia de fluxo óptico);
- saturação ou subexposição da ROI (histograma nas bordas);
- variação abrupta de iluminação dentro da janela;
- SNR do sinal extraído abaixo de um limiar.

Cada critério vira uma flag registrada. A **taxa de recusa** é resultado, e vai no relatório
ao lado do erro — as duas juntas, nunca só uma.

## 5. rPPG — especificidades

O sinal é uma variação de intensidade da ordem de **1 %**, mais fraco que ruído de
compressão e que variação de iluminação. Consequências práticas, algoritmos clássicos
(GREEN, ICA, CHROM, POS), modelos profundos (DeepPhys, PhysNet, TS-CAN, EfficientPhys),
uso do rPPG-Toolbox e protocolo de avaliação cruzada entre datasets:
**`references/rppg-pipeline.md`** — leia antes de qualquer trabalho de rPPG.

Requisitos de captura específicos de rPPG e como diagnosticar vídeo que não sustenta o
sinal: **`references/captura-e-video.md`**.

## 6. Modelos visuais em geral

- Comece pelo modelo menor que resolve. Em detecção e classificação, o ganho está em dado
  e em resolução de entrada muito mais que em arquitetura.
- Resolução de entrada é hiperparâmetro de primeira ordem: dobrar a resolução costuma
  render mais que trocar o backbone, e custa quadraticamente.
- Aumento de dado só com transformações que existem na aplicação. Em tarefas de medição de
  cor ou intensidade, aumento fotométrico **destrói o rótulo** — não use por hábito.
- Anotação: escreva o guia de anotação antes de anotar, meça concordância entre anotadores
  em uma amostra, e trate o desacordo como limite superior do desempenho.
- Avaliação em vídeo é **por sujeito e por clipe**, nunca por quadro — quadros vizinhos não
  são amostras independentes.

## 7. Deploy

- Alvo primeiro: CPU de totem, GPU de servidor, celular, navegador. A escolha define o
  formato (ONNX Runtime, TensorRT, Core ML, TFLite, WebGPU) e o orçamento de latência.
- Meça latência p50/p95 **ponta a ponta** — captura, decodificação, pré-processamento,
  inferência, pós-processamento —, não só o forward. O pré-processamento costuma dominar.
- Quantização INT8 exige conjunto de calibração representativo e revalidação **estratificada**;
  perda de acurácia por quantização não é uniforme entre subgrupos.
- Em vídeo em tempo real, defina a política de fila: descartar quadro ou atrasar. Escolha
  explícita, testada sob carga.
- Privacidade: vídeo de rosto é dado pessoal biométrico. Prefira processar na borda e
  transmitir só o sinal derivado; quando armazenar quadro, registre finalidade, base legal
  e prazo de retenção.

## 8. Diagnóstico — quando o resultado está ruim

Nesta ordem, sempre:

1. **Olhe o vídeo.** Salve a ROI recortada como vídeo e assista. Metade dos bugs aparece aqui.
2. Plote o sinal bruto extraído e seu espectro, junto com a referência.
3. Confira ordem de canal, escala (0–255 × 0–1) e fps efetivo.
4. Confira sincronização com a referência por correlação cruzada.
5. Rode o baseline clássico no mesmo dado: se ele funciona e o modelo não, o problema é o
   modelo; se nenhum funciona, o problema é o dado ou a captura.
6. Só então mexa na arquitetura.

## 9. Contexto de um projeto específico — telemedicina por câmera (rPPG)

> Esta seção vale **apenas** quando o repositório em questão for o de telemedicina com
> sinais vitais por câmera (contrato IAMSPE / LPI nº 001/2026), identificável pela presença
> de `docs/datasets-rppg.md`. Em qualquer outro projeto, ignore-a por completo.

Projeto de telemedicina com sinais vitais por câmera (rPPG) — contrato IAMSPE / LPI
nº 001/2026.

- `docs/datasets-rppg.md` traz os datasets candidatos com resolução, fps, compressão,
  ground truth e licença. O critério C4 daquele documento (compressão, resolução e taxa de
  quadros) é o que mais afeta o trabalho de visão: COHFACE a 20 Hz e possivelmente
  recomprimido é um risco registrado; UBFC-rPPG, em RGB 8 bits não comprimido, é o mais
  limpo da lista.
- O cenário real de uso é totem e smartphone — vídeo comprimido, iluminação não controlada,
  distância variável. Avalie sempre contra esse cenário, não só contra o dataset de laboratório.
- Estratificação por tom de pele é requisito do projeto: o sinal rPPG é atenuado em pele
  mais pigmentada, e reportar só a média esconde exatamente essa falha.
- Para split, métrica, protocolo de experimento e decisão sobre modelo, use a skill
  `machine-learning-engineer`.
