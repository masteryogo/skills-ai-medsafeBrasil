# Gestão de dataset

Este arquivo cobre a camada operacional: obter o dado, provar que é o que se espera,
organizá-lo no disco e mantê-lo reproduzível. A decisão de **qual** dataset usar, com quais
critérios e sob qual licença, está em `docs/datasets-rppg.md`; a auditoria de conteúdo
(agrupamento, rótulo, viés, base legal) está na seção 2 da skill; a verificação técnica do
vídeo em si está em `computer-vision-engineer/references/captura-e-video.md`. Não repita nada
disso aqui — este arquivo é o que fica de fora dos três.

## 1. Processo de acesso — trate como dependência de terceiro

O custo de um dataset com acesso controlado é latência, não esforço. Registre o processo no
repositório como se fosse uma dependência externa com prazo, porque é:

| Campo | Por que |
|---|---|
| Forma de acesso | download direto, formulário, EULA assinada, e-mail institucional |
| Quem assina | se exige assinatura institucional, o prazo depende de terceiro interno |
| Data do pedido e data da liberação | mede a latência real, informa o planejamento do próximo |
| Cópia do termo aceito | o arquivo, versionado. Termo aceito e não guardado não existe |
| Correspondência de autorização | quando a licença é ausente ou ambígua, o e-mail do autor **é** a autorização. Arquive o e-mail completo, com cabeçalhos |
| Versão do termo | licenças e condições mudam; guarde a data em que a página foi lida |

Peça acesso a **todos** os candidatos plausíveis de uma vez, no começo, mesmo aos que
provavelmente não serão usados. A espera roda em paralelo; a decisão de usar ou não vem
depois e custa nada.

## 2. Snapshot e manifesto

Nenhum resultado é reproduzível sem saber exatamente qual dado entrou. Todo dataset baixado
recebe um manifesto versionado em git (o dado, não):

```yaml
dataset: UBFC-Phys
origem: IEEE DataPort — 10.21227/5da0-7344
baixado_em: 2026-08-31
sujeitos_locais: [s1]
sujeitos_totais: 56
tamanho_local_bytes: 14871534656
arquivos:
  - caminho: s1/vid_s1_T1.avi
    sha256: ...
    bytes: 4954673952
docs_de_referencia:
  - READ_ME (baixado separado da página do DataPort, em 2026-08-31)
observacoes:
  - fps medido 35.138 (17569/500), não 35 exatos
  - BVP 64 Hz, EDA 4 Hz
  - info_s1.txt traz campo de grupo (valor "test")
```

Regras:

- **Checksum de tudo** na chegada, e reverificação antes de um treino que vá para relatório.
  Download truncado de arquivo de 5 GB acontece e não avisa.
- **Não versione o dado em git.** Vídeo vai para `.gitignore`; o manifesto e os derivados
  pequenos vão para o repositório.
- **Registre a versão dos documentos auxiliares.** No UBFC-Phys, o `READ_ME` não vem junto
  dos arquivos de sujeito e é o que define a semântica de `info_s<N>.txt` e de
  `selfReportedAnx_s<N>.csv`. Um dataset cuja semântica de coluna você não tem por escrito
  não está pronto para uso.
- **Um snapshot é imutável.** Se chegar mais dado, é um snapshot novo com data nova, e todo
  resultado cita qual usou. Nunca acrescente sujeitos a um snapshot já medido.

## 3. Layout no disco

Separe três camadas, com permissões e políticas diferentes:

```
datasets/
  raw/ubfc-phys/2026-08-31/     # imutável, somente leitura, nunca editado
    s1/...
  interim/ubfc-phys/            # cache regenerável (quadros, ROI, sinal bruto)
  processed/ubfc-phys/          # entrada de treino, pequena, versionável
    signals/s1_T1.parquet
```

- **`raw` é somente leitura.** Marque como tal no sistema de arquivos. Toda correção de
  layout acontece no carregador ou numa etapa explícita para `interim`, nunca editando o
  original — do contrário o checksum do manifesto deixa de valer.
