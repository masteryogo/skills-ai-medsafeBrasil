# Revisão de código: classes de vulnerabilidade

Referência de apoio da skill `security-engineer`. Para cada classe: onde ela mora, o que
procurar e o teste que confirma. Revisão sem teste de confirmação produz achado teórico.

## Autorização quebrada por objeto (IDOR/BOLA)

- **Onde**: todo endpoint que recebe identificador (`/pedidos/{id}`, `?paciente_id=`), toda
  query que filtra só pelo id do recurso, todo download por caminho previsível.
- **Procurar**: consulta ao banco sem cláusula do dono (`where id = :id` sem `and owner_id`),
  verificação feita só no handler de listagem e não no de detalhe, papel lido de campo
  enviado pelo cliente, verificação em middleware que não cobre rotas novas.
- **Confirmar**: autentique como B, chame o recurso de A, espere 403/404. Faça também para
  PUT, PATCH, DELETE e para endpoints de exportação — costumam ser esquecidos.
- **Corrigir**: autorização centralizada por (sujeito, ação, objeto), aplicada na camada de
  dados. Identificador imprevisível (UUID) ajuda, mas não substitui a verificação.

## Injeção em interpretador

- **SQL/NoSQL**: procure concatenação e f-string em query, `raw`/`execute` do ORM, `ORDER BY`
  ou nome de tabela vindo do usuário (parâmetro não cobre identificador — use allowlist).
- **Comando**: `os.system`, `subprocess` com `shell=True`, string montada. Use lista de
  argumentos e caminho absoluto do binário; nunca passe entrada como opção.
- **Template**: renderizar string controlada pelo usuário como template é execução remota
  (SSTI). Template vem do código, dado vem da variável.
- **LDAP, XPath, regex** (ReDoS), **CSV** (fórmula executada na planilha), **cabeçalho HTTP**
  (CRLF) — mesmas regras.
- **Confirmar**: payload que altera a estrutura, não só o valor; observe erro, tempo e
  diferença de resultado.

## Desserialização insegura

- **Onde**: `pickle`, `yaml.load` sem `SafeLoader`, `ObjectInputStream`, `Marshal`,
  desserializador de mensagem em fila, cookie de sessão serializado.
- **Regra**: dado que veio de fora nunca vira objeto por desserialização de formato que
  suporta código. Use JSON com esquema, ou formato explícito (protobuf) com validação.
- **Em ML**: ver `ai-ml-security.md` — checkpoint é o caso mais comum e mais ignorado.

## SSRF

- **Onde**: "importar de URL", webhook configurável, geração de miniatura, proxy, renderização
  de HTML/PDF, verificação de link, e qualquer cliente HTTP que recebe destino do usuário.
- **Procurar**: validação feita antes do redirecionamento (o redirect 302 escapa da checagem),
  allowlist por substring (`contains("empresa.com")`), resolução de DNS separada da conexão
  (rebinding).
- **Corrigir**: allowlist de domínio e de esquema, resolver o nome e **validar o IP** contra
  faixas privadas, bloquear redirect ou revalidar a cada salto, proxy de saída dedicado,
  metadata service da nuvem exigindo token.
- **Confirmar**: aponte para um servidor seu e observe a requisição; em nuvem, teste o
  endereço do metadata service.

## Upload e caminho de arquivo

- Nome do arquivo nunca vira caminho: gere o nome, guarde o original só como metadado.
- Normalize e verifique que o caminho final está sob o diretório permitido — `..`, caminho
  absoluto, symlink, separador do Windows, codificação dupla.
- Tipo verificado por conteúdo, não por extensão nem por `Content-Type`. Reprocessar imagem
  (decodificar e reescrever) remove payload embutido.
- Sirva de domínio separado ou com `Content-Disposition: attachment` e
  `X-Content-Type-Options: nosniff`. Arquivo do usuário no mesmo domínio vira XSS.
- Descompactação: limite de tamanho descomprimido, de número de entradas e de profundidade;
  rejeite entrada com caminho absoluto ou `..` (zip slip).

## Autenticação, sessão e token

