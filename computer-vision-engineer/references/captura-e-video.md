# Captura e vídeo

Referência de apoio da skill `computer-vision-engineer`. Use ao especificar uma coleta, ao
avaliar se um vídeo de terceiros serve, ou ao diagnosticar sinal ruim.

## 1. Especificação mínima de uma coleta

Registre todos os itens abaixo. O que não estiver registrado não é reproduzível.

| Item | Por que importa |
|---|---|
| Modelo de câmera e sensor | Define ruído, resposta espectral e bandas dos canais |
| Resolução e distância de uso | O que conta é pixel sobre a região de interesse |
| fps nominal **e** medido (com jitter) | Análise espectral depende de amostragem estável |
| Codec, perfil, taxa de bits, chroma subsampling | Compressão com perda destrói variação sutil |
| Exposição, ganho, balanço de branco: fixos ou automáticos | Automático injeta variação que imita sinal |
| Iluminação: tipo, nível (lux), direção, temperatura de cor | Define a condição de validade declarada |
| Flicker de rede (50/60 Hz) | Bate com o fps e cria artefato periódico |
| Sensor de referência, taxa de amostragem e método de sincronização | Sem isso não há rótulo confiável |
| Protocolo do sujeito (repouso, fala, movimento, duração) | Define o que o dataset consegue sustentar |
| Consentimento e base legal | Vídeo de rosto é dado pessoal biométrico |

## 2. Como verificar um vídeo antes de confiar nele

```bash
# metadados reais do arquivo (não o que a documentação promete)
ffprobe -v error -show_streams -show_format entrada.mp4

# codec, resolução, fps, formato de pixel e taxa de bits, em uma linha
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,width,height,r_frame_rate,avg_frame_rate,pix_fmt,bit_rate \
  -of default=noprint_wrappers=1 entrada.mp4

# timestamps de cada quadro — para medir jitter e fps efetivo
ffprobe -v error -select_streams v:0 -show_entries frame=pkt_pts_time \
  -of csv=p=0 entrada.mp4 | head -300
```

O que olhar:

- `pix_fmt` **yuv420p** indica chroma subsampling 4:2:0 — metade da resolução de cor.
  `rgb24`, `yuv444p` ou `gbrp` preservam mais.
- `bit_rate` baixo para a resolução indica compressão agressiva. Compare com o vídeo bruto
  equivalente (largura × altura × fps × 3 bytes) para ter noção do fator de compressão.
- `r_frame_rate` diferente de `avg_frame_rate` sugere fps variável.
- Diferenças irregulares entre timestamps consecutivos indicam jitter: quantifique
  (desvio-padrão do intervalo) antes de qualquer FFT.

Extração de quadros sem recompressão, quando for necessário processar fora:

```bash
ffmpeg -i entrada.mp4 -pix_fmt rgb24 -f image2 quadros/%06d.png   # sem perda, ocupa muito
```

Nunca reprocesse com codec com perda um vídeo do qual se vai extrair sinal sutil.

## 3. Diagnóstico de sinal ruim, na ordem certa

1. **Assista à ROI recortada** como vídeo. Caixa tremendo, recorte cortando a face, ROI
   pegando cabelo ou fundo — tudo isso é visível a olho nu e explica a maioria dos casos.
2. **Plote a média por canal ao longo do tempo.** Degraus indicam ganho ou exposição
   automáticos agindo. Deriva lenta indica mudança de iluminação ou de posição.
3. **Plote o espectro.** Um pico em 50/60 Hz rebatido, ou em harmônicos do fps, indica
   flicker ou artefato de amostragem, não fisiologia.
4. **Cheque ordem de canal e escala.** BGR × RGB, 0–255 × 0–1.
5. **Cheque o fps efetivo** e reamostre para grade uniforme.
6. **Cheque a sincronização** com a referência por correlação cruzada; corrija o atraso
   antes de calcular erro.
7. **Rode o método clássico** (POS) no mesmo dado. Funciona? Então o dado presta e o
   problema está no modelo. Não funciona? O problema é o dado ou a captura.

## 4. Condições de uso declaradas

O sistema só deve responder dentro das condições em que foi validado. Escreva-as
explicitamente, com números, por exemplo:

- distância entre X e Y cm, face ocupando ao menos N pixels de altura;
- iluminação frontal acima de L lux, sem contraluz direto;
- movimento limitado (sujeito sentado, fala permitida ou não — declare);
- fps efetivo mínimo, sem quedas maiores que um limite na janela;
- sem óculos escuros, sem maquiagem oclusiva na ROI (se for o caso, valide e declare).

Fora dessas condições, o comportamento correto é **recusar a medição**, não estimar assim
mesmo. A lista de condições e a taxa de recusa correspondente fazem parte da entrega, do
model card e da conversa com a área clínica.

## 5. Cenário de campo × cenário de laboratório

Datasets públicos foram gravados em laboratório: iluminação controlada, sujeito sentado,
câmera fixa, distância conhecida. Instalação real (totem, smartphone, consultório) tem
compressão de streaming, luz mista, movimento e distância variável.

Portanto: um resultado obtido só em dataset público **não é evidência de que funciona em
campo**. Planeje, desde o começo, uma coleta piloto no ambiente real — mesmo pequena, mesmo
com poucos sujeitos — e compare as duas condições lado a lado. É essa comparação, não o
número do dataset, que sustenta uma decisão de produto.
