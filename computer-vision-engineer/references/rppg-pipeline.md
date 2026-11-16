# Pipeline de rPPG

Referência de apoio da skill `computer-vision-engineer`. Leia antes de implementar,
avaliar ou revisar extração de sinais vitais por câmera.

## 1. O princípio físico, e o que ele impõe

A hemoglobina absorve luz de forma dependente do volume de sangue no leito capilar da pele.
A cada batimento, a intensidade refletida pela pele varia — na ordem de **1 %** ou menos, e
de forma desigual entre canais: o verde carrega o sinal mais forte (absorção da hemoglobina
próxima do pico de sensibilidade), o vermelho e o azul carregam principalmente o ruído de
iluminação e movimento. Toda a família de métodos clássicos explora essa diferença entre
canais para cancelar o que é comum a eles (variação de luz) e preservar o que não é (pulso).

Consequências que não se negociam:

- **Compressão com perda é adversária direta do sinal.** O codec descarta variação sutil
  por ser perceptualmente irrelevante — que é a definição do sinal aqui. Chroma subsampling
  4:2:0 remove metade da informação de cor.
- **Controle automático de câmera injeta artefato.** Exposição e ganho automáticos reagem à
  cena e criam variação de intensidade correlacionada com movimento.
- **Movimento e iluminação dominam a variância.** O pré-processamento existe quase inteiro
  para separar 1 % de sinal de variações muito maiores.
- **Tom de pele altera a amplitude.** Mais melanina absorve mais luz antes de alcançar o
  leito capilar; o sinal chega mais fraco. Avaliação sem estratificação por Fitzpatrick não
  detecta essa falha.

## 2. Pipeline de referência

```
vídeo
 └─ detecção de face (periódica) + rastreio entre detecções
     └─ ROI: máscara de pele (testa e bochechas), excluindo olhos, boca, cabelo, óculos
         └─ média espacial por canal, por quadro  →  3 séries temporais RGB
             └─ interpolação para grade temporal uniforme (se fps instável)
                 └─ detrend + normalização temporal por janela
                     └─ método de extração (clássico ou rede)  →  sinal BVP
                         └─ passa-banda 0,7–4 Hz, fase zero
                             └─ estimativa: pico do espectro (PSD) ou detecção de picos
                                 └─ métricas de qualidade → aceitar ou recusar
```

Cada seta é um ponto de inspeção. Ao depurar, salve a saída intermediária de cada uma.

## 3. Métodos clássicos — o baseline obrigatório

| Método | Ideia | Quando usar |
|---|---|---|
| **GREEN** | Usa só o canal verde | Piso absoluto; útil para saber quanto os outros ganham |
| **ICA / PCA** | Separação cega de fontes sobre os 3 canais | Referência histórica; ordem das componentes é ambígua |
| **CHROM** | Combinação linear de canais cromáticos, com suposição de pele padronizada, para cancelar movimento | Robusto, barato, forte com movimento moderado |
| **POS** (Plane-Orthogonal-to-Skin) | Projeta num plano ortogonal ao tom de pele no espaço RGB temporalmente normalizado | Costuma ser o melhor dos clássicos; **é o baseline a bater** |

Regra da skill `machine-learning-engineer`: nenhum modelo profundo é resultado antes de
vencer POS e CHROM no mesmo split. Os clássicos não precisam de treino, então também servem
de teste de sanidade do dado: se POS não produz nada num vídeo limpo, o problema está na
captura ou no pré-processamento, não no método.

## 4. Modelos profundos

| Modelo | Entrada | Nota |
|---|---|---|
| **DeepPhys** | Quadro + quadro de diferença normalizada, com atenção | Introduziu o ramo de movimento/aparência |
| **PhysNet** | Sequência 3D-CNN, saída de onda | Bom com sequências curtas; simples de treinar |
| **TS-CAN** | Dois ramos temporais com atenção, eficiente | Referência prática para tempo real |
| **EfficientPhys** | Simplifica o pré-processamento e reduz custo | Voltado a dispositivo |
| Baseados em transformer (PhysFormer e derivados) | Atenção temporal longa | Exigem mais dado; ganho não é garantido em cross-dataset |