- Senha: Argon2id (ou bcrypt/scrypt) com parâmetros atuais, comparação em tempo constante,
  sem limite de tamanho baixo, sem regra de complexidade que empurra para senha pior.
- Sessão: id gerado por fonte criptográfica, rotacionado no login, invalidado no logout e na
  troca de senha, expiração absoluta além da inativa. Cookie `httpOnly`, `Secure`,
  `SameSite=Lax` ou `Strict`.
- JWT: valide assinatura com algoritmo fixado no servidor (rejeite `alg` vindo do token e
  `none`), `aud`, `iss`, `exp`, `nbf`; revogação exige lista ou token curto com refresh.
  Não guarde dado sensível no payload — ele é legível.
- Recuperação de senha e código de verificação: token de uso único, expiração curta, limite
  de tentativa, e resposta idêntica para conta existente e inexistente.
- MFA: verifique no servidor que o passo foi cumprido antes de emitir sessão completa —
  pular etapa por chamada direta ao endpoint seguinte é falha comum.
- Enumeração de usuário: mensagem e tempo de resposta iguais nos dois casos.

## XSS e front-end

- Codifique por contexto: HTML, atributo, JavaScript, URL, CSS. O escape de HTML não protege
  dentro de `<script>` nem em `href`.
- Procure `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `document.write`, `eval`,
  `setTimeout` com string, e sanitização caseira por regex.
- URL vinda do usuário: valide o esquema (`javascript:`, `data:` fora).
- CSP com `nonce` ou hash, sem `unsafe-inline`; `frame-ancestors` contra clickjacking.
- CORS: nunca reflita `Origin` com `Allow-Credentials: true`; allowlist explícita, e cuidado
  com comparação por prefixo.
- CSRF: token por sessão em formulário, ou `SameSite` mais verificação de origem para API de
  cookie. API com token no cabeçalho não precisa, desde que não aceite cookie.

## Criptografia e segredo

- Nada de ECB, nada de modo sem autenticação, nada de IV fixo ou reutilizado, nada de
  `Math.random`/`rand()` para valor de segurança.
- Chave por finalidade, guardada em cofre/KMS, com rotação prevista e procedimento testado.
- Segredo em erro, log, resposta de debug, mensagem de exceção, stack trace e URL (que vai
  para log de proxy e para `Referer`).
- Comparação de segredo em tempo constante.
- TLS obrigatório, verificação de certificado ligada (procure `verify=False`,
  `rejectUnauthorized: false`, `InsecureSkipVerify`).

## Lógica de negócio

Scanner não vê; é onde está o dinheiro.

- Condição de corrida em saldo, cupom, estoque, limite de uso — teste com requisições
  concorrentes.
- Fluxo de várias etapas: chamar a etapa final direto, repetir a etapa de pagamento, voltar
  atrás depois de aprovado.
- Valor, preço, desconto, quantidade negativa, arredondamento e unidade vindos do cliente.
- Limite de taxa por identidade **e** por recurso caro; contorno trivial por troca de IP,
  de conta ou por endpoint alternativo.
- Estado que só existe no cliente (papel, plano, tenant) e é aceito pelo servidor.

## Erro, log e exposição

- Mensagem genérica para o usuário, detalhe no log. Stack trace em produção entrega
  arquitetura e versão.
- Endpoint de debug, métricas, `/actuator`, painel de admin, documentação de API e
  `.git`/`.env` publicados são achado recorrente — procure explicitamente.
- Log estruturado com identificador de correlação, sem senha, token, número de documento,
  prontuário ou corpo completo de requisição.

## Ordem prática numa revisão de PR

1. O diff cria ou muda **fronteira** (rota, permissão, consumo de mensagem, ferramenta de
   agente, chamada externa)? Se não, o risco costuma ser baixo.
2. Entrada nova: quem controla, o que valida, para onde vai (interpretador? arquivo? rede?).
3. Consulta nova: filtra pelo dono?
4. Segredo, log e mensagem de erro no caminho tocado.
5. Teste que confirma o controle — de preferência um caso negativo automatizado, não uma
   verificação manual.
