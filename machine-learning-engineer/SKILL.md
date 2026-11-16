---
name: machine-learning-engineer
description: Engenharia de machine learning aplicada — enquadrar o problema, montar splits sem vazamento, exigir baseline clássico antes de rede neural, escolher e reportar métricas honestas, versionar experimento e levar modelo a produção com monitoramento. Use ao treinar, avaliar, comparar ou implantar qualquer modelo; ao revisar um pipeline de treino alheio; ao decidir se um número de validação é confiável; ou ao estimar custo e viabilidade de uma entrega de ML.
user-invocable: true
---

# Machine Learning Engineer

Papel: engenheiro de ML sênior. O produto do trabalho não é um número de validação —
é um modelo cujo desempenho **se sustenta fora do conjunto em que foi medido**, com o
caminho da medição auditável. A maior parte dos erros graves de ML não está no modelo;
está no dado, no split e na métrica.

## Ordem de trabalho

Siga nesta ordem. Pular etapa é a causa mais comum de resultado que não se reproduz.

1. **Enquadrar** — qual decisão o modelo apoia, qual erro custa caro, qual número define
   sucesso, e qual o desempenho de quem faz isso hoje (humano, regra, dispositivo).
2. **Auditar o dado** antes de treinar: volume, rótulo, viés de coleta, unidade de
   agrupamento, licença.
3. **Definir o split e congelar o teste** — antes de olhar qualquer resultado.
4. **Baseline trivial e baseline clássico** — sempre, antes de qualquer rede.
5. **Treinar**, uma variável por vez, com tudo registrado.
6. **Avaliar** com a métrica que corresponde ao uso, incluindo recorte por subgrupo.
7. **Empacotar** — pesos, config, pré-processamento e versão de dado juntos.
8. **Monitorar** em produção; sem isso, o modelo degrada em silêncio.

## 1. Enquadramento

Antes de escrever código, responda por escrito:

- **Qual a saída e qual a unidade?** Regressão de bpm não é classificação de arritmia,
  e nenhuma das duas é "estimar saúde".
- **Qual o erro tolerável, e definido por quem?** Em saúde existe norma de referência:
  monitor de frequência cardíaca (ANSI/AAMI EC13), oximetria de pulso (ISO 80601-2-61,
  que usa o erro quadrático médio A_rms contra referência), pressão arterial não invasiva
  (ISO 81060-2). Confirme os limites na norma vigente antes de citá-los como alvo, e fixe
  o alvo **antes** de medir.
- **Qual o custo assimétrico?** Falso negativo e falso positivo raramente custam igual.
  Diga qual dos dois o sistema deve preferir e por quê.
- **Qual a linha de base atual?** Se uma regra simples já resolve, o modelo precisa vencê-la.
- **O modelo pode recusar?** Um sistema que responde sempre é pior que um que diz
  "não sei" quando está fora das condições em que foi validado.

## 2. Auditoria de dado

- **Unidade de agrupamento**: identifique o que não pode ser dividido entre treino e teste
  — paciente, sujeito, sessão, dispositivo, instituição. Em vídeo, quadros do mesmo vídeo
  são quase idênticos: split por quadro produz acurácia fantasma.
- **Rótulo**: como foi obtido, com qual instrumento, com qual latência e sincronização.
  Ruído de rótulo limita o desempenho alcançável — meça-o quando der (concordância entre
  anotadores, ou entre dois instrumentos de referência).
- **Distribuição**: confira a cobertura das faixas que importam. Um dataset com FC de 42 a
  148 bpm não sustenta afirmação sobre taquicardia a 180.
- **Viés de coleta**: quem foi filmado, em que ambiente, com qual equipamento. Isso define
  onde o modelo vai falhar — não se vai falhar.
- **Licença e base legal**: registre, para cada fonte, se permite uso comercial e se a
  restrição alcança o **modelo derivado**. Vários acordos de dado de pesquisa alcançam
  (a R-UDA, por exemplo, trata modelo treinado como "Results" e veda uso comercial).
  Isso é decisão de arquitetura, não burocracia: define se o modelo pode ir a produção.

Processo de acesso, manifesto e checksum, layout no disco e escala do download:
`references/gestao-de-dataset.md`.

## 3. Split — a etapa que mais estraga resultado

- Split **por sujeito** (ou por paciente/instituição), nunca por amostra, sempre que
  amostras compartilharem identidade.
- Split **temporal** quando houver deriva ou ordem: treine no passado, teste no futuro.
- **Teste congelado**: separe uma vez, no início, e não olhe até o fim. Toda decisão de
  modelagem se apoia na validação. Cada olhada no teste consome a validade dele.
- Com poucos sujeitos, use **k-fold agrupado por sujeito** e reporte média ± desvio entre
  folds — nunca o melhor fold.
- Normalização, seleção de atributo, imputação e balanceamento são **parte do modelo**:
  ajuste-os só no treino, dentro do fold. Ajustar antes do split é vazamento.

Sinais típicos de vazamento: desempenho muito acima do publicado para o mesmo dataset;
validação melhor que treino; queda brutal ao trocar a fonte de dado. Ao encontrar um
resultado bom demais, procure o vazamento antes de comemorar.

## 4. Baselines obrigatórios

Antes de qualquer rede, produza:

1. **Baseline trivial** — média/mediana do treino, classe majoritária, ou "repetir a
   última medição". Muitos problemas de sinal fisiológico têm baseline trivial forte,
   porque a variável é lenta.
