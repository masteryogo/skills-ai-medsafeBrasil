# Avaliação e codificação

## O conjunto ouro

- **20-40 documentos reais**, anotados campo a campo, é suficiente para começar e caro o
  bastante para não crescer sem motivo. Cresça-o com todo caso que der problema em produção.
- **Anotado ou validado por um profissional de saúde.** Anotação feita só por engenheiro
  produz um teste que mede se o modelo concorda com o engenheiro. Onde houver dúvida de
  definição de campo, a resposta vem do clínico e vira regra escrita no guia de anotação.
- **Meça concordância entre anotadores** em um subconjunto compartilhado antes de anotar tudo.
  Se dois profissionais discordam em 20% dos campos, esse é o teto real da métrica e o que
  precisa de conserto é a **definição do campo**, não o prompt.
- **Cubra as armadilhas de propósito:** achados negados, hipótese diagnóstica, história
  familiar, frase de orientação no fim da evolução, abreviação ambígua, dose com vírgula
  decimal, campo genuinamente ausente, documento quase vazio, documento longo com duas
  consultas juntas.
- **Versione no repositório** e revise mudanças em PR. Um conjunto ouro que muda sem registro
  destrói a comparabilidade histórica de todas as medições anteriores.

## Métrica

**Nunca um número único.** A tabela mínima é por campo:

| Campo | Acerto exato | Falso positivo | Omissão | Crítico |
|---|---|---|---|---|
| principio_ativo | 100% | 0 | 0 | sim |
| dose_valor + unidade | 93% | 0 | 3 | sim |
| via | 100% | 0 | 0 | sim |
| intervalo_horas | 90% | 2 | 2 | sim |
| alergias | 96% | 0 | 1 | sim |
| sintomas (status correto) | 88% | 4 | 3 | não |
| HD | 85% | 3 | 2 | não |

Regras de leitura:

- **Compare após normalização**, nunca por string bruta: `0,5 mg` e `500 mcg` são o mesmo
  valor; `6/6h` e `de 6 em 6 horas` são o mesmo intervalo; `HAS` e `hipertensão arterial
  sistêmica` são o mesmo termo. Um comparador ingênuo reporta erro onde não há, e você vai
  otimizar o comparador em vez do sistema.
- **Separe falso positivo de omissão.** São consequências clínicas diferentes: um campo
  inventado engana o revisor, um campo ausente ele nota. Reporte os dois, sempre.
- **Campos críticos em bloco próprio** — princípio ativo, dose, unidade, via, frequência,
  alergia, e o status de negação. Meta diferente e mais dura: zero invenção, e recall alto
  aceitando revisão. Um índice geral bonito com um erro de dose é uma reprovação.
- **Conte, não só percentual.** Em 40 documentos, 93% são 3 erros. Diferença de poucos pontos
  é ruído; leia os erros em vez do placar.
- **Reporte a taxa de invenção separadamente**: quantos medicamentos, diagnósticos ou valores
  apareceram na saída sem existir no texto de origem. Essa métrica precisa ser zero, e é a
  única com esse status.

## Taxonomia de erro

Classifique cada falha para saber o que consertar. As categorias reais em texto clínico
brasileiro:

1. Negação invertida ou escopo de negação errado
2. Hipótese tratada como diagnóstico confirmado
3. Sujeito errado (familiar atribuído ao paciente)
4. Temporalidade errada (pregresso ou hipotético como atual)
5. Abreviação desambiguada errado
6. Número mal normalizado (vírgula, milhar, unidade)
7. Unidade omitida ou convertida indevidamente
8. Campo inventado (não existe no texto)
9. Campo omitido (existe no texto e não foi extraído)
10. Erro herdado da transcrição de áudio
11. Falha de schema (JSON inválido, enum fora do domínio)

Conte por categoria e ataque a maior. As categorias 1 a 4 quase sempre se resolvem no schema
e na extração por seção; 5 a 7 no glossário e na normalização em código; 8 no `null`
explícito; 10 no fluxo de confirmação da transcrição. Ordenar assim evita mexer no prompt
quando o problema é de arquitetura.

## Codificação e terminologias brasileiras

Quando o destino exige código e não texto livre, mapeie — mas **guarde sempre o trecho
original junto do código**. Perder o texto de origem impede auditoria e torna o mapeamento
irreversível.

- **CID-10** — padrão oficial no Brasil para diagnóstico (DATASUS, faturamento, notificação).
  É o mapeamento mais pedido. Cuidado: CID é classificação estatística com granularidade
  grossa; muita coisa dita em consulta não tem código exato, e forçar um código próximo
  distorce o dado. Prefira sinalizar `sem_codigo_exato` a escolher o vizinho.
- **SNOMED CT** — muito mais expressivo para achado clínico e para uso interno. O Brasil
  ingressou no SNOMED International; confirme o estado atual do licenciamento nacional antes
  de depender dele num produto contratado.
- **LOINC** — para exames laboratoriais e observações. É o padrão certo para "qual exame é
  este", e mapear resultado de laboratório sem LOINC gera retrabalho depois.
- **DCB (Denominação Comum Brasileira)** da ANVISA — nomes de princípios ativos no Brasil;
  a `DCI/INN` é a referência internacional equivalente. Normalize nome comercial para
  princípio ativo pela DCB, e mantenha os dois campos.
- **TUSS** (ANS, saúde suplementar) e **SIGTAP** (SUS) — procedimentos. Qual usar depende de
  quem paga; sistemas que atendem os dois precisam dos dois.
- **RNDS** — a Rede Nacional de Dados em Saúde usa **FHIR**. Se há intenção de
  interoperar com o Ministério da Saúde, modele os recursos em FHIR desde o começo em vez de
  converter um schema próprio depois.

Como implementar o mapeamento: **não peça o código ao modelo de memória.** Ele produz códigos
com formato correto e significado errado, o que é a pior combinação possível. Faça o modelo
extrair o termo, e o código sair de uma busca (léxica mais vetorial) sobre a tabela oficial
carregada no seu banco, com revisão humana quando a similaridade for baixa. Reporte a
acurácia do mapeamento como métrica própria, separada da extração.

## Do offline para produção

- **Amostre e revise saídas reais continuamente** — algumas por dia, lidas por um clínico.
  Métrica não detecta que o sistema começou a escrever em tom impróprio, ou que passou a
  omitir uma seção depois de uma mudança no formato de entrada.
- **Registre a taxa de correção do revisor por campo.** É a melhor métrica de produção que
  existe aqui: quais campos o profissional mais conserta indica exatamente onde investir, e
  não depende de conjunto ouro nenhum.
- **Alerte quando a taxa de `nao_informado` mudar** de patamar. Uma queda súbita significa
  que o modelo passou a preencher o que não sabe; uma alta súbita significa que a entrada
  mudou (formato novo, transcrição pior, integração quebrada).
- **Mantenha o conjunto ouro alinhado com a produção**: sempre que uma revisão real corrigir
  algo interessante, esse documento entra no conjunto. É assim que o teste continua medindo o
  produto e não a versão dele de seis meses atrás.
