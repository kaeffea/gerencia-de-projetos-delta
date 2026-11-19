# Gerência de Projetos · Equipe Delta

Material da disciplina de Gerência de Projetos (Prof. Rafael de Amorim Silva).

- **Tema 3:** Sistemas Inteligentes para Agropecuária
- **Subtema:** Manejo rotacionado de animais
- **Projeto da disciplina:** Manejo Inteligente de Bois (Maneja)

**Equipe:** Jackson Bruno (líder), José Felix, Júlia Pereira, Leonardo Lima, Leandro Cavalcante, Kauê Fortaleza, João Pedro e Maria Antônia.

## Estrutura

```
disciplina/                      ementa, equipe, livro-texto (aulas/) e fotos/prints de quadros
modulo-1/ … modulo-5/            uma pasta por atividade
  enunciado.txt                  o que a atividade pede
  original/                      o que tinha sido entregue antes (quando houve correção)
  entrega/                       o que vai para o Classroom: PDF do pitch, código e diagramas
gestao-areas-de-conhecimento/    pitch das 5 áreas de conhecimento (qualidade, RH, comunicações,
                                 riscos, aquisições), passado em aula em 13/10
```

## Situação das atividades (AB1)

| Atividade | Conteúdo | Situação |
|---|---|---|
| 1 | Conceitos e metodologias de gestão de projetos, pitch | Feita em sala e considerada (2,0) |
| 2 | DCU, Diagrama de Atividades, EAP, Matriz RACI | Entregue (2,0) · `modulo-2/entrega/Módulo2.pdf` |
| 3 | DS, DE, Gantt, rede, 3 pontos, quadro de custos | Reenviar `modulo-3/entrega/Módulo3.pdf` (DS e DE agora dentro do PDF) |
| 4 | DS, DE e snippet code | Enviar `modulo-4/entrega/` |
| 5 | Diagrama de Componentes, Diagrama de Implantação e snippet code | Enviar `modulo-5/entrega/` |

O pitch de `gestao-areas-de-conhecimento/` cobre a ementa dos módulos 4 e 5. As entregas 4 e 5 o usam na parte "relacionar o conteúdo da ementa":

- **Atividade 4:** qualidade, RH e comunicações.
- **Atividade 5:** riscos, aquisições e software de gestão.

Cada pasta `entrega/` tem um `ROTEIRO.md` com a lista de anexos e uma fala curta por slide.

## Rodar os snippets

Precisa só de Python 3.10 ou mais novo, sem dependências:

```bash
python modulo-4/entrega/main.py
python modulo-5/entrega/main.py
```

## Projeto (AB2)

Pela agenda da AB2 (`disciplina/quadros/agenda-ab2.png`):

- **Método:** especificação com IA generativa (SDD com Claude Code: `CLAUDE.md` mais um `.md` por diagrama UML) e cenários BDD.
- **Marcos:** core 50%, support 25%, generic 25%.
- **Apresentação final:** 26/11.

O código do projeto fica no repositório próprio do Maneja, fora deste.

## O que não está neste repositório

- `maneja/` e `seugado/`: são repositórios próprios, clonados aqui só para consulta.
- `gestao-areas-de-conhecimento/apresentacao-video.mp4`: 101 MB, acima do limite de 100 MB do GitHub. Fica só local.
