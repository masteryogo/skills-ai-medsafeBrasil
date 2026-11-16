# Checklist de experimento

Referência de apoio da skill `machine-learning-engineer`. Use ao montar ou revisar um
pipeline de treino.

## Antes de rodar

- [ ] Pergunta do experimento escrita em uma frase, com o critério de sucesso.
- [ ] Teste separado e congelado; ninguém olhou.
- [ ] Split agrupado pela unidade correta (sujeito/paciente/instituição); verificado por
      código, não por confiança — asserte que a interseção de identificadores entre splits
      é vazia.
- [ ] Pré-processamento ajustado apenas no treino, dentro do fold.
- [ ] Baselines trivial e clássico já medidos no mesmo split.
- [ ] Seed fixa; config serializada junto com o run.
- [ ] Estimativa de custo (tempo, GPU, disco) feita e aceitável.
- [ ] Um teste rápido com 1 % do dado roda ponta a ponta antes do treino completo.

## Overfitting deliberado como teste de sanidade

Antes do treino de verdade, treine em **um lote pequeno (8–32 amostras) sem regularização
até o erro ir a quase zero**. Se não conseguir, há bug no dado, na perda ou no modelo —
nenhum ajuste de hiperparâmetro vai salvar. É o teste mais barato e o mais ignorado.

## Hiperparâmetros

- Ordem de importância prática: taxa de aprendizado > tamanho de lote e schedule >
  regularização (weight decay, dropout) > arquitetura.
- Busca aleatória vence busca em grade com o mesmo orçamento. Busca bayesiana só compensa
  quando cada run é caro e o espaço é grande.
- Toda a busca acontece na **validação**. O teste entra uma vez, no fim, com a config vencedora.
- Registre a faixa buscada, não só o valor escolhido: valor ótimo na borda da faixa
  significa que a faixa estava errada.

## Desbalanceamento

- Primeiro tente ajustar o **limiar de decisão** e a métrica; muitas vezes basta.
- Depois, pesos na função de perda.
- Reamostragem (oversampling da minoritária) apenas no treino, nunca na validação nem no
  teste — do contrário a métrica deixa de refletir a prevalência real.
- Sintetização (SMOTE e afins) raramente ajuda em imagem/vídeo e pode vazar quando aplicada
  antes do split.

## Aumento de dado (data augmentation)

- Só aumente com transformações que ocorrem no mundo real da aplicação. Aumento que quebra
  o sinal destrói o rótulo — em vídeo de rPPG, por exemplo, mudar contraste ou fazer
  reamostragem temporal altera exatamente a informação que o modelo deve ler.
- Valide o aumento visualmente em algumas amostras antes de rodar o treino inteiro.
- Aumento é aplicado no treino. Test-time augmentation é decisão separada e precisa ser
  declarada, porque muda o custo de inferência.

## Transfer learning e fine-tuning

- Comece congelando o backbone e treinando só a cabeça; depois descongele por blocos com
  taxa de aprendizado menor.
- Pré-treino em domínio próximo vale mais que pré-treino grande em domínio distante.
- Ao usar peso público, verifique a licença do peso **e** a do dado com que foi treinado —
  a restrição costuma acompanhar o modelo derivado.

## Reprodutibilidade

- Um comando reproduz o run: `python train.py --config configs/<exp>.yaml`.
- Config em arquivo versionado, nunca em argumento solto de linha de comando não registrado.
- Ambiente fixado (lockfile ou imagem). Versão de CUDA e de biblioteca entram no registro
  do run.
- Dado versionado por hash ou por manifesto de arquivos, com contagem de amostras.
- Artefatos do run em diretório próprio: config, log, métricas, checkpoints, gráficos.

## Depois de rodar

- [ ] Curvas de treino e validação inspecionadas (divergência, platô, instabilidade).
- [ ] Piores casos olhados um a um — pelo menos 10 amostras. É onde o bug aparece.
- [ ] Métrica estratificada calculada e registrada.
- [ ] Comparação com os baselines na mesma tabela.
- [ ] Resultado registrado mesmo quando negativo: experimento que falhou evita repetição.