Todos são sensíveis a **domínio**: acurácia alta no dataset de origem e queda forte em
outro dataset é o comportamento esperado, não a exceção. Por isso a avaliação padrão da
área é **cross-dataset** (treina em A, testa em B), e é ela que deve ser reportada.

## 5. rPPG-Toolbox

Implementação de referência aberta (código sob licença permissiva; os datasets, não) que já
traz os métodos clássicos, os modelos profundos acima e os *dataloaders* de UBFC-rPPG,
UBFC-Phys, PURE, COHFACE, SCAMPS, MMPD, iBVP e BP4D+. Use-o para:

1. reproduzir o número publicado antes de escrever pipeline próprio — é o baseline publicado
   exigido pela skill de ML;
2. garantir que o pré-processamento e o protocolo de avaliação sejam os mesmos da literatura,
   sem o que a comparação não vale;
3. só então divergir, documentando cada divergência.

Verifique a versão e o protocolo exato (janela, filtro, forma de estimar FC) antes de
comparar com qualquer número de artigo: variações nesses detalhes mudam o resultado mais
que a escolha de modelo.

## 6. Avaliação

- Métricas: MAE, RMSE, MAPE, Pearson e Bland-Altman sobre a FC estimada; opcionalmente
  SNR do sinal e correlação de forma de onda com a referência.
- Estimativa de FC por **PSD na banda 0,7–4 Hz** ou por detecção de picos — declare qual.
- Janela típica na literatura: 10 s ou 30 s, com passo de 1 s. Fixe e informe.
- Split **por sujeito**; avaliação **cross-dataset** como resultado principal quando o
  objetivo é uso real.
- Estratifique por Fitzpatrick, iluminação, movimento e distância.
- Reporte a taxa de recusa junto com o erro.

## 7. Além da frequência cardíaca

- **Frequência respiratória**: banda 0,1–0,5 Hz; extraível do mesmo sinal (modulação) ou do
  movimento do tórax/ombros. Mais fácil que HRV, mais difícil que FC.
- **SpO2 por câmera**: depende da razão de razões entre dois comprimentos de onda, e câmeras
  RGB comuns têm bandas largas e sobrepostas. Resultados existem em condição controlada;
  trate como pesquisa, não como capacidade pronta, e exija calibração contra oxímetro.
- **Pressão arterial por câmera**: normalmente inferida por tempo de trânsito de pulso ou por
  morfologia da onda; a literatura é otimista e a validação clínica (ISO 81060-2) é dura.
  Requer referência com onda de PA, que quase nenhum dataset público oferece.
- **Estresse**: rótulo mal definido. Exige que se declare o que é medido — HRV, EDA,
  autorrelato de ansiedade — porque não são a mesma coisa e não se validam entre si.
- **HRV**: exige detecção confiável de batimento individual, ordens de grandeza mais difícil
  que FC média. Não deduza HRV de uma FC boa.

## 8. Antipadrões de rPPG

| Antipadrão | Consequência |
|---|---|
| Avaliar em vídeo recomprimido | Mede o codec, não o método |
| ROI retangular incluindo cabelo, olhos e fundo | Dilui o sinal com pixels sem pele |
| Detectar face em todo quadro sem suavizar | Tremor da caixa vira frequência espúria |
| Média espacial sem máscara de pele | Ruído de fundo entra no sinal |
| Não travar exposição/ganho automáticos | Artefato correlacionado com movimento |
| Ignorar fps instável antes da FFT | Espectro deslocado e alargado |
| Reportar só o dataset de treino | Esconde a queda cross-dataset, que é a realidade de uso |
| Média sem estratificar por tom de pele | Esconde a falha mais previsível e mais grave do método |
| Sistema que sempre responde um número | Entrega valor inventado quando o sinal não existe |