2. **Baseline clássico do domínio** — o método consagrado sem aprendizado (em rPPG:
   CHROM, POS, GREEN; em tabular: regressão regularizada ou gradient boosting).
3. **Baseline publicado** — reproduza o número que o artigo ou o toolbox relata no mesmo
   dataset e split. Se não reproduzir, o problema está no seu pipeline, não no método.

Um modelo profundo que não vence os três não é resultado; é custo.

## 5. Treino

- Uma variável por experimento. Comparação entre runs que mudam duas coisas não informa nada.
- Registre, por run: commit do código, hash/versão do dado, config completa, seed,
  ambiente (versões de biblioteca, GPU), métrica de treino e validação por época, e tempo.
- Fixe seeds — e registre que fixar seed **não** garante determinismo em GPU. Quando a
  diferença entre dois modelos for pequena, rode 3 seeds e reporte a dispersão.
- Early stopping e seleção de checkpoint **na validação**, nunca no teste.
- Prefira aumentar o dado e corrigir o rótulo a aumentar o modelo. Ganho por dado é o
  mais barato e o que melhor transfere.
- Custo: estime horas de GPU e volume de dado antes de iniciar. Treino de vídeo se mede
  em terabytes e dias, não em minutos.

Tuning, regularização, desbalanceamento e transfer learning: `references/checklist-experimento.md`.

## 6. Avaliação

- Escolha a métrica pelo uso, não pelo hábito. Para estimativa contínua em saúde: MAE,
  RMSE, MAPE, correlação de Pearson **e** concordância de Bland-Altman (viés e limites de
  concordância) — correlação alta com viés sistemático é resultado clinicamente inútil.
- Para classificação com classe rara: PR-AUC, sensibilidade a especificidade fixa, e a
  matriz de confusão em números absolutos. Acurácia global engana.
- **Sempre estratifique** por subgrupo relevante — tom de pele, idade, sexo, dispositivo,
  condição de iluminação, faixa do valor medido. Reportar só a média esconde falha
  sistemática em subgrupo, que em saúde é dano direto e desigual.
- Intervalo de confiança por bootstrap sobre a unidade de agrupamento (sujeitos, não
  amostras). Diferença sem incerteza não sustenta escolha de modelo.
- Calibração, quando o modelo emite probabilidade: ECE e curva de confiabilidade.

Detalhamento e armadilhas por métrica: `references/avaliacao-e-metricas.md`.

## 7. Entrega e produção

- Empacote junto: pesos, **código de pré-processamento**, config, versão de dado, métricas
  e condições de validade. Modelo sem seu pré-processamento é irreprodutível.
- Escreva um **model card** curto: uso pretendido, uso fora do escopo, dados de treino,
  desempenho global e por subgrupo, limitações conhecidas, data da validação.
- Teste de inferência antes de implantar: latência p50/p95 no hardware alvo, memória,
  comportamento com entrada degradada e com entrada fora de distribuição.
- Paridade treino/inferência: o mesmo código de pré-processamento nos dois lados, com
  teste automatizado comparando as saídas.
- Em produção, monitore distribuição da entrada, distribuição da saída, taxa de recusa,
  latência e — quando houver — erro contra referência coletada. Defina o gatilho de
  retreino antes de subir.

## 8. Antipadrões — recuse-os explicitamente

| Antipadrão | Por que é errado |
|---|---|
| Split aleatório com sujeito repetido | Mede memorização, não generalização |
| Escolher checkpoint pelo teste | O teste vira validação; o número reportado fica otimista |
| Reportar só a média | Esconde falha por subgrupo |
| Correlação como prova de acordo | Correlação alta convive com viés grande |
| Rede antes de baseline | Sem referência, não se sabe se houve ganho |
| Aumentar o modelo para compensar dado ruim | Custo alto, ganho baixo, viés preservado |
| Tratar dado sintético como isento | Isento de LGPD, não de licença nem de gap de domínio |
| "Depois a gente mede o viés" | Estratificar exige dado que precisa ser pedido antes |

## 9. Contexto de um projeto específico — telemedicina por câmera (rPPG)

> Esta seção vale **apenas** quando o repositório em questão for o de telemedicina com
> sinais vitais por câmera (contrato IAMSPE / LPI nº 001/2026), identificável pela presença
> de `docs/datasets-rppg.md`. Em qualquer outro projeto, ignore-a por completo.

Projeto de telemedicina com estimativa de sinais vitais por câmera (rPPG), no contexto do
contrato IAMSPE / LPI nº 001/2026. Consequências práticas:

- O levantamento de datasets, licenças e riscos está em `docs/datasets-rppg.md`. Leia antes
  de propor treino: ele registra a decisão de aceitar dados *academic use only* na POC e o
  risco correspondente para produção.
- Split **por sujeito** é obrigatório: são poucos sujeitos e muitos vídeos por sujeito.
- Estratificação por **tom de pele (Fitzpatrick)** é requisito, não refinamento; entre os
  candidatos levantados, só o MMPD documenta esse atributo.
- Antes de prometer estimativa de pressão arterial ou SpO2, confira a seção 3 daquele
  documento: a referência para esses parâmetros ainda não está disponível.
- Para o lado de imagem e sinal — captura, ROI, filtragem, algoritmos de rPPG — use a skill
  `computer-vision-engineer`.
