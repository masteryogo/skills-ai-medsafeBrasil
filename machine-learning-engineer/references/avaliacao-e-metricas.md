# Avaliação e métricas

Referência de apoio da skill `machine-learning-engineer`. Consulte ao escolher a métrica,
ao montar o relatório de resultado ou ao julgar um número que outra pessoa reportou.

## 1. Regressão de grandeza fisiológica (FC, SpO2, PA, frequência respiratória)

| Métrica | O que diz | Armadilha |
|---|---|---|
| MAE | Erro médio absoluto, na unidade da grandeza | Não distingue viés de dispersão |
| RMSE | Penaliza erro grande | Dominado por poucos outliers; reporte junto com MAE |
| MAPE | Erro relativo | Explode quando o valor verdadeiro é pequeno |
| Pearson r | Se sobe junto | **Não mede acordo**: r = 0,99 com viés de 15 bpm é possível |
| Bland-Altman | Viés (média das diferenças) e limites de concordância (± 1,96 DP) | É o que se cobra em validação clínica |
| A_rms | Erro quadrático médio contra referência, usado em oximetria (ISO 80601-2-61) | Só faz sentido na faixa especificada pela norma |

Regra: para grandeza clínica, **MAE + RMSE + viés e limites de Bland-Altman**, nesta ordem.
Correlação entra como complemento, nunca como resultado principal.

Reporte também:
- **erro por faixa do valor verdadeiro** (o erro em FC de repouso não prediz o erro em FC alta);
- **percentual de medições dentro da tolerância** (ex.: ±5 bpm), que é como o usuário clínico lê;
- **taxa de recusa** do sistema e o erro *entre as medições aceitas* — os dois juntos. Um
  modelo com MAE baixo que recusa 70 % dos casos não é melhor que outro com MAE um pouco
  maior que responde sempre; são produtos diferentes, e ambos os números precisam aparecer.

## 2. Avaliação de sinal periódico no domínio da frequência

Quando a saída é uma onda (PPG, respiração) e a grandeza é a frequência dominante:

- Estime a FC pela densidade espectral de potência na banda fisiológica (tipicamente
  0,7–4 Hz, isto é, 42–240 bpm) ou por detecção de picos no tempo. Diga qual usou: os
  números não são intercambiáveis.
- **SNR do sinal** (potência na frequência fundamental e no primeiro harmônico contra o
  resto da banda) mede a qualidade da extração, independentemente do erro de FC — útil
  para separar "extraiu mal" de "estimou mal a frequência".
- Comprimento da janela e passo mudam o resultado. Janela de 30 s produz erro menor que
  janela de 10 s e não serve à mesma aplicação. Fixe e declare os dois.
- Métricas de variabilidade (HRV: SDNN, RMSSD, LF/HF) exigem detecção de batimento
  individual confiável, ordens de grandeza mais difícil que FC média. Não prometa HRV
  porque a FC ficou boa.

## 3. Classificação

- Classe rara: **PR-AUC**, sensibilidade a especificidade fixa (ou vice-versa), matriz de
  confusão em contagem absoluta. ROC-AUC infla com desbalanceamento.
- Escolha o limiar pelo custo do erro, na validação, e reporte o limiar escolhido.
- Multi-classe: macro-F1 quando as classes importam igualmente; micro quando o volume
  importa. Diga qual.
- Calibração: ECE e curva de confiabilidade. Modelo descalibrado com AUC boa induz decisão
  errada quando a probabilidade é mostrada a alguém.

## 4. Incerteza e comparação entre modelos

- Bootstrap **sobre a unidade de agrupamento** (reamostre sujeitos, não amostras): 1.000
  reamostragens, reporte intervalo de 95 %.
- Comparação pareada entre dois modelos no mesmo conjunto: teste de Wilcoxon pareado sobre
  o erro por sujeito, ou intervalo bootstrap da diferença. Comparar duas médias soltas não
  responde à pergunta.
- Com 10 sujeitos de teste, quase nenhuma diferença é estatisticamente distinguível. Diga
  isso em vez de declarar vencedor.

## 5. Estratificação — obrigatória

Reporte a mesma métrica principal por:

- tom de pele (Fitzpatrick I–VI, ou agrupado I–III / IV–VI quando o n for pequeno);
- sexo e faixa etária;
- condição de iluminação e de movimento;
- dispositivo/câmera;
- faixa do valor verdadeiro.

Mostre o **n de cada célula**. Célula com 3 sujeitos não sustenta conclusão, mas a ausência
dela também é informação — significa que o sistema não foi validado ali, e isso pertence às
limitações do model card.

## 6. Relatório mínimo de um experimento

1. Pergunta e hipótese em uma frase.
2. Dado: fonte, versão, n de sujeitos e de amostras por split.
3. Split: critério de agrupamento, folds, o que foi congelado.
4. Modelos comparados, incluindo os baselines.
5. Métrica principal com intervalo de confiança + tabela estratificada.
6. Gráficos: Bland-Altman, dispersão predito × verdadeiro, distribuição do erro.
7. O que **não** foi testado, e por quê.
8. Comando e commit exatos para reproduzir.