- **Normalize a esquisitice do layout no carregador**, não no disco. O UBFC-Phys entrega a
  pasta aninhada como `s<N>/s<N>/`; resolver isso no `Dataset` mantém o `raw` intacto e o
  código honesto sobre o que a fonte realmente é.
- **`interim` e `processed` são cache, não dado.** Devem ser regeneráveis por um comando, a
  partir de `raw` mais um script determinístico. Se não são, viraram dado sem manifesto.
- **Nomeie o derivado com o hash da configuração** que o produziu (`roi=face_center,
  fps=35.138, banda=0.7-4.0` → `a3f1c9`). Sem isso você não sabe se o `.parquet` no disco
  corresponde ao pipeline atual, e vai comparar modelos sobre entradas diferentes sem
  perceber.

## 4. Escala — decida antes de baixar

Números reais do UBFC-Phys: ~4,7 GB por vídeo, 3 vídeos por sujeito, ~19 GB por sujeito,
**~1 TB para os 56**. Consequências:

- **Baixe um sujeito primeiro** e rode o pipeline inteiro nele, ponta a ponta, antes de pedir
  o resto. Um sujeito revela codec, fps real, taxa de amostragem da referência, layout de
  pasta e semântica de coluna — tudo que muda o pipeline. Baixar 1 TB antes disso é apostar
  um dia de banda numa suposição.
- **O derivado é minúsculo.** O sinal extraído de 180 s a 35 fps são alguns milhares de
  amostras: kilobytes contra gigabytes. Depois que a extração está estável, o experimento de
  modelagem roda sobre `processed` e não precisa do vídeo montado. Planeje o pipeline para
  que reprocessar vídeo seja raro e explícito, não parte de cada iteração.
- **Extraia uma vez, use muitas.** Reprocessar vídeo a cada experimento é o desperdício mais
  comum aqui, e o mais fácil de evitar com cache versionado por hash de config.
- **Vídeo pode ficar em armazenamento frio** depois da extração, desde que o manifesto e o
  caminho de recuperação estejam registrados. Precisará dele de novo quando a definição de
  ROI ou de filtro mudar — o que vai acontecer.

## 5. Ficha do dataset

Uma ficha por fonte, no repositório, com o mínimo para alguém decidir sem reabrir a
investigação: origem e DOI, licença e o que ela alcança, número de sujeitos e duração,
parâmetros de vídeo medidos (codec, resolução, fps efetivo), instrumento e taxa da
referência, atributos de estratificação disponíveis (tom de pele, iluminação, movimento) e
**os que não existem**, e para que este dataset serve — treino, avaliação, ou só
desenvolvimento de pipeline.

O último campo é o que mais se perde. Um dataset serve para avaliação mas não para treino
(poucos sujeitos), ou para desenvolver o pipeline mas não para reportar número (referência de
punho em vez de dedo, como no UBFC-Phys). Escrever isso na ficha evita que a limitação seja
redescoberta depois de um resultado já ter sido apresentado.

## 6. Antipadrões

| Antipadrão | Por que é errado |
|---|---|
| Baixar o dataset inteiro antes de validar o pipeline num sujeito | Aposta banda e dias numa suposição sobre codec, fps e layout |
| Corrigir layout ou renomear dentro de `raw` | Invalida o checksum e apaga a diferença entre o que a fonte deu e o que você fez |
| Derivado no disco sem hash da config que o gerou | Compara modelos sobre entradas diferentes sem perceber |
| Acrescentar sujeitos a um snapshot já medido | Torna os resultados anteriores incomparáveis, em silêncio |
| Guardar a licença "no navegador" | Termo aceito e não arquivado não é prova de nada numa entrega contratada |
| Usar dataset cujo `READ_ME` você não tem | A semântica das colunas passa a ser suposição |
| Vídeo no git ou no repositório de artefatos | Estoura o limite e não resolve versionamento de binário grande |
